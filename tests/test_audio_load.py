import os
import random
import shutil
import tempfile
import unittest
from itertools import chain, repeat
from pathlib import Path
from unittest import mock

import av
import numpy as np
import soundfile as sf

from src.models.audio_player import (CORRUPTED_MESSAGE, DECODE_TIME_LIMIT_SECONDS, AudioLoadError,
                                     load_audio, memory_limit_bytes)
from src.view.file_dialog import audio_wildcard

DURATION_SECONDS = 1.0
DURATION_TOLERANCE = 0.05
TONE_HZ = 440
TONE_LEVEL = 0.2
AAC_FRAME_SIZE = 1024


def tone(rate: int, channels: int) -> np.ndarray:
    t = np.arange(int(rate * DURATION_SECONDS)) / rate
    wave = (TONE_LEVEL * np.sin(2 * np.pi * TONE_HZ * t)).astype(np.float32)
    if channels == 1:
        return wave
    return np.column_stack([wave] * channels)


def write_m4a(path: Path, rate: int) -> None:
    samples = np.ascontiguousarray(tone(rate, 2).T)
    with av.open(str(path), mode="w", format="ipod") as container:
        stream = container.add_stream("aac", rate=rate, layout="stereo")
        for start in range(0, samples.shape[1], AAC_FRAME_SIZE):
            chunk = np.ascontiguousarray(samples[:, start:start + AAC_FRAME_SIZE])
            frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout="stereo")
            frame.sample_rate = rate
            frame.pts = start
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)


class ValidFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._folder = tempfile.TemporaryDirectory()
        cls.folder = Path(cls._folder.name)
        sf.write(cls.folder / "wav_mono.wav", tone(44100, 1), 44100)
        sf.write(cls.folder / "wav_estereo.wav", tone(48000, 2), 48000)
        sf.write(cls.folder / "mp3_estereo.mp3", tone(44100, 2), 44100,
                 format="MP3", subtype="MPEG_LAYER_III")
        write_m4a(cls.folder / "m4a_aac.m4a", 44100)
        sf.write(cls.folder / "ogg_vorbis.ogg", tone(44100, 2), 44100,
                 format="OGG", subtype="VORBIS")
        sf.write(cls.folder / "ogg_opus.ogg", tone(48000, 2), 48000,
                 format="OGG", subtype="OPUS")
        shutil.copy(cls.folder / "wav_mono.wav", cls.folder / "maiusculo.WAV")

    @classmethod
    def tearDownClass(cls):
        cls._folder.cleanup()

    def assert_loaded(self, name: str, expected_rate: int, rate: int | None = None) -> None:
        data, loaded_rate = load_audio(self.folder / name, rate=rate)
        self.assertEqual(loaded_rate, expected_rate)
        self.assertEqual(data.dtype, np.float32)
        self.assertEqual(data.ndim, 2)
        self.assertEqual(data.shape[1], 2)
        self.assertTrue(data.flags["C_CONTIGUOUS"])
        self.assertAlmostEqual(len(data) / loaded_rate, DURATION_SECONDS, delta=DURATION_TOLERANCE)

    def test_ct01_wav_mono_is_loaded_as_stereo(self):
        self.assert_loaded("wav_mono.wav", 44100)

    def test_ct01_wav_stereo_is_loaded(self):
        self.assert_loaded("wav_estereo.wav", 48000)

    def test_ct01_mp3_is_loaded(self):
        self.assert_loaded("mp3_estereo.mp3", 44100)

    def test_ct01_m4a_is_loaded(self):
        self.assert_loaded("m4a_aac.m4a", 44100)

    def test_ct01_ogg_vorbis_is_loaded(self):
        self.assert_loaded("ogg_vorbis.ogg", 44100)

    def test_ct01_ogg_opus_is_loaded(self):
        self.assert_loaded("ogg_opus.ogg", 48000)

    def test_ct01_uppercase_extension_is_accepted(self):
        self.assert_loaded("maiusculo.WAV", 44100)

    def test_ct01_audio_is_converted_to_requested_rate(self):
        for name in ("wav_mono.wav", "wav_estereo.wav", "mp3_estereo.mp3",
                     "m4a_aac.m4a", "ogg_vorbis.ogg", "ogg_opus.ogg"):
            for rate in (44100, 48000):
                with self.subTest(name=name, rate=rate):
                    self.assert_loaded(name, rate, rate)


