from src.models.app_log import operation as log_operation
from src.models.audio_player import PlaybackError
from src.models.errors import PLAY, user_message
from src.view.keys import Command, KeyCommand

SEEK_SECONDS = 5
START_TEXT = "Início do som"
END_TEXT = "Fim do som"
WAITING_TEXT = "Aguardando saída de som"
PLAYING_TEXT = "Reproduzindo"
PAUSED_TEXT = "Pausado"


class PlaybackControl:
    def __init__(self, manager, player, start_text: str = START_TEXT, end_text: str = END_TEXT) -> None:
        self._manager = manager
        self._player = player
        self.start_text = start_text
        self.end_text = end_text

    def play(self) -> bool:
        with log_operation(PLAY):
            try:
                self._player.play()
            except PlaybackError as error:
                self._manager.announcer.error(user_message(error), PLAY, error)
                self._manager.focus_window()
                return False
        return True

    def handle(self, command: KeyCommand) -> bool:
        match command.command:
            case Command.SPACE:
                self._toggle()
            case Command.LEFT:
                self.seek(self._player.position() - SEEK_SECONDS)
            case Command.RIGHT:
                self.seek(self._player.position() + SEEK_SECONDS)
            case Command.HOME:
                self.seek(0)
            case Command.END:
                self.seek(self._player.duration)
            case _:
                return False
        return True

    def seek(self, seconds: float) -> None:
        position = self._player.seek(seconds)
        if position <= 0:
            self._manager.speaker.speak(self.start_text)
        elif position >= self._player.duration:
            self._player.pause()
            self._manager.speaker.speak(self.end_text)

    def state_text(self, playing: bool) -> str:
        if self._player.waiting:
            return WAITING_TEXT
        return PLAYING_TEXT if playing else PAUSED_TEXT

    def _toggle(self) -> None:
        if self._player.playing:
            self._player.pause()
            self._manager.speaker.speak(PAUSED_TEXT)
        elif self.play():
            text = PLAYING_TEXT
            if self._player.waiting:
                text += f". {WAITING_TEXT}"
            self._manager.speaker.speak(text)
