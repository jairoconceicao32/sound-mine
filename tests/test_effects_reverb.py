import time
import unittest

import numpy as np
import wx

from src.controllers import effects_menu
from src.models.effects import engine, reverb
from src.models.effects.catalog import find_effect
from src.models.settings import Settings
from src.view.confirm_screen import ConfirmScreen
from src.view.editor_screen import EditorScreen
from src.view.preview_screen import PreviewScreen
from tests.test_effect_preview import RATE, SECONDS, make_player
from tests.test_exit_flow import ScreenFlowCase, flush

SMALL_RATE = 8000

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


def impulse(length: int, value: float = 0.5) -> np.ndarray:
    data = np.zeros((length, 2), dtype=np.float32)
    data[0] = value
    return data


def parameters(duration: int = 200, mix: int = 50) -> dict[str, int]:
    return {reverb.DURATION: duration, reverb.MIX: mix}


def response_length(rate: int, milliseconds: float) -> int:
    return reverb.pre_delay_frames(rate, milliseconds) + round(milliseconds * rate / 1000)


class CharacterTests(unittest.TestCase):
    def test_default_duration_is_a_room(self):
        self.assertEqual(Settings().reverb_delay, 1200)

    def test_reverb_is_three_times_longer_like_a_church(self):
        self.assertEqual(reverb.HALL_DURATION_FACTOR, 3)
        self.assertEqual(Settings().reverb_delay * reverb.HALL_DURATION_FACTOR, 3600)

    def test_pre_delay_grows_with_room_size_within_limits(self):
        ms = SMALL_RATE / 1000
        self.assertEqual(reverb.pre_delay_frames(SMALL_RATE, 100), round(5 * ms))
        self.assertEqual(reverb.pre_delay_frames(SMALL_RATE, 1200), round(18 * ms))
        self.assertEqual(reverb.pre_delay_frames(SMALL_RATE, 3600), round(54 * ms))
        self.assertEqual(reverb.pre_delay_frames(SMALL_RATE, 6000), round(60 * ms))


