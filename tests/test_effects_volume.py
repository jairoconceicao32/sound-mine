import unittest

import numpy as np

from src.models.effects import volume
from src.models.effects.errors import EffectError
from src.models.effects.volume import UP

RATE = 1000
TRANSITION = round(RATE * volume.TRANSITION_SECONDS)


def frames(count: int, peak: float = 0.4) -> np.ndarray:
    values = np.full(count, peak, dtype=np.float32)
    values[1::2] = -peak
    return np.column_stack((values, values))


def apply(data, levels, direction, start=0, end=None):
    return volume.adjust(data, levels, RATE, start, len(data) if end is None else end, direction)


class WholeAudioTests(unittest.TestCase):
    def setUp(self):
        self.data = frames(200)
        self.levels = volume.original_levels(200)

    def test_increase_goes_to_next_level_without_transitions(self):
        candidate, levels = apply(self.data, self.levels, UP)
        np.testing.assert_allclose(candidate, self.data * 1.25, rtol=1e-6)
        self.assertTrue(np.all(levels == 125))

    def test_scale_goes_up_to_200_and_then_refuses(self):
        data, levels = self.data, self.levels
        for expected in (125, 150, 175, 200):
            data, levels = apply(frames(200, 0.1), levels, UP)
            self.assertTrue(np.all(levels == expected))
        with self.assertRaises(EffectError) as raised:
            apply(frames(200, 0.1), levels, UP)
        self.assertEqual(raised.exception.reason, volume.MAX_MESSAGE)

    def test_inputs_are_not_changed(self):
        data, levels = self.data.copy(), self.levels.copy()
        apply(self.data, self.levels, UP)
        np.testing.assert_array_equal(self.data, data)
        np.testing.assert_array_equal(self.levels, levels)


class ClippingTests(unittest.TestCase):
    def test_increase_that_would_clip_is_refused_with_its_own_message(self):
        data = frames(100, 0.9)
        with self.assertRaises(EffectError) as raised:
            apply(data, volume.original_levels(100), UP)
        self.assertEqual(raised.exception.reason, volume.DISTORTION_MESSAGE)
        self.assertNotEqual(volume.DISTORTION_MESSAGE, volume.MAX_MESSAGE)

    def test_scale_limit_is_checked_before_clipping(self):
        levels = np.full(100, 200, dtype=np.float32)
        with self.assertRaises(EffectError) as raised:
            apply(frames(100, 0.9), levels, UP)
        self.assertEqual(raised.exception.reason, volume.MAX_MESSAGE)

    def test_limit_is_098(self):
        self.assertEqual(volume.CLIP_LIMIT, 0.98)

    def test_increase_up_to_the_limit_is_accepted(self):
        candidate, _ = apply(frames(100, 0.78), volume.original_levels(100), UP)
        self.assertLessEqual(float(np.abs(candidate).max()), volume.CLIP_LIMIT)

    def test_increase_just_above_the_limit_is_refused(self):
        with self.assertRaises(EffectError) as raised:
            apply(frames(100, 0.79), volume.original_levels(100), UP)
        self.assertEqual(raised.exception.reason, volume.DISTORTION_MESSAGE)

class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.data = frames(400, 0.2)
        self.levels = volume.original_levels(400)

    def test_audio_outside_selection_is_preserved(self):
        candidate, levels = apply(self.data, self.levels, UP, 100, 300)
        np.testing.assert_array_equal(candidate[:100], self.data[:100])
        np.testing.assert_array_equal(candidate[300:], self.data[300:])
        self.assertTrue(np.all(levels[:100] == 100))
        self.assertTrue(np.all(levels[300:] == 100))

    def test_selection_has_its_own_level(self):
        data, levels = apply(self.data, self.levels, UP)
        data, levels = apply(data, levels, UP)
        data, levels = apply(data, levels, UP, 100, 300)
        self.assertTrue(np.all(levels[100 + TRANSITION:300 - TRANSITION] == 175))
        self.assertTrue(np.all(levels[:100] == 150))
        np.testing.assert_allclose(data[150:250], self.data[150:250] * 1.75, rtol=1e-5)

    def test_transitions_inside_selection_borders(self):
        _, levels = apply(self.data, self.levels, UP, 100, 300)
        borders = levels[100:100 + TRANSITION]
        self.assertTrue(np.all(np.diff(borders) > 0))
        self.assertTrue(np.all((borders > 100) & (borders < 125)))
        self.assertTrue(np.all(np.diff(levels[300 - TRANSITION:300]) < 0))
        self.assertLess(float(np.abs(np.diff(levels)).max()), 25 / TRANSITION + 1e-3)

    def test_audio_edges_have_no_transition(self):
        _, levels = apply(self.data, self.levels, UP, 0, 200)
        self.assertEqual(levels[0], 125)
        self.assertTrue(np.all(np.diff(levels[200 - TRANSITION:200]) < 0))
        _, levels = apply(self.data, self.levels, UP, 200, 400)
        self.assertEqual(levels[-1], 125)

    def test_short_selection_shortens_transition(self):
        self.assertEqual(volume.transition_frames(RATE, 6), 3)
        self.assertEqual(volume.transition_frames(RATE, 1), 0)
        _, levels = apply(self.data, self.levels, UP, 100, 101)
        self.assertEqual(levels[100], 125)

    def test_increase_levels_by_highest_part(self):
        levels = self.levels.copy()
        levels[200:] = 150
        _, updated = apply(self.data, levels, UP, 150, 250)
        self.assertTrue(np.all(updated[150 + TRANSITION:250 - TRANSITION] == 175))

    def test_part_at_maximum_refuses_increase(self):
        levels = self.levels.copy()
        levels[200:] = 200
        with self.assertRaises(EffectError) as raised:
            apply(self.data, levels, UP, 150, 250)
        self.assertEqual(raised.exception.reason, volume.MAX_MESSAGE)

    def test_change_stays_continuous_over_previous_transition(self):
        data, levels = apply(self.data, self.levels, UP, 200, 400)
        data, levels = apply(data, levels, UP, 100, 300)
        ratio = levels / 100
        np.testing.assert_allclose(data, self.data * ratio[:, np.newaxis], rtol=1e-5)
        self.assertLess(float(np.abs(np.diff(levels)).max()), 50 / TRANSITION + 1e-3)


class InvalidInputTests(unittest.TestCase):
    def test_invalid_inputs_are_refused(self):
        data = frames(10)
        levels = volume.original_levels(10)
        cases = [
            (data.astype(np.float64), levels, RATE, 0, 10, UP),
            (data, levels.astype(np.float64), RATE, 0, 10, UP),
            (data, volume.original_levels(9), RATE, 0, 10, UP),
            (data, np.zeros(10, dtype=np.float32), RATE, 0, 10, UP),
            (data, np.full(10, np.nan, dtype=np.float32), RATE, 0, 10, UP),
            (data, levels, 0, 0, 10, UP),
            (data, levels, RATE, 5, 5, UP),
            (data, levels, RATE, 0, 11, UP),
            (data, levels, RATE, 0, 10, "lado"),
        ]
        for case in cases:
            with self.subTest(case=case[2:]), self.assertRaises(EffectError):
                volume.adjust(*case)


if __name__ == "__main__":
    unittest.main()
