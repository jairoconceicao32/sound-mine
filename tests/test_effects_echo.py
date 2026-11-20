import unittest

import numpy as np
import wx

from src.controllers import effects_menu
from src.models.effects import echo, engine
from src.models.effects.catalog import find_effect
from src.view.confirm_screen import ConfirmScreen
from src.view.editor_screen import EditorScreen
from src.view.preview_screen import PreviewScreen
from tests.test_effect_preview import RATE, SECONDS, make_player
from tests.test_exit_flow import ScreenFlowCase, flush

SMALL_RATE = 1000

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


def impulse(length: int, position: int = 0, value: float = 0.5) -> np.ndarray:
    data = np.zeros((length, 2), dtype=np.float32)
    data[position] = value
    return data


def parameters(delay: int = 100, mix: int = 50) -> dict[str, int]:
    return {echo.DELAY: delay, echo.MIX: mix}


class EchoTests(unittest.TestCase):
    def test_repetitions_follow_interval_mix_and_halving(self):
        result = echo.echo(impulse(10), SMALL_RATE, parameters(delay=100, mix=50))
        self.assertAlmostEqual(float(result[0, 0]), 0.5)
        self.assertAlmostEqual(float(result[100, 0]), 0.25)
        self.assertAlmostEqual(float(result[200, 0]), 0.125)
        self.assertAlmostEqual(float(result[300, 0]), 0.0625)
        self.assertEqual(float(result[50, 0]), 0.0)

    def test_original_stays_at_full_volume(self):
        data = np.full((50, 2), 0.3, dtype=np.float32)
        result = echo.echo(data, SMALL_RATE, parameters(delay=100))
        np.testing.assert_array_equal(result[:50], data)

    def test_tail_lasts_until_repetitions_are_inaudible(self):
        count = echo.repetitions(0.75, echo.FEEDBACK)
        self.assertEqual(count, 10)
        self.assertGreaterEqual(0.75 * echo.FEEDBACK ** (count - 1), echo.SILENCE)
        self.assertLess(0.75 * echo.FEEDBACK ** count, echo.SILENCE)
        result = echo.echo(impulse(10), SMALL_RATE, parameters(delay=300, mix=75))
        self.assertEqual(len(result), 10 + count * 300)

    def test_zero_mix_changes_nothing(self):
        data = impulse(10)
        result = echo.echo(data, SMALL_RATE, parameters(mix=0))
        np.testing.assert_array_equal(result, data)

    def test_super_echo_is_louder_and_longer(self):
        normal = echo.echo(impulse(10), SMALL_RATE, parameters(delay=100, mix=50))
        strong = echo.super_echo(impulse(10), SMALL_RATE, parameters(delay=100, mix=50))
        self.assertAlmostEqual(float(strong[100, 0]), 0.5 * 0.75)
        self.assertAlmostEqual(float(strong[200, 0]), 0.5 * 0.75 * 0.7, places=6)
        self.assertGreater(float(strong[100, 0]), float(normal[100, 0]))
        self.assertGreater(len(strong), len(normal))

    def test_super_echo_mix_is_limited_to_100(self):
        strong = echo.super_echo(impulse(10), SMALL_RATE, parameters(delay=100, mix=80))
        self.assertAlmostEqual(float(strong[100, 0]), 0.5)

    def test_input_is_not_changed(self):
        data = impulse(10)
        original = data.copy()
        echo.super_echo(data, SMALL_RATE, parameters())
        np.testing.assert_array_equal(data, original)

    def test_catalog_entries(self):
        for effect_id, key in (("eco", "E"), ("super_eco", "S")):
            with self.subTest(effect=effect_id):
                effect = find_effect(effect_id)
                self.assertEqual((effect.key, effect.family, effect.adds_tail), (key, "eco", True))
                self.assertEqual([parameter.name for parameter in effect.parameters], ["echo_delay", "echo_percent"])


