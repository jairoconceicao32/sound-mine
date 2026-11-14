import unittest

import numpy as np

from src.view.interface_sounds import SOUND_NAMES, InterfaceSounds


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


class InterfaceSoundsEnabledTests(unittest.TestCase):
    def setUp(self):
        self.sounds = InterfaceSounds()
        self.sounds._sounds = {name: np.ones((10, 2), dtype=np.float32) for name in SOUND_NAMES}

    def played(self, name: str) -> bool:
        self.sounds.stop()
        self.sounds.play(name)
        return self.sounds._buffer is not None

    def test_every_sound_plays_when_enabled(self):
        for name in SOUND_NAMES:
            with self.subTest(name=name):
                self.assertTrue(self.played(name))

    def test_disabled_sounds_keep_startup_and_close(self):
        self.sounds.enabled = False
        for name in SOUND_NAMES:
            with self.subTest(name=name):
                self.assertEqual(self.played(name), name in ("startup", "close"))


if __name__ == "__main__":
    unittest.main()
