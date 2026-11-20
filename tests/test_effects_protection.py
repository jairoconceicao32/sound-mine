import unittest

import numpy as np

from src.models.effects import engine
from src.models.effects.contract import EffectSpec
from src.models.effects.errors import EffectError

RATE = 1000


def frames(count: int, value: float) -> np.ndarray:
    values = np.full(count, value, dtype=np.float32)
    values[1::2] = -value
    return np.column_stack((values, values))


def multiply(factor: float) -> EffectSpec:
    def process(chunk, rate, parameters):
        return chunk * np.float32(factor)

    return EffectSpec(effect_id="teste", label="Teste", key="T", family=None, uses_selection=True,
                      parameters=(), help_text="Efeito de teste.", process=process)


class NormalizationTests(unittest.TestCase):
    def test_limit_is_098(self):
        self.assertEqual(engine.PEAK_LIMIT, 0.98)

    def test_no_change_when_there_is_no_risk(self):
        data = frames(100, 0.4)
        candidate = engine.run(multiply(2.0), data, RATE, 0, 100, {})
        np.testing.assert_array_equal(candidate, data * np.float32(2.0))

    def test_whole_audio_is_normalized_when_effect_raises_peak(self):
        data = frames(100, 0.5)
        candidate = engine.run(multiply(3.0), data, RATE, 40, 60, {})
        self.assertAlmostEqual(engine.peak(candidate), engine.PEAK_LIMIT, places=6)
        factor = engine.PEAK_LIMIT / 1.5
        np.testing.assert_allclose(candidate[:40], data[:40] * factor, rtol=1e-6)
        np.testing.assert_allclose(candidate[60:], data[60:] * factor, rtol=1e-6)
        np.testing.assert_allclose(candidate[40:60], data[40:60] * 3.0 * factor, rtol=1e-6)

    def test_relative_dynamics_are_preserved(self):
        data = frames(100, 0.2)
        data[50:] *= np.float32(3.0)
        expected = data * np.float32(2.0)
        candidate = engine.run(multiply(2.0), data, RATE, 0, 100, {})
        np.testing.assert_allclose(candidate / candidate[0, 0], expected / expected[0, 0], rtol=1e-6)

    def test_peaks_are_never_cut(self):
        data = frames(100, 0.5)
        candidate = engine.run(multiply(4.0), data, RATE, 0, 100, {})
        self.assertEqual(len(np.unique(np.abs(candidate))), 1)
        self.assertAlmostEqual(engine.peak(candidate), engine.PEAK_LIMIT, places=6)

    def test_audio_already_above_limit_is_kept_when_effect_does_not_raise_peak(self):
        data = frames(100, 0.99)
        candidate = engine.run(multiply(0.5), data, RATE, 40, 60, {})
        np.testing.assert_array_equal(candidate[:40], data[:40])
        np.testing.assert_array_equal(candidate[60:], data[60:])

    def test_audio_already_above_limit_is_normalized_when_effect_raises_peak(self):
        data = frames(100, 0.99)
        candidate = engine.run(multiply(1.5), data, RATE, 40, 60, {})
        self.assertAlmostEqual(engine.peak(candidate), engine.PEAK_LIMIT, places=6)

    def test_input_is_not_changed_by_normalization(self):
        data = frames(100, 0.5)
        original = data.copy()
        engine.run(multiply(3.0), data, RATE, 0, 100, {})
        np.testing.assert_array_equal(data, original)

    def test_silence_is_accepted(self):
        data = frames(100, 0.0)
        candidate = engine.run(multiply(2.0), data, RATE, 0, 100, {})
        self.assertEqual(engine.peak(candidate), 0.0)

    def test_invalid_candidate_is_refused(self):
        candidate = frames(10, 0.5)
        candidate[3, 0] = np.inf
        with self.assertRaises(EffectError):
            engine.protect(candidate, 0.5)


if __name__ == "__main__":
    unittest.main()
