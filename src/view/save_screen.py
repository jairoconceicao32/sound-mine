import logging

import wx

from src.models.save_feedback import SaveFeedback, progress_text
from src.view.keys import Command, KeyCommand
from src.view.screen import Screen

logger = logging.getLogger(__name__)

REFRESH_MS = 250
SAVE_TITLE = "Salvando o arquivo"
SAVING_TEXT = "Salvando o arquivo."
CANCELING_TEXT = "Cancelando o salvamento."
CLOSE_REFUSED_TEXT = "Salvamento em andamento. Aguarde o término ou pressione Esc para cancelar."
SAVE_KEYS_TEXT = "Espaço: progresso   Esc: cancelar o salvamento   F1: ajuda"


class SaveScreen(Screen):
    def __init__(self, parent: wx.Window, manager, task, file_name: str) -> None:
        super().__init__(parent, manager)
        self._task = task
        self._file_name = file_name
        self._opened = False
        self._feedback = SaveFeedback(
            beep=lambda factor: manager.sounds.play_pitched("navigation", factor),
            announce=lambda text: manager.speaker.speak(text, interrupt=False),
            confirm=lambda: manager.sounds.play("confirme", always=True),
        )
        self._status = wx.StaticText(self, label=f"{SAVE_TITLE}: {file_name}")
        self._keys = wx.StaticText(self, label=SAVE_KEYS_TEXT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._status, 0, wx.ALL, 10)
        sizer.Add(self._keys, 0, wx.ALL, 10)
        self.SetSizer(sizer)
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)

    @property
    def title(self) -> str:
        return SAVE_TITLE

    def on_activate(self) -> None:
        if not self._opened:
            self._opened = True
            self.manager.speaker.speak(SAVING_TEXT)
        self._timer.Start(REFRESH_MS)

    def on_deactivate(self) -> None:
        if self.manager.current is not self:
            self._timer.Stop()

    def status_text(self) -> str:
        if self._task.canceling:
            return CANCELING_TEXT
        if self._task.shows_progress:
            return progress_text(self._task.progress)
        return SAVING_TEXT

    def finish(self, saved: bool) -> None:
        self._timer.Stop()
        self._safely(self._feedback.finish, saved)

    def refuses_close(self) -> bool:
        if not self._task.running:
            return False
        self.manager.speaker.speak(CLOSE_REFUSED_TEXT)
        return True

    def handle_command(self, command: KeyCommand) -> bool:
        match command.command:
            case Command.HELP:
                return False
            case Command.SPACE:
                self.manager.speaker.speak(self.status_text())
            case Command.BACK:
                if self._task.running and not self._task.canceling:
                    self._task.cancel()
                    self.manager.speaker.speak(CANCELING_TEXT)
        self._sync()
        return True

    def help_lines(self) -> list[str]:
        return [
            f"{SAVE_TITLE}:",
            "Espaço: informa o andamento do salvamento.",
            "Esc: cancela o salvamento. O arquivo de destino não é alterado.",
            "F1: exibe esta ajuda.",
            "",
            "O andamento em porcentagem é informado apenas quando o salvamento é demorado.",
            "O Sound Mine não pode ser fechado enquanto o arquivo está sendo salvo.",
        ]

    def _on_timer(self, event: wx.TimerEvent) -> None:
        task = self._task
        if not task.canceling:
            self._safely(self._feedback.update, task.shows_progress, task.elapsed, task.progress)
        self._sync()

    @staticmethod
    def _safely(action, *args) -> None:
        try:
            action(*args)
        except Exception:
            logger.exception("Falha no retorno sonoro do salvamento.")

    def _sync(self) -> None:
        text = f"{self.status_text()} {self._file_name}"
        if self._status.GetLabel() != text:
            self._status.SetLabel(text)
            self.Layout()

    def _on_destroy(self, event: wx.WindowDestroyEvent) -> None:
        if event.GetEventObject() is self:
            self._timer.Stop()
            self._feedback.finish(False)
            self._task.cancel()
        event.Skip()
