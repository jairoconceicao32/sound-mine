from collections.abc import Callable

import wx

from src.view.keys import Command, KeyCommand
from src.view.screen import Screen

MAX_STARTUP_DELAY_MS = 3000


class StartupScreen(Screen):
    def __init__(self, parent: wx.Window, manager, on_done: Callable[[], None]) -> None:
        super().__init__(parent, manager)
        self._on_done = on_done
        self._timer: wx.CallLater | None = None
        self._finished = False

    @property
    def title(self) -> str:
        return self.manager.version

    def on_activate(self) -> None:
        delay = min(self.manager.sounds.duration_ms("startup"), MAX_STARTUP_DELAY_MS)
        if delay <= 0:
            wx.CallAfter(self._finish)
            return
        self.manager.sounds.play("startup")
        self._timer = wx.CallLater(delay, self._finish)

    def on_deactivate(self) -> None:
        self._stop_timer()

    def handle_command(self, command: KeyCommand) -> bool:
        if command.command is Command.ACTIVATE:
            self.manager.sounds.stop()
            wx.CallAfter(self._finish)
        return True

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        self._stop_timer()
        self._on_done()

    def _stop_timer(self) -> None:
        if self._timer is not None:
            self._timer.Stop()
            self._timer = None
