import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import wx

from src.models import audio_edit
from src.models.audio_edit import EditError
from src.models.audio_player import (
    NO_OUTPUT_HINT,
    NO_OUTPUT_MESSAGE,
    PLAYBACK_HINT,
    PLAYBACK_MESSAGE,
    AudioLoadError,
    PlaybackError,
    load_audio,
)
from src.models.audio_save import AudioSaveError, save_audio
from src.models.errors import MEMORY_HINT, SoundMineError, unexpected_option_message, user_message
from src.view.player_screen import PlayerScreen
from tests.test_audio_player import FakeScreenPlayer
from tests.test_exit_flow import ScreenFlowCase, flush

_app = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


def raised(action) -> SoundMineError:
    try:
        action()
    except SoundMineError as error:
        return error
    raise AssertionError("a ação deveria falhar")


AUDIO = np.zeros((10, 2), dtype=np.float32)
EMPTY = np.zeros((0, 2), dtype=np.float32)

EDIT_ERRORS = {
    "remover antes no início": lambda: audio_edit.remove_before(AUDIO, 0),
    "remover antes no final": lambda: audio_edit.remove_before(AUDIO, 10),
    "remover depois no final": lambda: audio_edit.remove_after(AUDIO, 10),
    "remover depois no início": lambda: audio_edit.remove_after(AUDIO, 0),
    "remover entre sem ponto": lambda: audio_edit.remove_between(AUDIO, 3, None),
    "remover entre no ponto": lambda: audio_edit.remove_between(AUDIO, 3, 3),
    "remover entre tudo": lambda: audio_edit.remove_between(AUDIO, 0, 10),
    "cursor inválido": lambda: audio_edit.remove_before(AUDIO, 20),
    "inserir sem áudio": lambda: audio_edit.insert(AUDIO, EMPTY, 0),
    "fundo sem áudio": lambda: audio_edit.overlay(AUDIO, EMPTY, 0, 100, 30),
    "fundo com volume inválido": lambda: audio_edit.overlay(AUDIO, AUDIO, 0, 150, 30),
    "fundo no final": lambda: audio_edit.overlay(AUDIO, AUDIO, 10, 100, 30),
}


class MessageFormatTests(unittest.TestCase):
    def assert_sentence(self, text: str) -> None:
        self.assertTrue(text[0].isupper(), text)
        self.assertTrue(text.endswith("."), text)

    def test_message_joins_reason_and_hint(self):
        self.assertEqual(user_message(AudioSaveError("Motivo.", "O que fazer.")), "Motivo. O que fazer.")
        self.assertEqual(user_message(AudioSaveError("Motivo.")), "Motivo.")
        self.assertEqual(user_message(RuntimeError("falha")), "falha")

    def test_unexpected_option_message(self):
        self.assertEqual(unexpected_option_message("Salvar"),
                         "Ocorreu um erro inesperado na opção Salvar. Tente novamente.")

    def test_edit_errors_have_reason_and_hint_without_old_prefix(self):
        for name, action in EDIT_ERRORS.items():
            with self.subTest(name=name):
                error = raised(action)
                self.assertIsInstance(error, EditError)
                self.assert_sentence(error.reason)
                self.assertTrue(error.hint, name)
                self.assert_sentence(error.hint)
                self.assertNotIn("não pode ser realizada", user_message(error))
                self.assertNotIn("A operação", user_message(error))

    def test_edit_hints_point_to_the_player(self):
        for name in ("remover antes no início", "remover depois no final", "remover entre sem ponto",
                     "remover entre no ponto"):
            with self.subTest(name=name):
                self.assertIn("No player", raised(EDIT_ERRORS[name]).hint)
        self.assertIn("M", raised(EDIT_ERRORS["remover entre sem ponto"]).hint)

    def test_load_errors_say_what_to_do(self):
        with tempfile.TemporaryDirectory() as folder:
            unsupported = raised(lambda: load_audio(Path(folder) / "audio.flac"))
            missing = raised(lambda: load_audio(Path(folder) / "sumiu.mp3"))
        self.assertEqual(user_message(unsupported),
                         "O formato do arquivo não é aceito. Use arquivos MP3, M4A, WAV ou OGG.")
        self.assertEqual(missing.hint, "Ele pode ter sido movido, renomeado ou apagado.")

    def test_save_errors_say_what_to_do(self):
        data = np.zeros((100, 2), dtype=np.float32)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "saida.wav"
            invalid = raised(lambda: save_audio(data, 44100, target, "flac", "Estéreo", 44100))
            extension = raised(lambda: save_audio(data, 44100, Path(folder) / "saida.mp3", "wav", "Estéreo", 44100))
            no_folder = raised(lambda: save_audio(data, 44100, Path(folder) / "nao" / "saida.wav", "wav",
                                                  "Estéreo", 44100))
            with mock.patch("src.models.audio_save.tempfile.mkstemp", side_effect=PermissionError(13, "negado")):
                denied = raised(lambda: save_audio(data, 44100, target, "wav", "Estéreo", 44100))
        self.assertIn("guia Geral", invalid.hint)
        self.assertEqual(user_message(extension),
                         "O arquivo será salvo no formato WAV, definido nas configurações. Use a extensão .wav.")
        self.assertEqual(no_folder.hint, "Escolha outra pasta.")
        self.assertIn("Escolha outra pasta", denied.hint)

    def test_output_and_playback_messages_use_sound_output_terms(self):
        self.assertEqual(user_message(AudioLoadError(NO_OUTPUT_MESSAGE, NO_OUTPUT_HINT)),
                         "Nenhuma saída de som disponível. Conecte ou ative um dispositivo de som e tente novamente.")
        message = user_message(PlaybackError(PLAYBACK_MESSAGE, PLAYBACK_HINT))
        self.assertNotIn("tocar o arquivo", message)
        self.assertIn("dispositivo de som", message)

    def test_memory_hint_points_to_settings(self):
        self.assertIn("Memória em megabytes", MEMORY_HINT)
        self.assertIn("guia Desempenho", MEMORY_HINT)


class PlayerStatusTests(ScreenFlowCase):
    def test_status_and_speech_use_the_same_words(self):
        player = FakeScreenPlayer()
        screen = PlayerScreen(self.manager.parent, self.manager, player)
        self.manager.push(screen)
        flush()
        self.assertIn(" - Reproduzindo - ", screen._status.GetLabel())
        self.press(wx.WXK_SPACE)
        self.assertIn(" - Pausado - ", screen._status.GetLabel())
        self.press(wx.WXK_SPACE)
        self.assertIn("fala: Reproduzindo", self.log)
        self.assertNotIn("Tocando", screen._status.GetLabel())


if __name__ == "__main__":
    unittest.main()