class DeclaredDuration:
    def __init__(self, container, duration: int) -> None:
        self._container = container
        self.duration = duration

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        self._container.close()

    def __getattr__(self, name: str):
        return getattr(self._container, name)


class LargeFileTests(unittest.TestCase):
    MEMORY_MESSAGE = "O arquivo é grande demais para o limite de memória configurado."
    TIME_MESSAGE = "A leitura do arquivo demorou demais e foi cancelada."
    SMALL_MEMORY_MB = 1
    LONG_TONE_REPEAT = 4

    @classmethod
    def setUpClass(cls):
        cls._folder = tempfile.TemporaryDirectory()
        cls.path = Path(cls._folder.name) / "quatro_segundos.wav"
        sf.write(cls.path, np.tile(tone(44100, 2), (cls.LONG_TONE_REPEAT, 1)), 44100)

    @classmethod
    def tearDownClass(cls):
        cls._folder.cleanup()

    def test_ct03_automatic_memory_uses_default_limit(self):
        self.assertEqual(memory_limit_bytes(0), 1073741824)

    def test_ct03_negative_memory_uses_default_limit(self):
        self.assertEqual(memory_limit_bytes(-1), 1073741824)

    def test_ct03_positive_memory_is_converted_to_bytes(self):
        for memory_mb, expected in ((1, 1048576), (512, 536870912), (2048, 2147483648)):
            with self.subTest(memory_mb=memory_mb):
                self.assertEqual(memory_limit_bytes(memory_mb), expected)

    def test_ct03_declared_duration_above_memory_limit_is_refused(self):
        with mock.patch("av.AudioResampler", wraps=av.AudioResampler) as resampler:
            with self.assertRaises(AudioLoadError) as context:
                load_audio(self.path, self.SMALL_MEMORY_MB)
        self.assertEqual(str(context.exception), self.MEMORY_MESSAGE)
        resampler.assert_not_called()

    def test_ct03_decoded_size_above_memory_limit_is_refused(self):
        real_open = av.open
        one_second = av.time_base

        def open_with_short_duration(*args, **kwargs):
            return DeclaredDuration(real_open(*args, **kwargs), one_second)

        with mock.patch("av.open", side_effect=open_with_short_duration), \
                mock.patch("av.AudioResampler", wraps=av.AudioResampler) as resampler:
            with self.assertRaises(AudioLoadError) as context:
                load_audio(self.path, self.SMALL_MEMORY_MB)
        self.assertEqual(str(context.exception), self.MEMORY_MESSAGE)
        resampler.assert_called_once()

    def test_ct03_decoding_over_time_limit_is_cancelled(self):
        clock = chain([0.0], repeat(DECODE_TIME_LIMIT_SECONDS + 1.0))
        with mock.patch("src.models.audio_player.time") as fake_time:
            fake_time.monotonic.side_effect = clock
            with self.assertRaises(AudioLoadError) as context:
                load_audio(self.path)
        self.assertEqual(str(context.exception), self.TIME_MESSAGE)
        self.assertEqual(fake_time.monotonic.call_count, 2)


@unittest.skipUnless(os.environ.get("SOUND_MINE_LONG_TESTS") == "1",
                     "teste longo: defina SOUND_MINE_LONG_TESTS=1 para executar")
