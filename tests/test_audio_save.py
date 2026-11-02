import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.models.audio_player import load_audio
from src.models.audio_save import AudioSaveError, save_audio

RATE = 48000


def tone(seconds: float) -> np.ndarray:
    t = np.arange(int(RATE * seconds)) / RATE
    wave = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    return np.column_stack((wave, wave))


class SaveAudioTests(unittest.TestCase):
    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.folder = Path(self._folder.name)
        self.data = tone(2)

    def tearDown(self):
        self._folder.cleanup()

    def test_every_format_can_be_reopened_with_same_duration(self):
        for file_format in ("mp3", "m4a", "wav", "ogg"):
            with self.subTest(file_format=file_format):
                path = self.folder / f"saida.{file_format}"
                saved_rate = save_audio(self.data, RATE, path, file_format, "Estéreo", 44100)
                self.assertEqual(saved_rate, 44100)
                data, rate = load_audio(path)
                self.assertEqual(rate, 44100)
                self.assertAlmostEqual(len(data) / rate, 2.0, delta=0.05)

    def test_mp3_is_limited_to_48000(self):
        saved_rate = save_audio(self.data, RATE, self.folder / "saida.mp3", "mp3", "Estéreo", 96000)
        self.assertEqual(saved_rate, 48000)

    def test_mono_is_saved_with_one_channel(self):
        import soundfile
        path = self.folder / "saida.wav"
        save_audio(self.data, RATE, path, "wav", "Mono", 48000)
        self.assertEqual(soundfile.info(str(path)).channels, 1)

    def test_extension_must_match_configured_format(self):
        with self.assertRaises(AudioSaveError):
            save_audio(self.data, RATE, self.folder / "saida.wav", "mp3", "Estéreo", 44100)

    def test_missing_folder_is_refused(self):
        with self.assertRaises(AudioSaveError):
            save_audio(self.data, RATE, self.folder / "nao_existe" / "saida.mp3", "mp3", "Estéreo", 44100)

    def test_empty_audio_is_refused(self):
        with self.assertRaises(AudioSaveError):
            save_audio(self.data[:0], RATE, self.folder / "saida.wav", "wav", "Estéreo", 44100)

    def test_existing_file_is_replaced_and_no_temporary_file_is_left(self):
        path = self.folder / "saida.wav"
        path.write_bytes(b"antigo")
        save_audio(self.data, RATE, path, "wav", "Estéreo", 44100)
        self.assertGreater(path.stat().st_size, 100)
        self.assertEqual([item.name for item in self.folder.iterdir()], ["saida.wav"])


if __name__ == "__main__":
    unittest.main()
