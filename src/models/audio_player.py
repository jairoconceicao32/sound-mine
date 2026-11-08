import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

from src.models.audio_edit import EditError
from src.models.audio_save import save_audio

logger = logging.getLogger(__name__)

CHANNELS = 2
VOLUME_MIN = 0
VOLUME_MAX = 100
VOLUME_STEP = 10
BYTES_PER_SAMPLE = 4
DEFAULT_MEMORY_MB = 1024
FALLBACK_RATE = 44100
DECODE_TIME_LIMIT_SECONDS = 60
ACCEPTED_FORMATS = {
    ".wav": "wav",
    ".mp3": "mp3",
    ".ogg": "ogg",
    ".m4a": "m4a",
}
CORRUPTED_MESSAGE = "O arquivo está corrompido ou não é um áudio válido."


class AudioLoadError(Exception):
    pass


def memory_limit_bytes(memory_mb: int) -> int:
    megabytes = memory_mb if memory_mb > 0 else DEFAULT_MEMORY_MB
    return megabytes * 1024 * 1024


def load_audio(path: Path, memory_mb: int = 0, rate: int | None = None,
               time_limit: float = DECODE_TIME_LIMIT_SECONDS) -> tuple[np.ndarray, int]:
    extension = path.suffix.lower()
    if extension not in ACCEPTED_FORMATS:
        raise AudioLoadError("Formato inválido ou não suportado.")
    if not path.is_file():
        raise AudioLoadError("O arquivo não foi encontrado.")
    if path.stat().st_size == 0:
        raise AudioLoadError(CORRUPTED_MESSAGE)

    try:
        import av
    except Exception:
        logger.exception("Biblioteca de leitura de áudio indisponível.")
        raise AudioLoadError("A leitura de arquivos de áudio não está disponível.") from None

    try:
        with av.open(str(path), mode="r") as container:
            return _decode(container, ACCEPTED_FORMATS[extension], memory_limit_bytes(memory_mb),
                           rate, time_limit, av)
    except AudioLoadError:
        raise
    except PermissionError as error:
        logger.warning("Sem permissão para ler o arquivo de áudio (extensão %s, errno %s).",
                       extension, error.errno)
        raise AudioLoadError(
            "Sem permissão para ler o arquivo, ou o arquivo está em uso por outro programa."
        ) from None
    except Exception:
        logger.warning("Falha ao ler o arquivo de áudio: %s", path, exc_info=True)
        raise AudioLoadError(CORRUPTED_MESSAGE) from None


def _decode(container, expected_format: str, limit: int, target_rate: int | None,
            time_limit: float, av) -> tuple[np.ndarray, int]:
    if expected_format not in container.format.name.split(","):
        raise AudioLoadError("O conteúdo do arquivo não corresponde ao formato indicado.")
    if not container.streams.audio:
        raise AudioLoadError("O arquivo não contém áudio.")

    stream = container.streams.audio[0]
    source_rate = stream.codec_context.sample_rate
    if not source_rate or source_rate <= 0:
        raise AudioLoadError(CORRUPTED_MESSAGE)
    rate = target_rate or source_rate

    if container.duration and container.duration > 0:
        estimated_frames = container.duration / av.time_base * rate
        if estimated_frames * CHANNELS * BYTES_PER_SAMPLE > limit:
            raise AudioLoadError("O arquivo é grande demais para o limite de memória configurado.")

    resampler = av.AudioResampler(format="flt", layout="stereo", rate=rate)
    deadline = time.monotonic() + time_limit
    blocks: list[np.ndarray] = []
    total_bytes = 0

    def collect(frames) -> None:
        nonlocal total_bytes
        for frame in frames:
            block = frame.to_ndarray().reshape(-1, CHANNELS)
            blocks.append(block)
            total_bytes += block.nbytes
        if total_bytes > limit:
            raise AudioLoadError("O arquivo é grande demais para o limite de memória configurado.")
        if time.monotonic() > deadline:
            raise AudioLoadError("A leitura do arquivo demorou demais e foi cancelada.")

    for frame in container.decode(stream):
        collect(resampler.resample(frame))
    collect(resampler.resample(None))

    if not blocks:
        raise AudioLoadError(CORRUPTED_MESSAGE)
    data = np.concatenate(blocks)
    if len(data) == 0:
        raise AudioLoadError(CORRUPTED_MESSAGE)
    return np.ascontiguousarray(data, dtype=np.float32), int(rate)


