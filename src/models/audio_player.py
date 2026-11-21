import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

from src.models.audio_edit import INTERNAL_ERROR, EditError
from src.models.audio_output import OutputStatus
from src.models.audio_save import Progress, save_audio
from src.models.effects.volume import original_levels
from src.models.errors import MEMORY_HINT, SoundMineError

logger = logging.getLogger(__name__)

CHANNELS = 2
VOLUME_MIN = 0
VOLUME_MAX = 100
VOLUME_STEP = 10
BYTES_PER_SAMPLE = 4
DEFAULT_MEMORY_MB = 1024
DECODE_TIME_LIMIT_SECONDS = 60
ACCEPTED_FORMATS = {
    ".wav": "wav",
    ".mp3": "mp3",
    ".ogg": "ogg",
    ".m4a": "m4a",
}
CORRUPTED_MESSAGE = "O arquivo está corrompido ou não é um áudio válido."
NO_OUTPUT_MESSAGE = "Nenhuma saída de som disponível."
NO_OUTPUT_HINT = "Conecte ou ative um dispositivo de som e tente novamente."
PLAYBACK_MESSAGE = "O som não pôde ser iniciado."
PLAYBACK_HINT = "Verifique se o dispositivo de som está conectado e ativado."
MEMORY_MESSAGE = "O arquivo é grande demais para o limite de memória configurado."
SUBSTITUTION_NONE = "none"
SUBSTITUTION_READY = "ready"
SUBSTITUTION_NOT_LAST = "not_last"
SUBSTITUTION_NO_DATA = "no_data"


class AudioLoadError(SoundMineError):
    pass


class PlaybackError(SoundMineError):
    pass


def memory_limit_bytes(memory_mb: int) -> int:
    megabytes = memory_mb if memory_mb > 0 else DEFAULT_MEMORY_MB
    return megabytes * 1024 * 1024


def load_audio(path: Path, memory_mb: int = 0, rate: int | None = None,
               time_limit: float = DECODE_TIME_LIMIT_SECONDS) -> tuple[np.ndarray, int]:
    extension = path.suffix.lower()
    if extension not in ACCEPTED_FORMATS:
        raise AudioLoadError("O formato do arquivo não é aceito.", "Use arquivos MP3, M4A, WAV ou OGG.")
    if not path.is_file():
        raise AudioLoadError("O arquivo não foi encontrado.", "Ele pode ter sido movido, renomeado ou apagado.")
    if path.stat().st_size == 0:
        raise AudioLoadError(CORRUPTED_MESSAGE)

    try:
        import av
    except Exception:
        logger.exception("Biblioteca de leitura de áudio indisponível.")
        raise AudioLoadError("A leitura de arquivos de áudio não está disponível.",
                             "Instale as dependências com: python -m pip install -r requirements.txt") from None

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
            "O arquivo está em uso por outro programa ou sem permissão de leitura.",
            "Feche o programa que está usando o arquivo e tente novamente.",
        ) from None
    except Exception as error:
        logger.warning("Falha ao ler o arquivo de áudio (%s).", type(error).__name__, exc_info=True)
        raise AudioLoadError(CORRUPTED_MESSAGE) from None


