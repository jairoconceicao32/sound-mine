import wx

from src.models.audio_player import VOLUME_STEP
from src.view.keys import Command, KeyCommand
from src.view.playback import END_TEXT, SEEK_SECONDS, WAITING_TEXT, PlaybackControl
from src.view.screen import Screen

MARK_KEY = "M"
REFRESH_MS = 100
PLAYER_KEYS_TEXT = (
    "Espaço: tocar ou pausar   Setas para os lados: 5 segundos   "
    "Home: início   End: fim   M: memorizar ponto   F2: tempo   F3 e F4: volume   Esc: volta ao editor"
)


def spoken_time(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []

    if hours:
        parts.append(f"{hours} hora" if hours == 1 else f"{hours} horas")

    if minutes or hours:
        parts.append(
            f"{minutes} minuto" if minutes == 1 else f"{minutes} minutos"
        )

    if secs or not parts:
        parts.append(f"{secs} segundo" if secs == 1 else f"{secs} segundos")

    return " e ".join(parts)


def clock_time(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class PlayerScreen(Screen):
    def __init__(self, parent: wx.Window, manager, player) -> None:
        super().__init__(parent, manager)
        self._player = player
        self._control = PlaybackControl(manager, player)
        self._was_playing = False
        self._status = wx.StaticText(self, label="")
        self._output = wx.StaticText(self, label="")
        self._keys = wx.StaticText(self, label=PLAYER_KEYS_TEXT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._status, 0, wx.ALL, 10)
        sizer.Add(self._output, 0, wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self._keys, 0, wx.ALL, 10)
        self.SetSizer(sizer)
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer, self._timer)

    @property
    def title(self) -> str:
        return "Player"

    def on_activate(self) -> None:
        if self._control.play() and self._player.waiting:
            self.manager.speaker.speak(WAITING_TEXT)
        self._sync()
        self._timer.Start(REFRESH_MS)

    def output_changed(self) -> None:
        self._sync()

    def on_deactivate(self) -> None:
        if self.manager.current is not self:
            self._timer.Stop()

    def handle_command(self, command: KeyCommand) -> bool:
        match command.command:
            case Command.HELP:
                return False
            case Command.BACK:
                self._timer.Stop()
                self._player.pause()
                self.manager.pop()
                return True
            case Command.LETTER if command.char == MARK_KEY:
                position = self._player.mark()
                self.manager.speaker.speak(f"Ponto memorizado em {spoken_time(position)}")
            case Command.TIME:
                self.manager.speaker.speak(
                    f"{spoken_time(self._player.position())} de {spoken_time(self._player.duration)}"
                )
            case Command.VOLUME_DOWN | Command.VOLUME_UP:
                step = VOLUME_STEP if command.command is Command.VOLUME_UP else -VOLUME_STEP
                volume = self._player.change_volume(step)
                self.manager.speaker.speak(f"Volume {volume}%")
            case _:
                self._control.handle(command)
        self._sync()
        return True

    def help_lines(self) -> list[str]:
        return [
            "Player:",
            "Espaço: toca ou pausa o arquivo.",
            f"Seta para a esquerda: volta {SEEK_SECONDS} segundos.",
            f"Seta para a direita: avança {SEEK_SECONDS} segundos.",
            "Home: vai para o início do som.",
            "End: vai para o fim do som.",
            "M: memoriza a posição atual, usada em Remover entre o cursor e o ponto memorizado.",
            "F2: informa o tempo de reprodução.",
            "F3: diminui o volume.",
            "F4: aumenta o volume.",
            "Esc: pausa e volta ao editor.",
            "F1: exibe esta ajuda.",
            "",
            "Enquanto o player está aberto, o menu de edição fica bloqueado.",
        ]

    def _on_timer(self, event: wx.TimerEvent) -> None:
        was_playing = self._was_playing
        self._sync()
        if was_playing and not self._was_playing and self._player.position() >= self._player.duration:
            self.manager.speaker.speak(END_TEXT)

    def _sync(self) -> None:
        player = self._player
        self._was_playing = player.playing
        state = self._control.state_text(self._was_playing)
        text = (
            f"{player.file_name} - {state} - "
            f"{clock_time(player.position())} de {clock_time(player.duration)} - "
            f"Volume {player.volume}%"
        )
        output = self.manager.output_status
        if self._status.GetLabel() != text or self._output.GetLabel() != output:
            self._status.SetLabel(text)
            self._output.SetLabel(output)
            self.Layout()
