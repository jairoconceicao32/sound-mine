import logging
from collections.abc import Callable

from src.controllers.confirmation import Confirmation, ConfirmOption

logger = logging.getLogger(__name__)

TITLE = "Sair do editor"
QUESTION = "Sair do editor. Há alterações não salvas. O que deseja fazer?"
SAVE_AND_LEAVE = "Salvar e sair"
LEAVE_WITHOUT_SAVING = "Sair sem salvar"
CANCEL = "Cancelar"
CANCELED_MESSAGE = "Operação cancelada."
NOT_SAVED_MESSAGE = "O arquivo não foi salvo. O editor continua aberto."


class EditorExit:
    def __init__(self, has_changes: Callable[[], bool], save: Callable[[], bool],
                 show: Callable[[Confirmation], object], back: Callable[[str], None],
                 schedule: Callable[[Callable[[], None]], None]) -> None:
        self._has_changes = has_changes
        self._save = save
        self._show = show
        self._back = back
        self._schedule = schedule
        self._leave: Callable[[], None] | None = None
        self._screen = None

    @property
    def asking(self) -> bool:
        return self._leave is not None

    def request(self, leave: Callable[[], None]) -> bool:
        if self.asking:
            self._leave = leave
            announce = getattr(self._screen, "announce", None)
            if callable(announce):
                announce()
            return True
        if not self._has_changes():
            return False
        self._leave = leave
        self._screen = self._show(self.confirmation())
        return True

    def confirmation(self) -> Confirmation:
        return Confirmation(
            title=TITLE,
            question=QUESTION,
            options=(
                ConfirmOption(SAVE_AND_LEAVE, self._save_and_leave),
                ConfirmOption(LEAVE_WITHOUT_SAVING, self._leave_without_saving),
                ConfirmOption(CANCEL, self._cancel),
            ),
            on_cancel=self._cancel,
        )

    def _save_and_leave(self) -> None:
        try:
            saved = self._save()
        except Exception:
            logger.exception("Falha inesperada ao salvar antes de sair do editor.")
            saved = False
        if saved:
            self._finish()
        else:
            self._stay(NOT_SAVED_MESSAGE)

    def _leave_without_saving(self) -> None:
        self._finish()

    def _cancel(self) -> None:
        self._stay(CANCELED_MESSAGE)

    def _finish(self) -> None:
        leave = self._leave
        self._reset()
        if leave is not None:
            self._schedule(leave)

    def _stay(self, message: str) -> None:
        self._reset()
        self._back(message)

    def _reset(self) -> None:
        self._leave = None
        self._screen = None