def _decode(container, expected_format: str, limit: int, target_rate: int | None,
            time_limit: float, av) -> tuple[np.ndarray, int]:
    if expected_format not in container.format.name.split(","):
        raise AudioLoadError("O conteúdo do arquivo não corresponde à extensão.",
                             "Ele pode ter sido renomeado com outra extensão.")
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
            raise AudioLoadError(MEMORY_MESSAGE, MEMORY_HINT)

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
            raise AudioLoadError(MEMORY_MESSAGE, MEMORY_HINT)
        if time.monotonic() > deadline:
            raise AudioLoadError("A leitura do arquivo demorou demais e foi cancelada.",
                                 "O arquivo pode estar danificado.")

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
    def __init__(self, path: Path, memory_mb: int, outputs) -> None:
        self.path = path
        self.file_name = path.name
        self.volume = VOLUME_MAX
        self._memory_mb = memory_mb
        self._lock = threading.Lock()
        self._frame = 0
        self._marked: int | None = None
        self._playing = False
        self._outputs = outputs
        self._preview: np.ndarray | None = None
        self._editor_frame = 0
        self._data, self._rate = load_audio(path, memory_mb, outputs.rate())
        self._saved = self._data
        self._levels = original_levels(len(self._data))
        self._saved_levels = self._levels
        self._effects: dict[str, str] = {}
        self._saved_effects = self._effects
        self._last_family: str | None = None
        self._saved_last_family: str | None = None
        self._before_effect: tuple[np.ndarray, np.ndarray, dict[str, str]] | None = None
        if not outputs.register(self):
            outputs.unregister(self)
            raise AudioLoadError(NO_OUTPUT_MESSAGE, NO_OUTPUT_HINT)

    @property
    def rate(self) -> int:
        return self._rate

    @property
    def data(self) -> np.ndarray:
        with self._lock:
            return self._data

    @property
    def cursor_frame(self) -> int:
        with self._lock:
            return self._editor_frame if self._preview is not None else self._frame

    @property
    def marked_frame(self) -> int | None:
        with self._lock:
            return self._marked

    def _audio(self) -> np.ndarray:
        return self._data if self._preview is None else self._preview

    def _memory_in_use(self, extra: np.ndarray) -> int:
        used = self._saved.nbytes + extra.nbytes
        if not np.may_share_memory(self._data, self._saved):
            used += self._data.nbytes
        return used

    @property
    def previewing(self) -> bool:
        with self._lock:
            return self._preview is not None

    def start_preview(self, candidate: np.ndarray, start: int, end: int) -> None:
        with self._lock:
            if self._preview is not None or not 0 <= start < end <= len(candidate):
                raise EditError(*INTERNAL_ERROR)
            if self._memory_in_use(candidate) > memory_limit_bytes(self._memory_mb):
                raise EditError("O resultado ficaria grande demais para o limite de memória.", MEMORY_HINT)
            self._playing = False
            self._editor_frame = self._frame
            self._frame = 0
            self._preview = candidate[start:end]

    def stop_preview(self) -> None:
        with self._lock:
            if self._preview is None:
                return
            self._playing = False
            self._preview = None
            self._frame = self._editor_frame

    @property
    def duration(self) -> float:
        with self._lock:
            return len(self._audio()) / self._rate

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
            if self._preview is not None:
                raise EditError(*INTERNAL_ERROR)
            self._marked = self._frame
            return self._frame / self._rate

    def edit(self, operation: Callable[[np.ndarray, int, int | None], tuple[np.ndarray, int]],
             levels_operation: Callable[[np.ndarray, int, int | None], np.ndarray] | None = None) -> None:
        with self._lock:
            if self._preview is not None:
                raise EditError(*INTERNAL_ERROR)
            self._playing = False
            data, cursor = operation(self._data, self._frame, self._marked)
            if levels_operation is None:
                levels = self._levels
            else:
                levels = levels_operation(self._levels, self._frame, self._marked)
            if not isinstance(levels, np.ndarray) or levels.shape != (len(data),):
                raise EditError(*INTERNAL_ERROR)
            used = self._saved.nbytes + levels.nbytes
            if not np.may_share_memory(data, self._saved):
                used += data.nbytes
            if used > memory_limit_bytes(self._memory_mb):
                raise EditError("O resultado ficaria grande demais para o limite de memória.", MEMORY_HINT)
            self._data = data
            self._levels = levels
            self._frame = cursor
            self._marked = None
            self._last_family = None
            self._before_effect = None

    def apply_effect(self, candidate: np.ndarray, levels: np.ndarray | None = None,
                     family: str | None = None, effect_id: str | None = None,
                     replacing: bool = False) -> None:
        with self._lock:
            if self._preview is not None or (family is None) != (effect_id is None):
                raise EditError(*INTERNAL_ERROR)
            if replacing and (family is None or self._last_family != family or self._before_effect is None):
                raise EditError(*INTERNAL_ERROR)
            levels = self._levels if levels is None else levels
            if not isinstance(levels, np.ndarray) or levels.shape != (len(candidate),):
                raise EditError(*INTERNAL_ERROR)
            used = self._saved.nbytes + levels.nbytes
            if not np.may_share_memory(candidate, self._saved):
                used += candidate.nbytes
            limit = memory_limit_bytes(self._memory_mb)
            if used > limit:
                raise EditError("O resultado ficaria grande demais para o limite de memória.", MEMORY_HINT)
            before = self._before_effect if replacing else None
            if family is not None and not replacing:
                kept = self._data.nbytes + self._levels.nbytes
                if used + kept <= limit:
                    before = (self._data, self._levels, dict(self._effects))
            self._playing = False
            self._data = candidate
            self._levels = levels
            self._frame = min(self._frame, len(candidate))
            self._marked = None
            if family is not None:
                self._effects = {**self._effects, family: effect_id}
            self._last_family = family
            self._before_effect = before

    @property
    def levels(self) -> np.ndarray:
        with self._lock:
            return self._levels

    @property
    def effects(self) -> dict[str, str]:
        with self._lock:
            return dict(self._effects)

    def substitution(self, family: str) -> str:
        with self._lock:
            if family not in self._effects:
                return SUBSTITUTION_NONE
            if self._last_family != family:
                return SUBSTITUTION_NOT_LAST
            if self._before_effect is None:
                return SUBSTITUTION_NO_DATA
            return SUBSTITUTION_READY

    def before_effect(self, family: str) -> tuple[np.ndarray, np.ndarray]:
        with self._lock:
            if self._last_family != family or self._before_effect is None:
                raise EditError(*INTERNAL_ERROR)
            data, levels, _ = self._before_effect
            return data, levels

    def load_compatible(self, path: Path) -> np.ndarray:
        data, _ = load_audio(path, self._memory_mb, self._rate)
        return data

    def save(self, path: Path, file_format: str, channel: str, sample_rate: int,
             progress: Progress = None) -> int:
        with self._lock:
            self._playing = False
            data, rate, levels = self._data, self._rate, self._levels
            effects, last_family = self._effects, self._last_family
        saved_rate = save_audio(data, rate, path, file_format, channel, sample_rate, progress)
        with self._lock:
            self._saved = data
            self._saved_levels = levels
            self._saved_effects = effects
            self._saved_last_family = last_family
            self.path = path
            self.file_name = path.name
        return saved_rate

    def undo(self) -> None:
        with self._lock:
            if self._preview is not None:
                raise EditError(*INTERNAL_ERROR)
            self._playing = False
            self._data = self._saved
            self._levels = self._saved_levels
            self._effects = self._saved_effects
            self._last_family = self._saved_last_family
            self._before_effect = None
            self._frame = min(self._frame, len(self._data))
            self._marked = None

    @property
    def playing(self) -> bool:
        with self._lock:
            return self._playing

    @property
    def has_output(self) -> bool:
        return self._outputs.has_output(self)

    @property
    def waiting(self) -> bool:
        return self.playing and not self.has_output

    def position(self) -> float:
        with self._lock:
            return self._frame / self._rate

    def play(self) -> None:
        with self._lock:
            if self._playing:
                return
            if self._frame >= len(self._audio()):
                self._frame = 0
            self._playing = True
        if self._outputs.ensure(self) is OutputStatus.FAILED:
            with self._lock:
                self._playing = False
            raise PlaybackError(PLAYBACK_MESSAGE, PLAYBACK_HINT)

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
            target = max(0, min(len(self._audio()), round(seconds * self._rate)))
            self._frame = target
            return target / self._rate

    def change_volume(self, delta: int) -> int:
        self.volume = max(VOLUME_MIN, min(VOLUME_MAX, self.volume + delta))
        return self.volume

    def close(self) -> None:
        self.pause()
        self._outputs.unregister(self)

    def prepare_output(self, device) -> int:
        return self._rate

    def audio_callback(self, outdata, frames, time_info, status) -> None:
        with self._lock:
            if not self._playing:
                outdata.fill(0)
                return
            audio = self._audio()
            chunk = audio[self._frame:self._frame + frames]
            self._frame += len(chunk)
            if self._frame >= len(audio):
                self._playing = False
            gain = self.volume / VOLUME_MAX
        outdata[:len(chunk)] = chunk * gain
        outdata[len(chunk):] = 0
