import logging
from collections.abc import Callable

import wx

from src.models.settings import Settings
from src.view.announcer import Announcer
from src.view.interface_sounds import InterfaceSounds
from src.view.keys import Command, translate
from src.view.screen import FocusSink, NoFocusPanel, Screen
from src.view.speaker import Speaker

logger = logging.getLogger(__name__)

OUTPUT_CHECK_MS = 500
OUTPUT_ANNOUNCE_MS = 300

_IGNORED_COMMANDS = {
    Command.BLOCKED,
    Command.NEXT_FIELD,
    Command.PREV_FIELD,
    Command.NEXT_TAB,
    Command.PREV_TAB,
    Command.PAGE_UP,
    Command.PAGE_DOWN,
    Command.HOME,
    Command.END,
    Command.ERASE,
    Command.LEFT,
    Command.RIGHT,
    Command.SPACE,
}


class ScreenManager:
    def __init__(self, frame: wx.Frame, announcer: Announcer, speaker: Speaker,
                 sounds: InterfaceSounds, version: str, settings: Settings, outputs=None) -> None:
        self._frame = frame
        self.announcer = announcer
        self.speaker = speaker
        self.sounds = sounds
        self.version = version
        self.settings = settings
        self.outputs = outputs
        self.output_status = outputs.status_text() if outputs is not None else ""
        self._stack: list[Screen] = []
        self._close_guard: Callable[[Callable[[], None]], bool] | None = None
        self._closing = False
        self._key_panel = NoFocusPanel(frame, style=wx.WANTS_CHARS)
        self._container = NoFocusPanel(self._key_panel)
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._container.SetSizer(self._sizer)
        self._focus_sink = FocusSink(self._key_panel)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(self._focus_sink, 0)
        panel_sizer.Add(self._container, 1, wx.EXPAND)
        self._key_panel.SetSizer(panel_sizer)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self._key_panel, 1, wx.EXPAND)
        frame.SetSizer(outer)
        frame.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)
        frame.Bind(wx.EVT_ACTIVATE, self._on_activate_window)
        frame.Bind(wx.EVT_CLOSE, self._on_close)
        self._output_timer: wx.Timer | None = None
        if outputs is not None:
            outputs.set_listener(self._on_output_changed)
            self._output_timer = wx.Timer(frame)
            frame.Bind(wx.EVT_TIMER, self._on_output_timer, self._output_timer)
            self._output_timer.Start(OUTPUT_CHECK_MS)

    @property
    def parent(self) -> wx.Window:
        return self._container

    @property
    def current(self) -> Screen | None:
        return self._stack[-1] if self._stack else None

    def focus_window(self) -> None:
        wx.CallAfter(self._focus_now)

    def focus_now(self) -> None:
        self._focus_now()

    def push(self, screen: Screen) -> None:
        if self._stack:
            self._stack[-1].on_deactivate()
            self._stack[-1].Hide()
        self._stack.append(screen)
        self._sizer.Add(screen, 1, wx.EXPAND)
        self._show(screen)

    def replace(self, screen: Screen) -> None:
        if self._stack:
            old = self._stack.pop()
            old.on_deactivate()
            self._sizer.Detach(old)
            old.Destroy()
        self.push(screen)

    def pop(self) -> None:
        if len(self._stack) <= 1:
            self.close()
            return
        self._discard(self._stack.pop())
        self._show(self._stack[-1])

    def pop_through(self, screen: Screen) -> None:
        if screen not in self._stack:
            return
        if self._stack[0] is screen:
            self.close()
            return
        while True:
            top = self._stack.pop()
            self._discard(top)
            if top is screen:
                break
        self._show(self._stack[-1])

    def close(self) -> None:
        if self.current is not None:
            self.current.on_deactivate()
        wx.CallAfter(self._frame.Close)

    def close_now(self) -> None:
        self._closing = True
        self.close()

    def set_close_guard(self, guard: Callable[[Callable[[], None]], bool]) -> None:
        self._close_guard = guard

    def clear_close_guard(self, guard: Callable[[Callable[[], None]], bool]) -> None:
        if self._close_guard is guard:
            self._close_guard = None

    def show_help(self) -> None:
        screen = self.current
        if screen is None:
            return
        lines = screen.help_lines()
        if not lines:
            return
        screen.on_deactivate()
        self.announcer.dialog("\n".join(lines), f"Ajuda - {screen.title}")
        self.focus_window()

    def _discard(self, screen: Screen) -> None:
        screen.on_deactivate()
        self._sizer.Detach(screen)
        screen.Destroy()

    def _show(self, screen: Screen) -> None:
        screen.Show()
        self._container.Layout()
        self._key_panel.Layout()
        self.focus_window()
        screen.on_activate()

    def _focus_now(self) -> None:
        if not self._frame or self._frame.IsBeingDeleted():
            return
        target = self.current.focus_target() if self.current is not None else None
        (target or self._focus_sink).SetFocus()

    def _guard_vetoes(self, event: wx.CloseEvent) -> bool:
        if self._closing or self._close_guard is None or not event.CanVeto():
            return False
        try:
            return bool(self._close_guard(self.close_now))
        except Exception:
            logger.exception("Falha ao verificar o fechamento do programa.")
            return False

    def _on_output_timer(self, event: wx.TimerEvent) -> None:
        try:
            self.outputs.check()
        except Exception:
            logger.exception("Falha ao verificar a saída de áudio.")

    def _on_output_changed(self, message: str) -> None:
        self.output_status = message
        wx.CallLater(OUTPUT_ANNOUNCE_MS, self._announce_output, message)
        if self.current is not None:
            self.current.output_changed()

    def _announce_output(self, message: str) -> None:
        if self._closing or not self._frame or self._frame.IsBeingDeleted():
            return
        self.speaker.speak(message, interrupt=False)

    def _on_close(self, event: wx.CloseEvent) -> None:
        if self._guard_vetoes(event):
            event.Veto()
            return
        self._closing = True
        if self._output_timer is not None:
            self._output_timer.Stop()
        try:
            if self.current is not None:
                self.current.on_deactivate()
            self._frame.Hide()
            self.sounds.play_and_wait("close")
            self.sounds.close()
            if self.outputs is not None:
                self.outputs.close()
        except Exception:
            logger.exception("Falha ao encerrar o programa.")
        finally:
            event.Skip()

    def _on_activate_window(self, event: wx.ActivateEvent) -> None:
        if event.GetActive():
            self.focus_window()
        event.Skip()

    def _on_char_hook(self, event: wx.KeyEvent) -> None:
        command = translate(event)
        if command is None:
            event.Skip()
            return

        screen = self.current
        if screen is not None and screen.passes_key(command):
            event.Skip()
            return
        if screen is not None and screen.handle_command(command):
            return

        if command.command is Command.BACK:
            self.pop()
        elif command.command is Command.HELP:
            self.show_help()
        elif command.command in _IGNORED_COMMANDS:
            pass
        else:
            event.Skip()
