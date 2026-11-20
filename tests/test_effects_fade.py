import unittest

import numpy as np

from src.models.effects import engine, fade
from src.models.effects.catalog import EFFECTS, find_effect
from src.models.effects.errors import EffectError

RATE = 100


def frames(seconds: int, value: float = 0.5) -> np.ndarray:
    return np.full((seconds * RATE, 2), value, dtype=np.float32)


def run(effect, data, seconds, start=0, end=None):
    return engine.run(effect, data, RATE, start, len(data) if end is None else end, {fade.DURATION: seconds})


class FadeInTests(unittest.TestCase):
    def test_starts_in_silence_and_reaches_previous_volume(self):
        data = frames(10)
        result = run(fade.FADE_IN, data, 2)
        self.assertEqual(float(result[0, 0]), 0.0)
        self.assertAlmostEqual(float(result[2 * RATE - 1, 0]), 0.5, places=6)
        np.testing.assert_array_equal(result[2 * RATE:], data[2 * RATE:])

    def test_volume_rises_gradually_and_never_passes_previous_volume(self):
        result = run(fade.FADE_IN, frames(10), 3)
        curve = result[:3 * RATE, 0]
        self.assertTrue(np.all(np.diff(curve) > 0))
        self.assertLessEqual(float(np.abs(result).max()), 0.5)

    def test_starts_at_selection_start(self):
        data = frames(10)
        result = run(fade.FADE_IN, data, 2, 3 * RATE, 8 * RATE)
        np.testing.assert_array_equal(result[:3 * RATE], data[:3 * RATE])
        self.assertEqual(float(result[3 * RATE, 0]), 0.0)
        np.testing.assert_array_equal(result[5 * RATE:], data[5 * RATE:])


class DurationTests(unittest.TestCase):
    def test_duration_limits(self):
        parameter = fade.DURATION_PARAMETER
        self.assertEqual((parameter.minimum, parameter.maximum, parameter.default), (1, 60, 5))

    def test_duration_equal_to_available_audio_is_accepted(self):
        result = run(fade.FADE_IN, frames(3), 3)
        self.assertEqual(float(result[0, 0]), 0.0)

    def test_duration_longer_than_selection_is_refused_and_not_adjusted(self):
        for effect in (fade.FADE_IN,):
            data = frames(10)
            original = data.copy()
            with self.subTest(effect=effect.effect_id):
                with self.assertRaises(EffectError) as raised:
                    run(effect, data, 4, 2 * RATE, 5 * RATE)
                self.assertEqual((raised.exception.reason, raised.exception.hint), fade.TOO_LONG)
                np.testing.assert_array_equal(data, original)

    def test_duration_outside_limits_is_refused(self):
        for seconds in (0, 61):
            with self.subTest(seconds=seconds), self.assertLogs(engine.logger, level="WARNING"):
                with self.assertRaises(EffectError):
                    run(fade.FADE_IN, frames(70), seconds)

    def test_audio_length_is_preserved(self):
        for effect in (fade.FADE_IN,):
            with self.subTest(effect=effect.effect_id):
                self.assertEqual(run(effect, frames(10), 2).shape, (10 * RATE, 2))


class CatalogTests(unittest.TestCase):
    def test_fades_are_in_the_catalog_with_their_keys(self):
        self.assertEqual(find_effect("fade_in").key, "I")
        self.assertIn(fade.FADE_IN, EFFECTS)

    def test_fades_use_selection_and_have_no_family(self):
        for effect in (fade.FADE_IN,):
            with self.subTest(effect=effect.effect_id):
                self.assertTrue(effect.uses_selection)
                self.assertIsNone(effect.family)


if __name__ == "__main__":
    unittest.main()