class LongFileTests(unittest.TestCase):
    LONG_DURATION_SECONDS = 30 * 60
    LONG_TOLERANCE = 0.1
    SOURCE_RATE = 44100
    TARGET_RATE = 48000

    @classmethod
    def setUpClass(cls):
        cls._folder = tempfile.TemporaryDirectory()
        cls.path = Path(cls._folder.name) / "trinta_minutos.ogg"
        block = tone(cls.SOURCE_RATE, 2)
        with sf.SoundFile(cls.path, "w", cls.SOURCE_RATE, 2, format="OGG", subtype="VORBIS") as file:
            for _ in range(int(cls.LONG_DURATION_SECONDS / DURATION_SECONDS)):
                file.write(block)

    @classmethod
    def tearDownClass(cls):
        cls._folder.cleanup()

    def test_ct03_thirty_minute_file_is_loaded(self):
        data, rate = load_audio(self.path, 0, self.TARGET_RATE)
        self.assertEqual(rate, self.TARGET_RATE)
        self.assertEqual(data.dtype, np.float32)
        self.assertEqual(data.ndim, 2)
        self.assertEqual(data.shape[1], 2)
        self.assertTrue(data.flags["C_CONTIGUOUS"])
        self.assertAlmostEqual(len(data) / rate, self.LONG_DURATION_SECONDS, delta=self.LONG_TOLERANCE)
        self.assertLessEqual(data.nbytes, memory_limit_bytes(0))


class UnsupportedFormatTests(unittest.TestCase):
    SUPPORTED_PATTERNS = ["*.wav", "*.mp3", "*.ogg", "*.m4a"]
    UNSUPPORTED_MESSAGE = "Formato inválido ou não suportado."

    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.folder = Path(self._folder.name)

    def tearDown(self):
        self._folder.cleanup()

    def test_ct02_wildcard_lists_only_supported_extensions(self):
        description, patterns = audio_wildcard().split("|")
        self.assertEqual(sorted(patterns.split(";")), sorted(self.SUPPORTED_PATTERNS))
        self.assertIn(f"({patterns})", description)
        for extension in ("flac", "txt"):
            with self.subTest(extension=extension):
                self.assertNotIn(extension, audio_wildcard().lower())

    def test_ct02_unsupported_extension_is_refused(self):
        sf.write(self.folder / "audio.flac", tone(44100, 1), 44100, format="FLAC")
        (self.folder / "texto.txt").write_text("isto não é um áudio", encoding="utf-8")
        for name in ("audio.flac", "texto.txt"):
            with self.subTest(name=name):
                with self.assertRaises(AudioLoadError) as context:
                    load_audio(self.folder / name)
                self.assertEqual(str(context.exception), self.UNSUPPORTED_MESSAGE)


class RenamedFileTests(unittest.TestCase):
    MISMATCH_MESSAGE = "O conteúdo do arquivo não corresponde ao formato indicado."
    EXTENSIONS = (".wav", ".mp3", ".ogg", ".m4a")

    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.folder = Path(self._folder.name)

    def tearDown(self):
        self._folder.cleanup()

    def test_ct05_text_renamed_to_audio_extension_is_refused(self):
        for extension in self.EXTENSIONS:
            with self.subTest(extension=extension):
                path = self.folder / f"texto{extension}"
                path.write_text("isto não é um áudio", encoding="utf-8")
                self.assertGreater(path.stat().st_size, 0)
                with self.assertLogs("src.models.audio_player", "WARNING"):
                    with self.assertRaises(AudioLoadError) as context:
                        load_audio(path)
                self.assertEqual(str(context.exception), CORRUPTED_MESSAGE)

    def test_ct05_audio_renamed_to_other_extension_is_refused(self):
        sf.write(self.folder / "original.wav", tone(44100, 2), 44100)
        sf.write(self.folder / "original.mp3", tone(44100, 2), 44100,
                 format="MP3", subtype="MPEG_LAYER_III")
        sf.write(self.folder / "original.ogg", tone(44100, 2), 44100,
                 format="OGG", subtype="VORBIS")
        write_m4a(self.folder / "original.m4a", 44100)
        for source in self.EXTENSIONS:
            original = self.folder / f"original{source}"
            load_audio(original)
            for target in self.EXTENSIONS:
                if target == source:
                    continue
                with self.subTest(content=source, extension=target):
                    renamed = self.folder / f"{source[1:]}_como{target}"
                    shutil.copy(original, renamed)
                    with self.assertRaises(AudioLoadError) as context:
                        load_audio(renamed)
                    self.assertEqual(str(context.exception), self.MISMATCH_MESSAGE)


