import unittest

import numpy as np

from src.view.interface_sounds import InterfaceSounds


class InterfaceSoundsConversionTests(unittest.TestCase):
    def test_mono_becomes_stereo(self):
        data = np.array([[0.1], [0.2]], dtype=np.float32)
        result = InterfaceSounds._to_stereo(data)
        self.assertEqual(result.shape, (2, 2))
        np.testing.assert_allclose(result[:, 0], result[:, 1])

    def test_extra_channels_are_dropped(self):
        data = np.zeros((4, 6), dtype=np.float32)
        self.assertEqual(InterfaceSounds._to_stereo(data).shape, (4, 2))

    def test_leading_silence_is_removed(self):
        data = np.array([[0.0, 0.0], [0.001, 0.0], [0.5, 0.5], [0.0, 0.0]], dtype=np.float32)
        result = InterfaceSounds._trim_silence(data)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(float(result[0, 0]), 0.5)

    def test_fully_silent_sound_is_kept(self):
        data = np.zeros((10, 2), dtype=np.float32)
        self.assertEqual(len(InterfaceSounds._trim_silence(data)), 10)

    def test_resample_changes_length_by_rate(self):
        data = np.zeros((24000, 2), dtype=np.float32)
        result = InterfaceSounds._resample(data, 24000, 48000)
        self.assertEqual(result.shape, (48000, 2))

    def test_resample_same_rate_keeps_data(self):
        data = np.ones((100, 2), dtype=np.float32)
        self.assertIs(InterfaceSounds._resample(data, 48000, 48000), data)


if __name__ == "__main__":
    unittest.main()
