import logging

import wx

from src.controllers.settings import (
    DIGITS,
    ButtonField,
    NumberField,
    SettingsForm,
    TabField,
    ToggleField,
)
from src.view.keys import Command, KeyCommand
from src.view.menu_view import MenuView
from src.view.screen import Screen

logger = logging.getLogger(__name__)

ANNOUNCE_DELAY_MS = 150

_SLIDER_KEYS = {
    Command.LEFT,
    Command.RIGHT,
    Command.HOME,
    Command.END,
    Command.UP,
    Command.DOWN,
    Command.PAGE_UP,
    Command.PAGE_DOWN,
}

_EDIT_KEYS = _SLIDER_KEYS | {Command.ERASE}


def _run_action(manager, field: ButtonField) -> None:
    try:
        field.action()
    except Exception:
        logger.exception("Erro ao executar a opção %r", field.label)
        manager.announcer.error(f"Não foi possível executar a opção {field.label}.")
    manager.focus_window()


class SettingsScreen(Screen):
    def __init__(self, parent: wx.Window, manager, form: SettingsForm) -> None:
        super().__init__(parent, manager)
        self._form = form
        self._view = MenuView(self)
        self._controls: dict[str, tuple[wx.StaticText | None, wx.Window]] = {}

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._view, 1, wx.EXPAND)
        for tab in form.tabs:
            for field in tab.fields:
                if isinstance(field, (NumberField, ToggleField)):
                    label, control = self._create_control(field)
                    if label is not None:
                        sizer.Add(label, 0, wx.LEFT | wx.RIGHT, 10)
                    sizer.Add(control, 0, wx.EXPAND | wx.ALL, 10)
        for field in form.buttons:
            button = wx.Button(self, label=field.label)
            button.Bind(wx.EVT_BUTTON, lambda event: self._on_activate_field())
            button.Hide()
            self._controls[self._key_of(field)] = (None, button)
            sizer.Add(button, 0, wx.ALL, 10)
        self.SetSizer(sizer)

    @staticmethod
    def _key_of(field: NumberField | ToggleField | ButtonField) -> str:
        return f"button:{field.label}" if isinstance(field, ButtonField) else field.key

    def _create_control(self, field: NumberField | ToggleField
                        ) -> tuple[wx.StaticText | None, wx.Window]:
        value = self._form.values[field.key]
        if isinstance(field, ToggleField):
            control = wx.CheckBox(self, label=field.label)
            control.SetValue(value)
            control.Bind(wx.EVT_CHECKBOX,
                         lambda event, key=field.key: self._on_checkbox(event, key))
            control.Hide()
            self._controls[field.key] = (None, control)
            return None, control
        label = wx.StaticText(self, label=field.label)
        if field.slider:
            control = wx.Slider(self, value=value, minValue=field.minimum,
                                maxValue=field.maximum, style=wx.SL_HORIZONTAL)
            control.SetLineSize(field.step)
            control.SetPageSize(field.big_step)
            control.Bind(wx.EVT_SLIDER, lambda event, key=field.key: self._on_slider(event, key))
        else:
            control = wx.TextCtrl(self, value=str(value))
            control.SetMaxLength(len(str(field.maximum)))
            control.Bind(wx.EVT_CHAR, self._on_edit_char)
        label.Hide()
        control.Hide()
        self._controls[field.key] = (label, control)
        return label, control

    @property
    def title(self) -> str:
        return self._form.title

    def on_activate(self) -> None:
        self._update_view()
        if self._native_control() is not None:
            self._show_native()
            return
        self.manager.speaker.speak(f"{self._form.title}.")
        self.manager.speaker.speak(self._form.text_of(self._form.current()), interrupt=False)

    def focus_target(self) -> wx.Window | None:
        return self._native_control()

    def passes_key(self, command: KeyCommand) -> bool:
        control = self._native_control()
        if control is None:
            return False
        if isinstance(control, wx.Button):
            return False
        if isinstance(control, wx.CheckBox):
            return command.command is Command.SPACE
        if isinstance(control, wx.Slider):
            return command.command in _SLIDER_KEYS
        if command.command is Command.LETTER:
            return command.char is not None and command.char in DIGITS
        return command.command in _EDIT_KEYS

    def handle_command(self, command: KeyCommand) -> bool:
        if self._native_control() is not None:
            return self._handle_native_command(command)
        match command.command:
            case Command.NEXT_FIELD:
                self._on_field_moved(self._form.next_field())
            case Command.PREV_FIELD:
                self._on_field_moved(self._form.prev_field())
            case Command.NEXT_TAB:
                self._on_field_moved(self._form.next_tab())
            case Command.PREV_TAB:
                self._on_field_moved(self._form.prev_tab())
            case Command.UP:
                self._on_value_changed(self._form.change_value(-1))
            case Command.DOWN:
                self._on_value_changed(self._form.change_value(1))
            case Command.ACTIVATE:
                self._on_activate_field()
            case Command.LETTER | Command.ERASE | Command.BLOCKED | Command.LEFT | Command.RIGHT \
                    | Command.HOME | Command.END | Command.PAGE_UP | Command.PAGE_DOWN:
                pass
            case _:
                return False
        return True

    def _handle_native_command(self, command: KeyCommand) -> bool:
        match command.command:
            case Command.NEXT_FIELD:
                if self._commit_edit():
                    self._on_field_moved(self._form.next_field())
            case Command.PREV_FIELD:
                if self._commit_edit():
                    self._on_field_moved(self._form.prev_field())
            case Command.NEXT_TAB:
                if self._commit_edit():
                    self._on_field_moved(self._form.next_tab())
            case Command.PREV_TAB:
                if self._commit_edit():
                    self._on_field_moved(self._form.prev_tab())
            case Command.ACTIVATE:
                if isinstance(self._form.current(), ButtonField):
                    self._on_activate_field()
                elif self._editable_field() is not None and self._commit_edit():
                    self.manager.sounds.play("confirme")
                    self.manager.speaker.speak(self._form.value_of(self._form.current()))
            case Command.BACK:
                return self._restore_edit()
            case Command.HELP:
                return False
        return True

    def _number_field(self) -> NumberField | None:
        field = self._form.current()
        return field if isinstance(field, NumberField) else None

    def _editable_field(self) -> NumberField | None:
        field = self._number_field()
        return field if field is not None and not field.slider else None

    def _native_control(self) -> wx.Window | None:
        field = self._form.current()
        if isinstance(field, (NumberField, ToggleField, ButtonField)):
            return self._controls[self._key_of(field)][1]
        return None

    def _current_text(self, field: NumberField) -> str:
        return str(self._form.values[field.key])

    def _commit_edit(self) -> bool:
        field = self._editable_field()
        if field is None:
            return True
        if self._form.set_text(self._native_control().GetValue()):
            self._update_view()
            return True
        self.manager.speaker.speak(
            f"Valor inválido. Digite um número de {field.minimum} a {field.maximum}."
        )
        return False

    def _restore_edit(self) -> bool:
        field = self._editable_field()
        if field is None:
            return False
        control = self._native_control()
        if control.GetValue() == self._current_text(field):
            return False
        control.ChangeValue(self._current_text(field))
        control.SelectAll()
        self.manager.speaker.speak(f"Edição cancelada. {self._form.value_of(field)}")
        return True

    def _on_edit_char(self, event: wx.KeyEvent) -> None:
        code = event.GetUnicodeKey()
        if code == wx.WXK_NONE or code < 32 or chr(code) in DIGITS:
            event.Skip()

    def _on_checkbox(self, event: wx.CommandEvent, key: str) -> None:
        field = self._form.current()
        if isinstance(field, ToggleField) and field.key == key:
            self._form.set_toggle(event.GetEventObject().GetValue())
            self._update_view()
        event.Skip()

    def _on_slider(self, event: wx.CommandEvent, key: str) -> None:
        field = self._number_field()
        if field is not None and field.key == key:
            self._form.set_text(str(event.GetEventObject().GetValue()))
            self._update_view()
        event.Skip()

    def _show_native(self) -> bool:
        target = self._native_control()
        previous = [pair for pair in self._controls.values() if pair[1].IsShown()]
        had_native = bool(previous)
        if target is not None:
            field = self._form.current()
            label = self._controls[self._key_of(field)][0]
            if isinstance(target, (wx.Slider, wx.CheckBox)):
                target.SetValue(self._form.values[field.key])
            elif isinstance(target, wx.TextCtrl):
                target.ChangeValue(self._current_text(field))
            if label is not None:
                label.Show()
            target.Show()
            self.Layout()
        if target is not None or had_native:
            self.manager.focus_now()
        for label, control in previous:
            if control is not target:
                if label is not None:
                    label.Hide()
                control.Hide()
        self.Layout()
        if isinstance(target, wx.TextCtrl):
            target.SelectAll()
        return had_native

    def _speak_current(self) -> None:
        if self.manager.current is self and self._native_control() is None:
            self.manager.speaker.speak(self._form.text_of(self._form.current()))

    def _on_field_moved(self, moved: bool) -> None:
        if not moved:
            return
        self.manager.sounds.play("navigation")
        self._update_view()
        after_native = self._show_native()
        if self._native_control() is not None:
            return
        if after_native:
            wx.CallLater(ANNOUNCE_DELAY_MS, self._speak_current)
        else:
            self._speak_current()

    def _on_value_changed(self, changed: bool) -> None:
        if not changed:
            return
        field = self._form.current()
        self.manager.sounds.play("navigation")
        self._update_view()
        if isinstance(field, TabField):
            self.manager.speaker.speak(self._form.text_of(field))
        else:
            self.manager.speaker.speak(self._form.value_of(field))

    def _on_activate_field(self) -> None:
        field = self._form.current()
        if isinstance(field, ButtonField):
            self.manager.sounds.play("confirme")
            wx.CallAfter(_run_action, self.manager, field)

    def _update_view(self) -> None:
        form = self._form
        if form.show_tab_selector:
            self._view.show_message(
                f"Guia {form.tab.name}  ({form.tab_index + 1} de {form.tab_count})"
            )
        else:
            self._view.show_message(form.title)
        self._view.show_item(form.text_of(form.current()), form.field_index, len(form.fields))