class CorruptedFileTests(unittest.TestCase):
    EXTENSIONS = (".wav", ".mp3", ".ogg", ".m4a")
    RANDOM_SEED = 20261107
    RANDOM_SIZE = 4096
    ID3_HEADER = b"ID3\x04\x00\x00\x00\x00\x00\x0a" + bytes(10)

    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.folder = Path(self._folder.name)

    def tearDown(self):
        self._folder.cleanup()

    def assert_corrupted_is_refused(self, name: str, content: bytes) -> None:
        for extension in self.EXTENSIONS:
            with self.subTest(extension=extension):
                path = self.folder / f"{name}{extension}"
                path.write_bytes(content)
                self.assertGreater(path.stat().st_size, 0)
                with self.assertLogs("src.models.audio_player", "WARNING"):
                    with self.assertRaises(AudioLoadError) as context:
                        load_audio(path)
                self.assertEqual(str(context.exception), CORRUPTED_MESSAGE)

    def test_ct04_random_bytes_are_refused(self):
        content = random.Random(self.RANDOM_SEED).randbytes(self.RANDOM_SIZE)
        self.assert_corrupted_is_refused("aleatorio", content)

    def test_ct04_id3_header_with_invalid_data_is_refused(self):
        content = self.ID3_HEADER + bytes(range(256)) * 20
        self.assert_corrupted_is_refused("id3_invalido", content)


class PermissionTests(unittest.TestCase):
    FILE_NAME = "bloqueado_teste.wav"
    PERMISSION_MESSAGE = "Sem permissão para ler o arquivo, ou o arquivo está em uso por outro programa."

    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.folder = Path(self._folder.name)
        self.path = self.folder / self.FILE_NAME
        self.path.write_bytes(b"RIFF" + bytes(64))
        denied = av.error.PermissionError(13, "Permission denied", str(self.path))
        self._open = mock.patch("av.open", side_effect=denied)
        self._open.start()

    def tearDown(self):
        self._open.stop()
        self._folder.cleanup()

    def load_locked(self) -> tuple[str, list[str]]:
        with self.assertLogs("src.models.audio_player", "WARNING") as logs:
            with self.assertRaises(AudioLoadError) as context:
                load_audio(self.path)
        return str(context.exception), logs.output

    def test_locked_file_reports_permission(self):
        message, _ = self.load_locked()
        self.assertEqual(message, self.PERMISSION_MESSAGE)

    def test_locked_file_is_not_reported_as_corrupted(self):
        message, _ = self.load_locked()
        self.assertNotEqual(message, CORRUPTED_MESSAGE)

    def test_locked_file_log_has_no_file_name(self):
        _, output = self.load_locked()
        text = "\n".join(output)
        self.assertIn(".wav", text)
        self.assertIn("errno 13", text)
        self.assertNotIn(self.FILE_NAME, text)
        self.assertNotIn(str(self.folder), text)


class EmptyFileTests(unittest.TestCase):
    def setUp(self):
        self._folder = tempfile.TemporaryDirectory()
        self.folder = Path(self._folder.name)

    def tearDown(self):
        self._folder.cleanup()

    def assert_empty_is_refused(self, extension: str) -> None:
        path = self.folder / f"vazio{extension}"
        path.write_bytes(b"")
        with self.assertRaises(AudioLoadError) as context:
            load_audio(path)
        self.assertEqual(str(context.exception), CORRUPTED_MESSAGE)

    def test_ct06_empty_wav_is_refused(self):
        self.assert_empty_is_refused(".wav")

    def test_ct06_empty_mp3_is_refused(self):
        self.assert_empty_is_refused(".mp3")

    def test_ct06_empty_ogg_is_refused(self):
        self.assert_empty_is_refused(".ogg")

    def test_ct06_empty_m4a_is_refused(self):
        self.assert_empty_is_refused(".m4a")


if __name__ == "__main__":
    unittest.main()
