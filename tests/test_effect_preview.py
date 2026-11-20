import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import wx

from src.controllers import effect_preview
from src.models import audio_player
from src.models.audio_edit import EditError
from src.models.audio_output import OutputCoordinator
from src.models.audio_player import AudioPlayer
from src.view.confirm_screen import ConfirmScreen
from src.view.preview_screen import PREVIEW_END_TEXT, PreviewScreen
from tests.test_audio_output import HEADSET, SPEAKERS, Clock, FakeBackend
from tests.test_exit_flow import ScreenFlowCase, flush

RATE = 48000
SECONDS = 10
LABEL = "Teste"

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


def fake_load(path, memory_mb, rate):
    return np.full((rate * SECONDS, 2), 0.25, dtype=np.float32), rate


def make_player(case: unittest.TestCase) -> AudioPlayer:
    outputs = OutputCoordinator(FakeBackend([HEADSET, SPEAKERS], HEADSET), Clock())
    patcher = mock.patch.object(audio_player, "load_audio", side_effect=fake_load)
    patcher.start()
    case.addCleanup(patcher.stop)
    return AudioPlayer(Path("musica.wav"), 0, outputs)


def read(player: AudioPlayer, frames: int) -> np.ndarray:
    out = np.zeros((frames, 2), dtype=np.float32)
    player.audio_callback(out, frames, None, None)
    return out


class PlayerPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.player = make_player(self)
        self.candidate = np.full_like(self.player.data, 0.5)
        self.player.seek(4)
        self.player.mark()
        self.player.seek(2)

    def test_rate_is_public(self):
        self.assertEqual(self.player.rate, RATE)

    def test_preview_plays_only_the_candidate_range(self):
        self.player.start_preview(self.candidate, RATE, 3 * RATE)
        self.assertTrue(self.player.previewing)
        self.assertEqual(self.player.duration, 2)
        self.assertEqual(self.player.position(), 0)
        self.player.play()
        np.testing.assert_array_equal(read(self.player, 100), np.full((100, 2), 0.5, dtype=np.float32))

    def test_preview_does_not_change_editor_state(self):
        data = self.player.data
        self.player.start_preview(self.candidate, 0, len(self.candidate))
        self.player.play()
        read(self.player, RATE)
        self.player.seek(8)
        self.player.stop_preview()
        self.assertFalse(self.player.previewing)
        self.assertIs(self.player.data, data)
        self.assertEqual(self.player.position(), 2)
        self.assertEqual(self.player.marked, 4)
        self.assertFalse(self.player.has_changes)
        self.assertFalse(self.player.playing)

    def test_cursor_frame_is_the_editor_cursor_during_preview(self):
        self.player.start_preview(self.candidate, 0, len(self.candidate))
        self.player.seek(7)
        self.assertEqual(self.player.cursor_frame, 2 * RATE)
        self.assertEqual(self.player.marked_frame, 4 * RATE)

    def test_editing_is_refused_during_preview(self):
        self.player.start_preview(self.candidate, 0, len(self.candidate))
        for action in (lambda: self.player.edit(lambda d, c, m: (d, c)), self.player.undo, self.player.mark):
            with self.assertRaises(EditError):
                action()

    def test_invalid_range_is_refused(self):
        for start, end in ((5, 5), (-1, 10), (0, len(self.candidate) + 1)):
            with self.subTest(start=start, end=end), self.assertRaises(EditError):
                self.player.start_preview(self.candidate, start, end)
        self.assertFalse(self.player.previewing)

    def test_preview_counts_in_memory_limit(self):
        self.player._memory_mb = 1
        with self.assertRaises(EditError):
            self.player.start_preview(self.candidate, 0, len(self.candidate))
        self.assertFalse(self.player.previewing)

    def test_end_of_preview_stops_playback(self):
        self.player.start_preview(self.candidate, 0, 100)
        self.player.play()
        read(self.player, 200)
        self.assertFalse(self.player.playing)
        self.player.play()
        self.assertEqual(self.player.position(), 0)