class AudioPlayer:
    def __init__(self, path: Path, memory_mb: int = 0) -> None:
        self.path = path
        self.file_name = path.name
        self.volume = VOLUME_MAX
        self._memory_mb = memory_mb
        self._lock = threading.Lock()
        self._frame = 0
        self._marked: int | None = None
        self._playing = False
        self._data = np.zeros((0, CHANNELS), dtype=np.float32)
        self._rate = 0
        self._stream = self._open_stream(path, memory_mb)
        self._saved = self._data

    @property
    def duration(self) -> float:
        with self._lock:
            return len(self._data) / self._rate

    @property
    def has_changes(self) -> bool:
        with self._lock:
            return self._data is not self._saved

    @property
    def marked(self) -> float | None:
        with self._lock:
            return None if self._marked is None else self._marked / self._rate

    def mark(self) -> float:
        with self._lock:
            self._marked = self._frame
            return self._frame / self._rate

    def edit(self, operation: Callable[[np.ndarray, int, int | None], tuple[np.ndarray, int]]) -> None:
        with self._lock:
            self._playing = False
            data, cursor = operation(self._data, self._frame, self._marked)
            used = self._saved.nbytes
            if not np.may_share_memory(data, self._saved):
                used += data.nbytes
            if used > memory_limit_bytes(self._memory_mb):
                raise EditError("o resultado é grande demais para o limite de memória configurado.")
            self._data = data
            self._frame = cursor
            self._marked = None

    def load_compatible(self, path: Path) -> np.ndarray:
        data, _ = load_audio(path, self._memory_mb, self._rate)
        return data

    def save(self, path: Path, file_format: str, channel: str, sample_rate: int) -> int:
        with self._lock:
            self._playing = False
            data, rate = self._data, self._rate
        saved_rate = save_audio(data, rate, path, file_format, channel, sample_rate)
        with self._lock:
            self._saved = data
            self.path = path
            self.file_name = path.name
        return saved_rate

    def undo(self) -> None:
        with self._lock:
            self._playing = False
            self._data = self._saved
            self._frame = min(self._frame, len(self._data))
            self._marked = None

    @property
    def playing(self) -> bool:
        with self._lock:
            return self._playing

    def position(self) -> float:
        with self._lock:
            return self._frame / self._rate

    def play(self) -> None:
        with self._lock:
            if self._playing:
                return
            if self._frame >= len(self._data):
                self._frame = 0
            self._playing = True
        self._start_stream()

    def pause(self) -> None:
        with self._lock:
            self._playing = False

    def toggle(self) -> bool:
        if self.playing:
            self.pause()
        else:
            self.play()
        return self.playing

    def seek(self, seconds: float) -> float:
        with self._lock:
            target = max(0, min(len(self._data), round(seconds * self._rate)))
            self._frame = target
            return target / self._rate

    def change_volume(self, delta: int) -> int:
        self.volume = max(VOLUME_MIN, min(VOLUME_MAX, self.volume + delta))
        return self.volume

    def close(self) -> None:
        self.pause()
        if self._stream is None:
            return
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            logger.exception("Falha ao fechar a saída de áudio do player.")
        self._stream = None

    def _start_stream(self) -> None:
        if self._stream is not None and not self._stream.active:
            try:
                self._stream.start()
            except Exception:
                logger.exception("Falha ao iniciar a saída de áudio do player.")

    def _callback(self, outdata, frames, time_info, status) -> None:
        with self._lock:
            if not self._playing:
                outdata.fill(0)
                return
            chunk = self._data[self._frame:self._frame + frames]
            self._frame += len(chunk)
            if self._frame >= len(self._data):
                self._playing = False
            gain = self.volume / VOLUME_MAX
        outdata[:len(chunk)] = chunk * gain
        outdata[len(chunk):] = 0

    def _open_stream(self, path: Path, memory_mb: int):
        try:
            import sounddevice
        except Exception:
            logger.exception("Biblioteca de reprodução indisponível.")
            raise AudioLoadError("A reprodução de áudio não está disponível.") from None

        for device, rate, extra in self._candidates(sounddevice):
            if rate != self._rate:
                self._data, self._rate = load_audio(path, memory_mb, rate)
            try:
                stream = sounddevice.OutputStream(
                    device=device,
                    samplerate=self._rate,
                    channels=CHANNELS,
                    dtype="float32",
                    latency="low",
                    extra_settings=extra,
                    callback=self._callback,
                )
                stream.start()
                return stream
            except Exception:
                logger.warning("Saída de áudio indisponível para o player: %r", device, exc_info=True)
        raise AudioLoadError("Nenhuma saída de áudio disponível para reproduzir o arquivo.")

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
