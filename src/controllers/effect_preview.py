from collections.abc import Callable

import numpy as np
import wx

from src.controllers.confirmation import Confirmation, ConfirmOption
from src.models.app_log import operation as log_operation
from src.models.audio_edit import EditError
from src.models.errors import APPLY_EFFECT, user_message
from src.view.confirm_screen import ConfirmScreen
from src.view.preview_screen import PreviewScreen

APPLY_LABEL = "Aplicar efeito"
DISCARD_LABEL = "Não aplicar"
LISTEN_LABEL = "Ouvir novamente"
DISCARDED_MESSAGE = "Efeito não aplicado."


def question(label: str) -> str:
    return f"Deseja aplicar o efeito {label}?"


def applied_message(label: str) -> str:
    return f"Efeito {label} aplicado."


def effect_options(label: str, on_apply: Callable[[], None], on_discard: Callable[[], None],
                   on_listen: Callable[[], None]) -> Confirmation:
    return Confirmation(
        title=f"Efeito {label}",
        question=question(label),
        options=(
            ConfirmOption(APPLY_LABEL, on_apply),
            ConfirmOption(DISCARD_LABEL, on_discard),
            ConfirmOption(LISTEN_LABEL, on_listen),
        ),
        on_cancel=None,
        initial_index=0,
        escape_cancels=False,
    )


def open_preview(manager, player, label: str, candidate: np.ndarray, start: int, end: int,
                 on_finish: Callable[[], None] | None = None, levels: np.ndarray | None = None,
                 family: str | None = None, effect_id: str | None = None, replacing: bool = False) -> bool:
    with log_operation(APPLY_EFFECT):
        try:
            player.start_preview(candidate, start, end)
        except EditError as error:
            manager.announcer.error(user_message(error), APPLY_EFFECT, error)
            return False

    def finish(message: str | None = None) -> None:
        def back() -> None:
            manager.pop_through(screen)
            if message:
                manager.speaker.speak(message)
            if on_finish is not None:
                on_finish()
        wx.CallAfter(back)

    def apply() -> None:
        player.stop_preview()
        with log_operation(APPLY_EFFECT):
            try:
                player.apply_effect(candidate, levels, family, effect_id, replacing)
            except EditError as error:
                manager.announcer.error(user_message(error), APPLY_EFFECT, error)
                finish()
                return
        manager.announcer.done(applied_message(label))
        finish()

    def discard() -> None:
        player.stop_preview()
        finish(DISCARDED_MESSAGE)

    def listen() -> None:
        wx.CallAfter(manager.pop)

    options = effect_options(label, apply, discard, listen)

    def show_options() -> None:
        manager.push(ConfirmScreen(manager.parent, manager, options))

    screen = PreviewScreen(manager.parent, manager, player, label, show_options)
    manager.push(screen)
    return True
