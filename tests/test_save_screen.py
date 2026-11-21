import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import wx

from src.controllers import editor_menu
from src.controllers.editor_exit import NOT_SAVED_MESSAGE
from src.models.audio_save import SAVE_FAILED_HINT, SAVE_FAILED_MESSAGE, AudioSaveError
from src.models.save_feedback import progress_text
from src.models.save_task import PROGRESS_AFTER_SECONDS
from src.view.save_screen import (
    CANCELING_TEXT,
    CLOSE_REFUSED_TEXT,
    SAVING_TEXT,
    SaveScreen,
)
from tests.test_exit_flow import FakePlayer, ScreenFlowCase, flush

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


class SaveSettings:
    disable_tips = False
    format = "wav"
    sample_rate = "44100"
    channel = "Estéreo"
    memory_mb = 0


class BlockingPlayer(FakePlayer):
    def __init__(self) -> None:
        super().__init__(True)
        self.release = threading.Event()
        self.halfway = threading.Event()
        self.error: Exception | None = None
        self.saved_paths: list[Path] = []

    def save(self, path, file_format, channel, sample_rate, progress=None) -> int:
        progress(0.5)
        self.halfway.set()
        self.release.wait(5)
        progress(1.0)
        if self.error is not None:
            raise self.error
        self.saved_paths.append(path)
        self.has_changes = False
        return sample_rate


def wait_until(condition, seconds: float = 5) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return True
        flush()
        time.sleep(0.01)
    return condition()


