import logging
import threading
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

SOUNDS_DIR = Path(__file__).resolve().parents[2] / "sounds" / "interface"
SOUND_NAMES = ("startup", "close", "navigation", "confirme", "border")
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_WAIT_SECONDS = 3.0
SILENCE_THRESHOLD = 0.01
CHANNELS = 2


class InterfaceSounds:
    def __init__(self, folder: Path = SOUNDS_DIR, outputs=None) -> None:
        self._folder = folder
        self._sounds: dict[str, np.ndarray] = {}
        self._lock = threading.Lock()
        self._buffer: np.ndarray | None = None
        self._position = 0
        self._rate = 0
        self._outputs = outputs
        self.enabled = True
        try:
            import soundfile
            self._soundfile = soundfile
        except Exception:
            logger.exception("Não foi possível iniciar os sons de interface.")
            self._soundfile = None
        if outputs is not None:
            outputs.register(self)

    @property
    def has_output(self) -> bool:
        return self._outputs is not None and self._outputs.has_output(self)

    def prepare_output(self, device) -> int:
        if device.rate != self._rate:
            self._load_all(device.rate)
        return device.rate

    def play(self, name: str) -> None:
        sound = self._sounds.get(name)
        if sound is None or not self.enabled:
            return
        with self._lock:
            self._buffer = sound
            self._position = 0

    def duration_ms(self, name: str) -> int:
        sound = self._sounds.get(name)
        if sound is None or not self._rate:
            return 0
        return round(len(sound) / self._rate * 1000)

    def stop(self) -> None:
        with self._lock:
            self._buffer = None
            self._position = 0

    def play_and_wait(self, name: str) -> None:
        if name not in self._sounds or not self.enabled or not self.has_output:
            return
        self.play(name)
        deadline = time.monotonic() + MAX_WAIT_SECONDS
        while time.monotonic() < deadline:
            with self._lock:
                if self._buffer is None:
                    return
            time.sleep(0.02)

    def close(self) -> None:
        if self._outputs is not None:
            self._outputs.unregister(self)

    def _load_all(self, rate: int) -> None:
        sounds = {}
        if self._soundfile is not None:
            for name in SOUND_NAMES:
                sound = self._load(self._soundfile, self._folder / f"{name}.ogg", rate)
                if sound is not None:
                    sounds[name] = sound
        with self._lock:
            self._sounds = sounds
            self._buffer = None
            self._position = 0
        self._rate = rate

    def audio_callback(self, outdata, frames, time_info, status) -> None:
        with self._lock:
            buffer = self._buffer
            if buffer is None:
                outdata.fill(0)
                return
            chunk = buffer[self._position:self._position + frames]
            self._position += len(chunk)
            if self._position >= len(buffer):
                self._buffer = None
        outdata[:len(chunk)] = chunk
        outdata[len(chunk):] = 0

    @classmethod
    def _load(cls, soundfile, path: Path, rate: int) -> np.ndarray | None:
        if not path.is_file():
            logger.warning("Som de interface não encontrado: %s", path.name)
            return None
        if path.stat().st_size > MAX_FILE_SIZE:
            logger.warning("Som de interface muito grande, ignorado: %s", path.name)
            return None
        try:
            data, source_rate = soundfile.read(str(path), dtype="float32", always_2d=True)
        except Exception:
            logger.exception("Não foi possível ler o som de interface %s", path.name)
            return None
        if len(data) == 0:
            logger.warning("Som de interface vazio, ignorado: %s", path.name)
            return None
        data = cls._to_stereo(data)
        data = cls._trim_silence(data)
        data = cls._resample(data, source_rate, rate)
        return np.ascontiguousarray(data, dtype=np.float32)

    @staticmethod
    def _to_stereo(data: np.ndarray) -> np.ndarray:
        if data.shape[1] == 1:
            return np.repeat(data, CHANNELS, axis=1)
        return data[:, :CHANNELS]

    @staticmethod
    def _trim_silence(data: np.ndarray) -> np.ndarray:
        loud = np.abs(data).max(axis=1) > SILENCE_THRESHOLD
        if not loud.any():
            return data
        return data[int(np.argmax(loud)):]

    @staticmethod
    def _resample(data: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
        if source_rate == target_rate:
            return data
        length = max(1, round(len(data) * target_rate / source_rate))
        old_positions = np.arange(len(data))
        new_positions = np.linspace(0, len(data) - 1, length)
        return np.column_stack(
            [np.interp(new_positions, old_positions, data[:, channel]) for channel in range(data.shape[1])]
        )
