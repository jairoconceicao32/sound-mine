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
FALLBACK_RATE = 44100


class InterfaceSounds:
    def __init__(self, folder: Path = SOUNDS_DIR) -> None:
        self._sounds: dict[str, np.ndarray] = {}
        self._lock = threading.Lock()
        self._buffer: np.ndarray | None = None
        self._position = 0
        self._stream = None
        self.enabled = True
        try:
            import sounddevice
            import soundfile
        except Exception:
            logger.exception("Não foi possível iniciar os sons de interface.")
            return
        self._stream, rate = self._open_stream(sounddevice)
        if self._stream is None:
            return
        for name in SOUND_NAMES:
            sound = self._load(soundfile, folder / f"{name}.ogg", rate)
            if sound is not None:
                self._sounds[name] = sound

    def play(self, name: str) -> None:
        sound = self._sounds.get(name)
        if sound is None or not self.enabled:
            return
        with self._lock:
            self._buffer = sound
            self._position = 0

    def duration_ms(self, name: str) -> int:
        sound = self._sounds.get(name)
        if sound is None or self._stream is None:
            return 0
        return round(len(sound) / self._stream.samplerate * 1000)

    def stop(self) -> None:
        with self._lock:
            self._buffer = None
            self._position = 0

    def play_and_wait(self, name: str) -> None:
        if name not in self._sounds or not self.enabled:
            return
        self.play(name)
        deadline = time.monotonic() + MAX_WAIT_SECONDS
        while time.monotonic() < deadline:
            with self._lock:
                if self._buffer is None:
                    return
            time.sleep(0.02)

    def close(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            logger.exception("Falha ao fechar a saída de áudio.")
        self._stream = None

    def _callback(self, outdata, frames, time_info, status) -> None:
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

    def _open_stream(self, sounddevice):
        for device, rate, extra in self._candidates(sounddevice):
            try:
                stream = sounddevice.OutputStream(
                    device=device,
                    samplerate=rate,
                    channels=CHANNELS,
                    dtype="float32",
                    latency="low",
                    extra_settings=extra,
                    callback=self._callback,
                )
                stream.start()
                return stream, rate
            except Exception:
                logger.warning("Saída de áudio indisponível: %r", device, exc_info=True)
        logger.error("Nenhuma saída de áudio disponível para os sons de interface.")
        return None, 0

    @staticmethod
    def _candidates(sounddevice) -> list[tuple]:
        candidates = []
        try:
            for api in sounddevice.query_hostapis():
                device = api["default_output_device"]
                if "WASAPI" in api["name"] and device >= 0:
                    rate = int(sounddevice.query_devices(device)["default_samplerate"])
                    candidates.append((device, rate, sounddevice.WasapiSettings()))
        except Exception:
            logger.warning("Não foi possível consultar o WASAPI.", exc_info=True)
        try:
            rate = int(sounddevice.query_devices(kind="output")["default_samplerate"])
        except Exception:
            rate = FALLBACK_RATE
        candidates.append((None, rate, None))
        return candidates

    @classmethod
    def _load(cls, soundfile, path: Path, rate: int) -> np.ndarray | None:
        if not path.is_file():
            logger.warning("Som de interface não encontrado: %s", path)
            return None
        if path.stat().st_size > MAX_FILE_SIZE:
            logger.warning("Som de interface muito grande, ignorado: %s", path)
            return None
        try:
            data, source_rate = soundfile.read(str(path), dtype="float32", always_2d=True)
        except Exception:
            logger.exception("Não foi possível ler o som de interface %s", path)
            return None
        if len(data) == 0:
            logger.warning("Som de interface vazio, ignorado: %s", path)
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