class SaveScreenTests(ScreenFlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.manager.settings = SaveSettings()
        self.choose_file = mock.patch.object(editor_menu, "choose_save_file", return_value=Path("saida.wav"))
        self.choose_file.start()
        self.addCleanup(self.choose_file.stop)
        self.results: list[bool] = []

    def open_blocking(self) -> BlockingPlayer:
        player = BlockingPlayer()
        editor_menu.open_editor(self.manager, player)
        self.log.clear()
        self.addCleanup(player.release.set)
        return player

    def start_save(self, player: BlockingPlayer) -> SaveScreen:
        editor_menu.save_audio_file(self.manager, player, self.results.append)
        self.assertTrue(player.halfway.wait(5))
        flush()
        screen = self.manager.current
        self.assertIsInstance(screen, SaveScreen)
        return screen

    def finish(self, player: BlockingPlayer) -> None:
        player.release.set()
        self.assertTrue(wait_until(lambda: self.results))

    def test_save_runs_in_background_and_finishes_with_confirmation(self):
        player = self.open_blocking()
        editor = self.manager.current
        self.start_save(player)
        self.assertIn(f"fala: {SAVING_TEXT}", self.log)
        self.assertEqual(self.results, [])
        self.finish(player)
        self.assertEqual(self.results, [True])
        self.assertIs(self.manager.current, editor)
        self.assertIn("concluído: Arquivo salvo: saida.wav.", self.log)

    def test_space_does_not_show_percentage_for_small_files(self):
        player = self.open_blocking()
        self.start_save(player)
        self.log.clear()
        self.press(wx.WXK_SPACE)
        self.assertEqual(self.log, [f"fala: {SAVING_TEXT}"])
        self.finish(player)

    def test_space_shows_real_percentage_for_long_saves(self):
        player = self.open_blocking()
        screen = self.start_save(player)
        self.log.clear()
        self.make_long(screen)
        self.press(wx.WXK_SPACE)
        self.assertEqual(self.log[0], "fala: Salvando: 50 por cento.")
        self.assertEqual(progress_text(0.5), "Salvando: 50 por cento.")
        self.finish(player)

    def make_long(self, screen: SaveScreen) -> None:
        later = time.monotonic() + PROGRESS_AFTER_SECONDS + 1
        screen._task._clock = lambda: later

    def beeps(self) -> list[str]:
        return [item for item in self.log if item.startswith("beep:")]

    def test_small_save_has_no_beeps_percentage_or_confirmation_sound(self):
        player = self.open_blocking()
        screen = self.start_save(player)
        screen._on_timer(None)
        self.finish(player)
        self.assertEqual(self.beeps(), [])
        self.assertNotIn("fala: Salvando: 50 por cento.", self.log)
        self.assertNotIn("som sempre: confirme", self.log)

    def test_long_save_beeps_announces_and_confirms(self):
        player = self.open_blocking()
        screen = self.start_save(player)
        self.make_long(screen)
        screen._on_timer(None)
        self.assertEqual(self.beeps(), ["beep: navigation 1.10"])
        self.assertIn("fala: Salvando: 50 por cento.", self.log)
        self.finish(player)
        self.assertIn("som sempre: confirme", self.log)
        self.assertLess(self.log.index("som sempre: confirme"),
                        self.log.index("concluído: Arquivo salvo: saida.wav."))

    def test_beeps_stop_and_no_confirmation_after_cancel(self):
        player = self.open_blocking()
        screen = self.start_save(player)
        self.make_long(screen)
        screen._on_timer(None)
        self.press(wx.WXK_ESCAPE)
        screen._on_timer(None)
        self.assertEqual(len(self.beeps()), 1)
        self.finish(player)
        self.assertNotIn("som sempre: confirme", self.log)

    def test_no_confirmation_sound_after_failure(self):
        player = self.open_blocking()
        player.error = AudioSaveError(SAVE_FAILED_MESSAGE, SAVE_FAILED_HINT)
        screen = self.start_save(player)
        self.make_long(screen)
        screen._on_timer(None)
        self.finish(player)
        self.assertNotIn("som sempre: confirme", self.log)

    def test_sound_failure_does_not_stop_the_save(self):
        player = self.open_blocking()
        screen = self.start_save(player)
        self.make_long(screen)
        with mock.patch.object(self.manager.sounds, "play_pitched", side_effect=RuntimeError("sem som")):
            with self.assertLogs("src.view.save_screen", level="ERROR"):
                screen._on_timer(None)
        self.finish(player)
        self.assertEqual(self.results, [True])

    def test_esc_cancels_and_keeps_editor_with_changes(self):
        player = self.open_blocking()
        editor = self.manager.current
        self.start_save(player)
        self.press(wx.WXK_ESCAPE)
        self.assertIn(f"fala: {CANCELING_TEXT}", self.log)
        self.finish(player)
        self.assertEqual(self.results, [False])
        self.assertIs(self.manager.current, editor)
        self.assertIn(f"fala: {editor_menu.SAVE_CANCELED_MESSAGE}", self.log)
        self.assertEqual(player.saved_paths, [])
        self.assertTrue(player.has_changes)

    def test_alt_f4_is_refused_while_saving(self):
        player = self.open_blocking()
        screen = self.start_save(player)
        self.log.clear()
        self.assertFalse(self.alt_f4())
        self.assertTrue(self.frame)
        self.assertFalse(self.program_closed())
        self.assertIs(self.manager.current, screen)
        self.assertEqual(self.log, [f"fala: {CLOSE_REFUSED_TEXT}"])
        self.finish(player)
        self.assertEqual(self.results, [True])

    def test_other_keys_do_not_reach_the_editor_while_saving(self):
        player = self.open_blocking()
        screen = self.start_save(player)
        for key in ("R", "M", "S", "D", "T"):
            self.letter(key)
        self.press(wx.WXK_RETURN)
        self.press(wx.WXK_LEFT)
        self.assertIs(self.manager.current, screen)
        self.finish(player)

    def test_failure_shows_error_and_keeps_editor(self):
        player = self.open_blocking()
        editor = self.manager.current
        player.error = AudioSaveError(SAVE_FAILED_MESSAGE, SAVE_FAILED_HINT)
        self.start_save(player)
        self.finish(player)
        self.assertEqual(self.results, [False])
        self.assertIs(self.manager.current, editor)
        self.assertIn(f"erro [salvar]: {SAVE_FAILED_MESSAGE} {SAVE_FAILED_HINT}", self.log)

    def test_unexpected_failure_is_reported_as_save_failure(self):
        player = self.open_blocking()
        player.error = RuntimeError("inesperado")
        self.start_save(player)
        with self.assertLogs("src.controllers.editor_menu", level="ERROR"):
            self.finish(player)
        self.assertEqual(self.results, [False])
        self.assertIn(f"erro [salvar]: {SAVE_FAILED_MESSAGE} {SAVE_FAILED_HINT}", self.log)

    def test_choosing_no_file_does_not_open_save_screen(self):
        player = self.open_blocking()
        editor = self.manager.current
        with mock.patch.object(editor_menu, "choose_save_file", return_value=None):
            editor_menu.save_audio_file(self.manager, player, self.results.append)
        self.assertEqual(self.results, [False])
        self.assertIs(self.manager.current, editor)

    def test_save_and_leave_waits_for_save_then_returns_to_main_menu(self):
        player = self.open_blocking()
        self.press(wx.WXK_ESCAPE)
        self.choose("Salvar e sair")
        self.assertTrue(player.halfway.wait(5))
        flush()
        self.assertIsInstance(self.manager.current, SaveScreen)
        self.assertFalse(player.closed)
        player.release.set()
        self.assertTrue(wait_until(lambda: self.manager.current is self.main_menu))
        self.assertTrue(player.closed)

    def test_save_and_leave_canceled_keeps_editor_open(self):
        player = self.open_blocking()
        editor = self.manager.current
        self.press(wx.WXK_ESCAPE)
        self.choose("Salvar e sair")
        self.assertTrue(player.halfway.wait(5))
        flush()
        self.press(wx.WXK_ESCAPE)
        player.release.set()
        self.assertTrue(wait_until(lambda: f"fala: {NOT_SAVED_MESSAGE}" in self.log))
        self.assertIs(self.manager.current, editor)
        self.assertFalse(player.closed)


if __name__ == "__main__":
    unittest.main()