class PreviewFlowTests(ScreenFlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.player = make_player(self)
        self.original = self.player.data
        self.candidate = np.full_like(self.original, 0.5)
        self.player.seek(3)
        self.finished = 0
        effect_preview.open_preview(self.manager, self.player, LABEL, self.candidate, 0,
                                    len(self.candidate), self.finish)
        flush()

    def finish(self) -> None:
        self.finished += 1

    def options(self) -> ConfirmScreen:
        self.press(wx.WXK_ESCAPE)
        return self.confirmation()

    def test_opening_announces_and_plays(self):
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.assertIn("fala: Prévia do efeito Teste", self.log)
        self.assertTrue(self.player.previewing)
        self.assertTrue(self.player.playing)

    def test_enter_does_nothing_during_playback(self):
        self.press(wx.WXK_RETURN)
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.assertTrue(self.player.previewing)
        self.assertIs(self.player.data, self.original)

    def test_escape_during_playback_only_opens_options(self):
        self.log.clear()
        screen = self.options()
        self.assertEqual(screen.selected, effect_preview.APPLY_LABEL)
        self.assertEqual(self.log[:2], ["fala: Deseja aplicar o efeito Teste?", "fala: Aplicar efeito"])
        self.assertTrue(self.player.previewing)
        self.assertFalse(self.player.playing)
        self.assertEqual(self.finished, 0)

    def test_options_order(self):
        self.assertEqual(self.options()._confirmation.labels,
                         (effect_preview.APPLY_LABEL, effect_preview.DISCARD_LABEL, effect_preview.LISTEN_LABEL))

    def test_apply_replaces_audio_and_returns(self):
        self.options()
        self.press(wx.WXK_RETURN)
        self.assertIn("concluído: Efeito Teste aplicado.", self.log)
        self.assertIs(self.player.data, self.candidate)
        self.assertFalse(self.player.previewing)
        self.assertTrue(self.player.has_changes)
        self.assertEqual(self.player.position(), 3)
        self.assertIsNone(self.player.marked)
        self.assertIs(self.manager.current, self.main_menu)
        self.assertEqual(self.finished, 1)

    def test_escape_in_options_does_nothing(self):
        screen = self.options()
        self.log.clear()
        self.press(wx.WXK_ESCAPE)
        self.assertIs(self.manager.current, screen)
        self.assertTrue(self.player.previewing)
        self.assertIs(self.player.data, self.original)
        self.assertEqual(self.finished, 0)
        self.assertNotIn("fala: Efeito não aplicado.", self.log)
        self.press(wx.WXK_RETURN)
        self.assertIs(self.player.data, self.candidate)

    def test_options_help_does_not_offer_escape(self):
        lines = self.options().help_lines()
        self.assertFalse(any(line.startswith("Esc") for line in lines))

    def test_not_apply_discards(self):
        self.options()
        self.press(wx.WXK_DOWN)
        self.press(wx.WXK_RETURN)
        self.assert_discarded()

    def assert_discarded(self):
        self.assertIn("fala: Efeito não aplicado.", self.log)
        self.assertIs(self.player.data, self.original)
        self.assertFalse(self.player.previewing)
        self.assertFalse(self.player.has_changes)
        self.assertEqual(self.player.position(), 3)
        self.assertIs(self.manager.current, self.main_menu)
        self.assertEqual(self.finished, 1)

    def test_listen_again_restarts_from_the_beginning(self):
        self.player.seek(5)
        screen = self.options()
        self.letter("O")
        self.assertIs(self.manager.current, screen)
        self.assertEqual(screen.selected, effect_preview.LISTEN_LABEL)
        self.press(wx.WXK_RETURN)
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.assertTrue(self.player.previewing)
        self.assertTrue(self.player.playing)
        self.assertLess(self.player.position(), 1)

    def test_end_of_preview_keeps_screen_open(self):
        screen = self.manager.current
        self.player.seek(SECONDS - 0.001)
        self.player.play()
        screen._sync()
        read(self.player, RATE)
        screen._on_timer(None)
        self.assertIn(f"fala: {PREVIEW_END_TEXT}", self.log)
        self.assertIs(self.manager.current, screen)
        self.assertTrue(self.player.previewing)

    def test_letters_do_not_apply(self):
        self.options()
        self.letter("A")
        self.letter("N")
        self.assertIsInstance(self.manager.current, ConfirmScreen)
        self.assertTrue(self.player.previewing)


if __name__ == "__main__":
    unittest.main()
