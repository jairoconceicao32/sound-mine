from collections.abc import Callable

import wx

from src.controllers.menu_model import Menu, MenuItem
from src.view.keys import Command, KeyCommand
from src.view.menu_screen import MenuScreen
from src.view.player_screen import clock_time
from src.view.settings_screen import ANNOUNCE_DELAY_MS


class EditorScreen(MenuScreen):
    def __init__(self, parent: wx.Window, manager, menu: Menu, player,
                 on_back: Callable[[], bool] | None = None) -> None:
        super().__init__(parent, manager, menu)
        self._player = player
        self._on_back = on_back
        self._menu_open = False
        self._ask_timer: wx.CallLater | None = None
        self._status = wx.StaticText(self, label="")
        self.GetSizer().Insert(0, self._status, 0, wx.ALL, 10)

    def on_activate(self) -> None:
        self._stop_message()
        self._close_menu()
        self._update_status()
        self._ask()

    def on_deactivate(self) -> None:
        super().on_deactivate()
        self._cancel_ask()

    def handle_command(self, command: KeyCommand) -> bool:
        self._cancel_ask()
        match command.command:
            case Command.BACK:
                if self._on_back is not None and self._on_back():
                    return True
            case Command.UP | Command.DOWN:
                if not self._menu_open:
                    self._open_menu(command.command)
                    return True
            case Command.ACTIVATE:
                if not self._menu_open:
                    return True
            case Command.LETTER:
                item = self._navigator.select_by_key(command.char)
                if item is not None:
                    self._stop_message()
                    self._activate(item)
                return True
        return super().handle_command(command)

    def help_lines(self) -> list[str]:
        menu = self._navigator.menu
        return [
            "Opções disponíveis:",
            *(menu.item_text(item) for item in self._navigator.items),
            "",
            "Letra: executa a opção correspondente.",
            "Setas para cima e para baixo: mostram a lista de opções e navegam entre elas.",
            "Enter: executa a opção selecionada na lista.",
            "Esc: volta à tela anterior.",
            "F1: exibe esta ajuda.",
        ]

    def _open_menu(self, direction: Command) -> None:
        self._menu_open = True
        self._navigator.refresh()
        last = len(self._navigator.items) - 1
        self._navigator.select_index(0 if direction is Command.DOWN else last)
        self._view.show_message("")
        self._on_moved()

    def _close_menu(self) -> None:
        self._menu_open = False
        self._refresh()
        self._view.show_message(self._navigator.menu.opening_message)

    def _update_item_label(self) -> None:
        if self._menu_open:
            super()._update_item_label()
        else:
            self._view.show_item("", None, 0)

    def _activate(self, item: MenuItem | None) -> None:
        self._menu_open = False
        super()._activate(item)
        if self.manager.current is self:
            self._close_menu()
            self._update_status()
            self._ask()

    def _ask(self) -> None:
        self._cancel_ask()
        self._ask_timer = wx.CallLater(ANNOUNCE_DELAY_MS, self._speak_question)

    def _cancel_ask(self) -> None:
        if self._ask_timer is not None:
            self._ask_timer.Stop()
            self._ask_timer = None

    def _speak_question(self) -> None:
        self._ask_timer = None
        if self.manager.current is self and not self._menu_open:
            self.manager.speaker.speak(self._navigator.menu.opening_message, interrupt=False)

    def _update_status(self) -> None:
        player = self._player
        text = f"{player.file_name} - cursor em {clock_time(player.position())} de {clock_time(player.duration)}"
        if self._status.GetLabel() != text:
            self._status.SetLabel(text)
            self.Layout()
