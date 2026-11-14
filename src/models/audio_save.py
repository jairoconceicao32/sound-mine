import logging
import os
import tempfile
from pathlib import Path

import numpy as np

from src.models.errors import SoundMineError

logger = logging.getLogger(__name__)

SAVE_FORMATS = ("mp3", "m4a", "wav", "ogg")
MONO = "Mono"
BIT_RATE = 192000
BLOCK_SECONDS = 1
MAX_RATES = {"mp3": 48000}
PERMISSION_MESSAGE = "Sem permissão para gravar nessa pasta, ou o arquivo está em uso."
PERMISSION_HINT = "Escolha outra pasta, como Documentos, ou feche o programa que está usando o arquivo."
SAVE_FAILED_MESSAGE = "Não foi possível salvar o arquivo."
SAVE_FAILED_HINT = "Verifique se há espaço livre no disco ou escolha outra pasta."
CODECS = {
    "mp3": ("mp3", "libmp3lame", 1152),
    "m4a": ("ipod", "aac", 1024),
}


class AudioSaveError(SoundMineError):
    pass


def output_rate(file_format: str, requested_rate: int) -> int:
    return min(requested_rate, MAX_RATES.get(file_format, requested_rate))


def convert(data: np.ndarray, rate: int, target_rate: int, mono: bool) -> np.ndarray:
    import av
    layout = "mono" if mono else "stereo"
    resampler = av.AudioResampler(format="flt", layout=layout, rate=target_rate)
    source = np.ascontiguousarray(data, dtype=np.float32)
    blocks = []
    step = rate * BLOCK_SECONDS
    for start in range(0, len(source), step):
        chunk = source[start:start + step]
        frame = av.AudioFrame.from_ndarray(chunk.reshape(1, -1), format="flt", layout="stereo")
        frame.sample_rate = rate
        blocks.extend(out.to_ndarray().reshape(-1, 1 if mono else 2) for out in resampler.resample(frame))
    blocks.extend(out.to_ndarray().reshape(-1, 1 if mono else 2) for out in resampler.resample(None))
    if not blocks:
        raise AudioSaveError("Não há áudio para salvar.")
    return np.clip(np.concatenate(blocks), -1.0, 1.0)


def save_audio(data: np.ndarray, rate: int, path: Path, file_format: str,
               channel: str, sample_rate: int) -> int:
    if file_format not in SAVE_FORMATS:
        raise AudioSaveError("O formato de gravação configurado não é válido.",
                             "Escolha um formato em Configurações, guia Geral.")
    if path.suffix.lower() != f".{file_format}":
        raise AudioSaveError(
            f"O arquivo será salvo no formato {file_format.upper()}, definido nas configurações.",
            f"Use a extensão .{file_format}.",
        )
    if len(data) == 0:
        raise AudioSaveError("Não há áudio para salvar.")
    target_rate = output_rate(file_format, sample_rate)
    mono = channel == MONO

    folder = path.parent
    if not folder.is_dir():
        raise AudioSaveError("A pasta escolhida não existe.", "Escolha outra pasta.")
    try:
        handle, temporary = tempfile.mkstemp(prefix=".sound_mine_", suffix=path.suffix, dir=folder)
    except PermissionError:
        raise AudioSaveError(PERMISSION_MESSAGE, PERMISSION_HINT) from None
    except OSError as error:
        logger.error("Falha ao criar o arquivo temporário de gravação (%s, errno %s).",
                     type(error).__name__, error.errno)
        raise AudioSaveError(SAVE_FAILED_MESSAGE, SAVE_FAILED_HINT) from None
    os.close(handle)
    temporary = Path(temporary)
    try:
        samples = convert(data, rate, target_rate, mono)
        if file_format in CODECS:
            _encode(samples, target_rate, temporary, file_format, mono)
        else:
            _write_soundfile(samples, target_rate, temporary, file_format)
        os.replace(temporary, path)
    except AudioSaveError:
        temporary.unlink(missing_ok=True)
        raise
    except PermissionError:
        temporary.unlink(missing_ok=True)
        raise AudioSaveError(PERMISSION_MESSAGE, PERMISSION_HINT) from None
    except Exception:
        logger.exception("Falha ao salvar o arquivo de áudio (formato %s).", file_format)
        temporary.unlink(missing_ok=True)
        raise AudioSaveError(SAVE_FAILED_MESSAGE, SAVE_FAILED_HINT) from None
    return target_rate


def _encode(samples: np.ndarray, rate: int, path: Path, file_format: str, mono: bool) -> None:
    import av
    container_format, codec, frame_size = CODECS[file_format]
    layout = "mono" if mono else "stereo"
    planar = np.ascontiguousarray(samples.T)
    with av.open(str(path), mode="w", format=container_format) as container:
        stream = container.add_stream(codec, rate=rate, layout=layout)
        stream.bit_rate = BIT_RATE
        for start in range(0, planar.shape[1], frame_size):
            chunk = np.ascontiguousarray(planar[:, start:start + frame_size])
            frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout=layout)
            frame.sample_rate = rate
            frame.pts = start
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)


def _write_soundfile(samples: np.ndarray, rate: int, path: Path, file_format: str) -> None:
    import soundfile
    options = {"format": "WAV", "subtype": "PCM_16"}
    if file_format == "ogg":
        options = {"format": "OGG", "subtype": "VORBIS"}
    with soundfile.SoundFile(str(path), "w", rate, samples.shape[1], **options) as file:
        for start in range(0, len(samples), rate * BLOCK_SECONDS):
            file.write(samples[start:start + rate * BLOCK_SECONDS])