class ImpulseResponseTests(unittest.TestCase):
    def test_length_is_pre_delay_plus_duration(self):
        self.assertEqual(len(reverb.impulse_response(SMALL_RATE, 200)), 40 + 1600)
        self.assertEqual(len(reverb.impulse_response(SMALL_RATE, 1000)), 120 + 8000)

    def test_silent_during_pre_delay(self):
        response = reverb.impulse_response(SMALL_RATE, 1200)
        pre_delay = reverb.pre_delay_frames(SMALL_RATE, 1200)
        self.assertTrue(np.all(response[:pre_delay] == 0))
        self.assertTrue(np.any(response[pre_delay:pre_delay + 400] != 0))

    def test_decays_about_60_db_over_the_duration(self):
        for duration in (500, 1200, 3600):
            with self.subTest(duration=duration):
                response = reverb.impulse_response(RATE, duration)
                tail = response[reverb.pre_delay_frames(RATE, duration):, 0]
                tenth = len(tail) // 10
                first = float(np.sqrt(np.mean(tail[:tenth] ** 2)))
                last = float(np.sqrt(np.mean(tail[-tenth:] ** 2)))
                self.assertLess(20 * np.log10(last / first), -45)

    def test_energy_grows_with_duration_and_is_deterministic(self):
        for duration in (300, 1200, 3600):
            with self.subTest(duration=duration):
                response = reverb.impulse_response(SMALL_RATE, duration)
                expected = duration / 1000 / reverb.REFERENCE_SECONDS
                np.testing.assert_allclose(np.sum(response ** 2, axis=0), [expected, expected], rtol=1e-9)
                np.testing.assert_array_equal(response, reverb.impulse_response(SMALL_RATE, duration))

    def test_hall_sounds_bigger_than_room_at_every_moment(self):
        room = reverb.impulse_response(RATE, 1200)[:, 0]
        church = reverb.impulse_response(RATE, 3600)[:, 0]

        def level(response: np.ndarray, start: float, end: float) -> float:
            return float(np.sqrt(np.mean(response[int(start * RATE):int(end * RATE)] ** 2)))

        for start, end in ((0.06, 0.16), (0.3, 0.4), (0.8, 0.9)):
            with self.subTest(start=start):
                self.assertGreater(level(church, start, end), level(room, start, end))

    def test_channels_are_different(self):
        response = reverb.impulse_response(SMALL_RATE, 300)
        self.assertFalse(np.allclose(response[:, 0], response[:, 1]))

    def test_builds_up_gradually_instead_of_starting_at_full_strength(self):
        response = reverb.impulse_response(RATE, 1000)[:, 0]
        pre_delay = reverb.pre_delay_frames(RATE, 1000)
        ms = RATE // 1000

        def level(start: int, end: int) -> float:
            return float(np.sqrt(np.mean(response[pre_delay + start * ms:pre_delay + end * ms] ** 2)))

        self.assertLess(level(0, 10), level(30, 60) / 10)

    def test_high_frequencies_fade_faster_than_low_frequencies(self):
        response = reverb.impulse_response(RATE, 1000)[:, 0]
        frequencies = np.fft.rfftfreq(RATE // 10, 1 / RATE)

        def high_to_low(part: np.ndarray) -> float:
            power = np.abs(np.fft.rfft(part)) ** 2
            return float(power[frequencies > 5000].sum() / power[frequencies < 500].sum())

        early = high_to_low(response[RATE // 20:RATE // 20 + RATE // 10])
        late = high_to_low(response[RATE * 85 // 100:RATE * 85 // 100 + RATE // 10])
        self.assertLess(late, early / 100)

    def test_has_no_repeating_pattern_like_an_echo(self):
        for duration in (200, 1200, 3600):
            with self.subTest(duration=duration):
                response = reverb.impulse_response(RATE, duration)[:, 0]
                spectrum = np.abs(np.fft.rfft(response, 2 * len(response))) ** 2
                correlation = np.fft.irfft(spectrum)[:len(response)]
                self.assertLess(float(np.abs(correlation[RATE // 1000:]).max() / correlation[0]), 0.3)


class ConvolutionTests(unittest.TestCase):
    def test_matches_direct_convolution_across_blocks(self):
        rng = np.random.default_rng(1)
        signal = rng.standard_normal(reverb.BLOCK_FRAMES * 2 + 123)
        response = rng.standard_normal(500)
        np.testing.assert_allclose(reverb.convolve(signal, response), np.convolve(signal, response), atol=1e-8)


class ReverbTests(unittest.TestCase):
    def test_original_stays_and_reverb_is_added_with_mix(self):
        response = reverb.impulse_response(SMALL_RATE, 200)
        result = reverb.room_reverb(impulse(10), SMALL_RATE, parameters(200, 50))
        self.assertAlmostEqual(float(result[0, 0]), 0.5)
        np.testing.assert_allclose(result[1:len(response), 0], 0.5 * 0.5 * response[1:, 0], atol=1e-6)

    def test_tail_length(self):
        result = reverb.room_reverb(impulse(10), SMALL_RATE, parameters(200, 50))
        self.assertEqual(len(result), 10 + response_length(SMALL_RATE, 200) - 1)

    def test_zero_mix_changes_nothing(self):
        data = impulse(10)
        np.testing.assert_array_equal(reverb.room_reverb(data, SMALL_RATE, parameters(mix=0)), data)

    def test_hall_is_louder_and_longer(self):
        normal = reverb.room_reverb(impulse(10), SMALL_RATE, parameters(200, 50))
        strong = reverb.hall_reverb(impulse(10), SMALL_RATE, parameters(200, 50))
        self.assertEqual(len(strong), 10 + response_length(SMALL_RATE, 600) - 1)
        self.assertGreater(len(strong), len(normal))
        response = reverb.impulse_response(SMALL_RATE, 600)
        np.testing.assert_allclose(strong[1:len(response), 0], 0.5 * 0.6 * response[1:, 0], atol=1e-6)

    def test_hall_mix_reinforcement_is_12_and_limited_to_100(self):
        self.assertEqual(reverb.HALL_MIX_FACTOR, 1.2)
        response = reverb.impulse_response(SMALL_RATE, 600)
        strong = reverb.hall_reverb(impulse(10), SMALL_RATE, parameters(200, 90))
        np.testing.assert_allclose(strong[1:len(response), 0], 0.5 * response[1:, 0], atol=1e-6)

    def test_input_is_not_changed(self):
        data = impulse(10)
        original = data.copy()
        reverb.hall_reverb(data, SMALL_RATE, parameters())
        np.testing.assert_array_equal(data, original)

    def test_long_audio_is_processed_in_reasonable_time(self):
        data = np.random.default_rng(2).uniform(-0.3, 0.3, (RATE * 60, 2)).astype(np.float32)
        began = time.monotonic()
        result = reverb.hall_reverb(data, RATE, parameters(2000, 80))
        self.assertLess(time.monotonic() - began, 20)
        self.assertEqual(len(result), RATE * 60 + response_length(RATE, 6000) - 1)

    def test_catalog_entries(self):
        for effect_id, key in (("reverberacao", "R"), ("super_reverberacao", "X")):
            with self.subTest(effect=effect_id):
                effect = find_effect(effect_id)
                self.assertEqual((effect.key, effect.family, effect.adds_tail), (key, "reverberacao", True))
                self.assertEqual([parameter.name for parameter in effect.parameters],
                                 ["reverb_delay", "reverb_percent"])
                self.assertEqual(effect.parameter("reverb_delay").default, 1200)

    def test_loud_audio_is_normalized_by_engine(self):
        data = np.full((2000, 2), 0.9, dtype=np.float32)
        candidate, _ = engine.apply(reverb.REVERB, data, SMALL_RATE, 0, 2000, parameters(200, 80))
        self.assertAlmostEqual(engine.peak(candidate), engine.PEAK_LIMIT, places=6)


class ReverbMenuTests(ScreenFlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.player = make_player(self)
        self.original = self.player.data
        self.manager.settings.reverb_delay = 1200
        self.manager.settings.reverb_percent = 50
        menu = effects_menu.build_effects_menu(self.manager, self.player)
        self.screen = EditorScreen(self.manager.parent, self.manager, menu, self.player)
        self.manager.push(self.screen)
        flush()

    def apply_preview(self) -> None:
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.press(wx.WXK_ESCAPE)
        self.press(wx.WXK_RETURN)
        flush()

    def test_reverb_is_applied_and_extends_audio(self):
        self.letter("R")
        self.assertIn("fala: Prévia do efeito Reverberação", self.log)
        self.apply_preview()
        self.assertEqual(len(self.player.data), SECONDS * RATE + response_length(RATE, 3600) - 1)
        self.assertEqual(self.player.effects, {"reverberacao": "reverberacao"})

    def test_super_reverb_replaces_reverb(self):
        self.letter("R")
        self.apply_preview()
        self.letter("X")
        self.assertIsInstance(self.manager.current, ConfirmScreen)
        self.press(wx.WXK_UP)
        self.press(wx.WXK_RETURN)
        self.apply_preview()
        expected, _ = engine.apply(reverb.SUPER_REVERB, self.original, RATE, 0, len(self.original),
                                   parameters(1200, 50))
        np.testing.assert_allclose(self.player.data, expected, rtol=1e-5, atol=1e-6)
        self.assertEqual(len(self.player.data), SECONDS * RATE + response_length(RATE, 1200) - 1)
        self.assertEqual(self.player.effects, {"reverberacao": "super_reverberacao"})

    def test_reverb_and_echo_are_combined(self):
        self.manager.settings.echo_delay = 300
        self.manager.settings.echo_percent = 50
        self.letter("R")
        self.apply_preview()
        self.letter("E")
        self.assertIsInstance(self.manager.current, PreviewScreen)


if __name__ == "__main__":
    unittest.main()
