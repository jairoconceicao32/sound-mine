from collections.abc import Callable

import wx

from src.view.keys import Command, KeyCommand
from src.view.playback import SEEK_SECONDS, PlaybackControl
from src.view.player_screen import clock_time
from src.view.screen import Screen

REFRESH_MS = 100
PREVIEW_END_TEXT = "Fim da prévia"
PREVIEW_KEYS_TEXT = (
    "Espaço: tocar ou pausar   Setas para os lados: 5 segundos   "
    "Home: início   End: fim   Esc: opções do efeito"
)


def opening_text(label: str) -> str:
    return f"Prévia do efeito {label}"


class PreviewScreen(Screen):
    def __init__(self, parent: wx.Window, manager, player, label: str,
                 on_options: Callable[[], None]) -> None:
        super().__init__(parent, manager)
        self._player = player
        self._label = label
        self._on_options = on_options
        self._control = PlaybackControl(manager, player, end_text=PREVIEW_END_TEXT)
        self._opened = False
        self._was_playing = False
        self._status = wx.StaticText(self, label="")
        self._output = wx.StaticText(self, label="")
        self._keys = wx.StaticText(self, label=PREVIEW_KEYS_TEXT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._status, 0, wx.ALL, 10)
        sizer.Add(self._output, 0, wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self._keys, 0, wx.ALL, 10)
        self.SetSizer(sizer)
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)

    @property
    def title(self) -> str:
        return opening_text(self._label)

    def on_activate(self) -> None:
        if not self._opened:
            self._opened = True
            self.manager.speaker.speak(opening_text(self._label))
        self._player.seek(0)
        self._control.play()
        self._sync()
        self._timer.Start(REFRESH_MS)

    def on_deactivate(self) -> None:
        if self.manager.current is not self:
            self._timer.Stop()

    def output_changed(self) -> None:
        self._sync()

    def handle_command(self, command: KeyCommand) -> bool:
        match command.command:
            case Command.HELP:
                return False
            case Command.BACK:
                self._timer.Stop()
                self._player.pause()
                self._on_options()
                return True
            case Command.ACTIVATE:
                return True
            case _:
                self._control.handle(command)
        self._sync()
        return True

    def help_lines(self) -> list[str]:
        return [
            f"{opening_text(self._label)}:",
            "Espaço: toca ou pausa a prévia.",
            f"Seta para a esquerda: volta {SEEK_SECONDS} segundos.",
            f"Seta para a direita: avança {SEEK_SECONDS} segundos.",
            "Home: vai para o início da prévia.",
            "End: vai para o fim da prévia.",
            "Esc: interrompe a prévia e apresenta as opções do efeito: Aplicar efeito, Não aplicar e Ouvir novamente.",
            "F1: exibe esta ajuda.",
            "",
            "O efeito só é aplicado depois da confirmação nas opções do efeito.",
        ]

    def _on_timer(self, event: wx.TimerEvent) -> None:
        was_playing = self._was_playing
        self._sync()
        if was_playing and not self._was_playing and self._player.position() >= self._player.duration:
            self.manager.speaker.speak(PREVIEW_END_TEXT)

    def _sync(self) -> None:
        player = self._player
        self._was_playing = player.playing
        state = self._control.state_text(self._was_playing)
        text = (
            f"{opening_text(self._label)} - {state} - "
            f"{clock_time(player.position())} de {clock_time(player.duration)}"
        )
        output = self.manager.output_status
        if self._status.GetLabel() != text or self._output.GetLabel() != output:
            self._status.SetLabel(text)
            self._output.SetLabel(output)
            self.Layout()

    def _on_destroy(self, event: wx.WindowDestroyEvent) -> None:
        if event.GetEventObject() is self:
            self._timer.Stop()
            self._player.stop_preview()
        event.Skip()