class EngineTailTests(unittest.TestCase):
    def test_without_selection_audio_gets_longer(self):
        data = impulse(1000)
        candidate, effect_end = engine.apply(echo.ECHO, data, SMALL_RATE, 0, 1000, parameters(delay=100))
        self.assertGreater(len(candidate), 1000)
        self.assertEqual(effect_end, len(candidate))

    def test_with_selection_tail_is_added_to_following_audio(self):
        data = np.full((2000, 2), 0.1, dtype=np.float32)
        data[0:100] = 0.0
        data[100] = 0.4
        candidate, effect_end = engine.apply(echo.ECHO, data, SMALL_RATE, 0, 150, parameters(delay=100, mix=50))
        self.assertEqual(len(candidate), 2000)
        self.assertAlmostEqual(float(candidate[200, 0]), 0.1 + 0.2, places=6)
        self.assertAlmostEqual(float(candidate[300, 0]), 0.1 + 0.1, places=6)
        self.assertEqual(effect_end, 150 + echo.repetitions(0.5, echo.FEEDBACK) * 100)
        np.testing.assert_array_equal(candidate[effect_end:], data[effect_end:])

    def test_tail_past_audio_end_extends_audio(self):
        data = impulse(1000, position=950)
        candidate, effect_end = engine.apply(echo.ECHO, data, SMALL_RATE, 900, 1000, parameters(delay=100))
        self.assertEqual(len(candidate), effect_end)
        self.assertGreater(effect_end, 1000)

    def test_echo_over_loud_audio_is_normalized(self):
        data = np.full((1000, 2), 0.9, dtype=np.float32)
        candidate, _ = engine.apply(echo.ECHO, data, SMALL_RATE, 0, 1000, parameters(delay=100, mix=75))
        self.assertAlmostEqual(engine.peak(candidate), engine.PEAK_LIMIT, places=6)

    def test_effect_without_tail_must_keep_length(self):
        spec = find_effect("fade_in")
        self.assertFalse(spec.adds_tail)


class EchoMenuTests(ScreenFlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.player = make_player(self)
        self.original = self.player.data
        menu = effects_menu.build_effects_menu(self.manager, self.player)
        self.screen = EditorScreen(self.manager.parent, self.manager, menu, self.player)
        self.manager.push(self.screen)
        flush()

    def apply_preview(self) -> None:
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.press(wx.WXK_ESCAPE)
        self.press(wx.WXK_RETURN)
        flush()

    def test_echo_uses_settings_and_extends_audio_and_levels(self):
        self.manager.settings.echo_delay = 300
        self.manager.settings.echo_percent = 75
        self.letter("E")
        self.assertIn("fala: Prévia do efeito Eco", self.log)
        self.apply_preview()
        tail = echo.repetitions(0.75, echo.FEEDBACK) * round(0.3 * RATE)
        self.assertEqual(len(self.player.data), SECONDS * RATE + tail)
        self.assertEqual(len(self.player.levels), len(self.player.data))
        self.assertEqual(self.player.effects, {"eco": "eco"})

    def test_preview_with_selection_includes_tail(self):
        self.manager.settings.echo_delay = 300
        self.manager.settings.echo_percent = 75
        self.player.seek(2)
        self.player.mark()
        self.player.seek(4)
        self.letter("E")
        tail = echo.repetitions(0.75, echo.FEEDBACK) * round(0.3 * RATE)
        self.assertAlmostEqual(self.player.duration, 2 + tail / RATE, places=3)
        self.apply_preview()
        self.assertEqual(len(self.player.data), SECONDS * RATE)

    def test_super_echo_replaces_echo(self):
        self.manager.settings.echo_delay = 300
        self.manager.settings.echo_percent = 50
        self.letter("E")
        self.apply_preview()
        self.letter("S")
        self.assertIsInstance(self.manager.current, ConfirmScreen)
        self.press(wx.WXK_UP)
        self.press(wx.WXK_RETURN)
        self.apply_preview()
        expected, _ = engine.apply(echo.SUPER_ECHO, self.original, RATE, 0, len(self.original),
                                   {echo.DELAY: 300, echo.MIX: 50})
        np.testing.assert_allclose(self.player.data, expected, rtol=1e-6)
        self.assertEqual(self.player.effects, {"eco": "super_eco"})


if __name__ == "__main__":
    unittest.main()
