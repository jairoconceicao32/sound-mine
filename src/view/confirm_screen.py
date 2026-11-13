import logging

import wx

from src.controllers.confirmation import Confirmation
from src.view.keys import Command, KeyCommand
from src.view.menu_view import MenuView
from src.view.screen import Screen

logger = logging.getLogger(__name__)

CANCEL_LABEL = "Cancelar"


class ConfirmScreen(Screen):
    def __init__(self, parent: wx.Window, manager, confirmation: Confirmation) -> None:
        super().__init__(parent, manager)
        self._confirmation = confirmation
        self._index = confirmation.initial_index
        self._answered = False
        self._view = MenuView(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._view, 1, wx.EXPAND)
        self.SetSizer(sizer)

    @property
    def title(self) -> str:
        return self._confirmation.title

    @property
    def selected(self) -> str:
        return self._option()

    def on_activate(self) -> None:
        self.announce()

    def announce(self) -> None:
        self._view.show_message(self._confirmation.question)
        self._show_option()
        self.manager.speaker.speak(self._confirmation.question)
        self.manager.speaker.speak(self._option(), interrupt=False)

    def handle_command(self, command: KeyCommand) -> bool:
        match command.command:
            case Command.UP:
                self._move(-1)
            case Command.DOWN:
                self._move(1)
            case Command.ACTIVATE:
                self._answer(self._confirmation.action(self._index), self._option())
            case Command.BACK:
                self._answer(self._confirmation.on_cancel, CANCEL_LABEL)
            case Command.LETTER:
                self._select_by_key(command.char)
            case Command.BLOCKED:
                pass
            case _:
                return False
        return True

    def help_lines(self) -> list[str]:
        return [
            self._confirmation.question,
            "",
            "Opções disponíveis:",
            *self._confirmation.labels,
            "",
            "Setas para cima e para baixo: navegam entre as opções.",
            "Letra: seleciona a opção que começa com essa letra, sem confirmar. "
            "Repetir a letra passa para a próxima opção com a mesma inicial.",
            "Enter: confirma a opção selecionada.",
            "Esc: cancela e volta à tela anterior.",
            "F1: exibe esta ajuda.",
        ]

    def _option(self) -> str:
        return self._confirmation.labels[self._index]

    def _show_option(self) -> None:
        self._view.show_item(self._option(), self._index, len(self._confirmation.options))

    def _move(self, step: int) -> None:
        index = self._index + step
        if not 0 <= index < len(self._confirmation.options):
            self.manager.sounds.play("border")
            return
        self._select(index)

    def _select_by_key(self, key: str | None) -> None:
        index = self._confirmation.index_for_key(key, self._index)
        if index is not None:
            self._select(index)

    def _select(self, index: int) -> None:
        if index != self._index:
            self._index = index
            self.manager.sounds.play("navigation")
        self._show_option()
        self.manager.speaker.speak(self._option())

    def _answer(self, action, label: str) -> None:
        if self._answered:
            return
        self._answered = True
        self.manager.sounds.play("confirme")
        try:
            action()
        except Exception:
            self._answered = False
            logger.exception("Erro ao executar a opção %r da confirmação %r", label, self.title)
            self.manager.announcer.error(f"Não foi possível executar a opção {label}.")
        self.manager.focus_window()
