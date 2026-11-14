import logging

import wx

from src.controllers.menu_model import LetterMode, Menu, MenuItem
from src.controllers.menu_navigator import MenuNavigator
from src.models.errors import RUN_OPTION
from src.view.keys import Command, KeyCommand
from src.view.menu_view import MenuView
from src.view.screen import Screen

logger = logging.getLogger(__name__)

MESSAGE_TIME_MS = 3000


class MenuScreen(Screen):
    def __init__(self, parent: wx.Window, manager, menu: Menu) -> None:
        super().__init__(parent, manager)
        self._navigator = MenuNavigator(menu)
        self._view = MenuView(self)
        self._message_timer: wx.CallLater | None = None

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._view, 1, wx.EXPAND)
        self.SetSizer(sizer)

    @property
    def title(self) -> str:
        return self._navigator.menu.title

    def on_activate(self) -> None:
        self._refresh()
        self._stop_message()
        menu = self._navigator.menu
        message = menu.title if self.manager.settings.disable_tips else menu.opening_message
        self._view.show_message(message)
        self.manager.speaker.speak(message)
        self._message_timer = wx.CallLater(MESSAGE_TIME_MS, self._end_message)

    def on_deactivate(self) -> None:
        self._stop_message()

    def handle_command(self, command: KeyCommand) -> bool:
        match command.command:
            case Command.UP:
                if self._navigator.move_up():
                    self._on_moved()
                else:
                    self.manager.sounds.play("border")
                return True
            case Command.DOWN:
                if self._navigator.move_down():
                    self._on_moved()
                else:
                    self.manager.sounds.play("border")
                return True
            case Command.ACTIVATE:
                self._stop_message()
                self._activate(self._navigator.current())
                return True
            case Command.LETTER:
                previous = self._navigator.current()
                item = self._navigator.select_by_key(command.char)
                if item is not None:
                    self._stop_message()
                    if item is not previous:
                        self.manager.sounds.play("navigation")
                    self._show_current()
                    if self._navigator.menu.letter_mode is LetterMode.ACTIVATE:
                        self._activate(item)
                return True
            case Command.BLOCKED:
                return True
        return False

    def help_lines(self) -> list[str]:
        if not self._navigator.menu.has_help:
            return []
        if self._navigator.menu.letter_mode is LetterMode.ACTIVATE:
            letter_help = "Letra: executa a opção correspondente."
        else:
            letter_help = "Letra: seleciona a opção correspondente."
        return [
            "Opções disponíveis:",
            *(self._navigator.menu.item_text(item) for item in self._navigator.items),
            "",
            "Setas para cima e para baixo: navegam entre as opções.",
            letter_help,
            "Enter: executa a opção selecionada.",
            "Esc: volta à tela anterior; no menu principal, fecha o programa.",
            "F1: exibe esta ajuda.",
        ]

    def _refresh(self) -> None:
        self._navigator.refresh()
        self._update_item_label()

    def _update_item_label(self) -> None:
        item = self._navigator.current()
        text = self._navigator.menu.item_text(item) if item is not None else ""
        self._view.show_item(text, self._navigator.index, len(self._navigator.items))

    def _on_moved(self) -> None:
        self._stop_message()
        self.manager.sounds.play("navigation")
        self._show_current()

    def _show_current(self, interrupt: bool = True) -> None:
        self._update_item_label()
        item = self._navigator.current()
        if item is not None:
            self.manager.speaker.speak(self._navigator.menu.item_text(item), interrupt)

    def _end_message(self) -> None:
        self._message_timer = None
        self._view.show_message("")
        self._show_current(interrupt=False)

    def _stop_message(self) -> None:
        if self._message_timer is not None:
            self._message_timer.Stop()
            self._message_timer = None
            self._view.show_message("")

    def _activate(self, item: MenuItem | None) -> None:
        if item is None:
            return
        self.manager.sounds.play("confirme")
        try:
            item.action()
        except Exception:
            logger.exception("Erro ao executar a opção %r", item.label)
            self.manager.announcer.error(
                f"Não foi possível executar a opção {item.label}.", RUN_OPTION
            )
        self.manager.focus_window()
        if self.manager.current is self:
            self._refresh()
