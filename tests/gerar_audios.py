import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

OUTPUT = Path(__file__).resolve().parent / "audios"
DURATION_SECONDS = 30
MARK_EVERY_SECONDS = 5
START_HZ = 220
END_HZ = 880
SWEEP_LEVEL = 0.15
BEEP_LEVEL = 0.25
BEEP_SECONDS = 0.2
BEEP_HZ = 1760


def build_signal(rate: int, channels: int) -> np.ndarray:
    t = np.arange(rate * DURATION_SECONDS) / rate
    phase = 2 * np.pi * (START_HZ * t + (END_HZ - START_HZ) * t ** 2 / (2 * DURATION_SECONDS))
    signal = SWEEP_LEVEL * np.sin(phase)
    beep_length = int(rate * BEEP_SECONDS)
    for second in range(0, DURATION_SECONDS, MARK_EVERY_SECONDS):
        start = second * rate
        end = start + beep_length
        signal[start:end] += BEEP_LEVEL * np.sin(2 * np.pi * BEEP_HZ * t[start:end])
    signal = signal.astype(np.float32)
    if channels == 1:
        return signal
    return np.column_stack([signal] * channels)


def write_in_blocks(path: Path, data: np.ndarray, rate: int, **options) -> None:
    channels = 1 if data.ndim == 1 else data.shape[1]
    with sf.SoundFile(path, "w", rate, channels, **options) as file:
        for start in range(0, len(data), rate):
            file.write(data[start:start + rate])


def write_m4a(path: Path, rate: int) -> bool:
    try:
        import av
    except ImportError:
        return False
    samples = np.ascontiguousarray(build_signal(rate, 2).T)
    with av.open(str(path), mode="w", format="ipod") as container:
        stream = container.add_stream("aac", rate=rate, layout="stereo")
        frame_size = 1024
        for start in range(0, samples.shape[1], frame_size):
            chunk = np.ascontiguousarray(samples[:, start:start + frame_size])
            frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout="stereo")
            frame.sample_rate = rate
            frame.pts = start
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    return True


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    sf.write(OUTPUT / "wav_mono_44100.wav", build_signal(44100, 1), 44100)
    sf.write(OUTPUT / "wav_estereo_48000.wav", build_signal(48000, 2), 48000)
    sf.write(OUTPUT / "mp3_estereo_44100.mp3", build_signal(44100, 2), 44100,
             format="MP3", subtype="MPEG_LAYER_III")
    write_in_blocks(OUTPUT / "ogg_vorbis_44100.ogg", build_signal(44100, 2), 44100,
                    format="OGG", subtype="VORBIS")
    sf.write(OUTPUT / "ogg_opus_48000.ogg", build_signal(48000, 2), 48000,
             format="OGG", subtype="OPUS")
    m4a_created = write_m4a(OUTPUT / "m4a_aac_44100.m4a", 44100)

    (OUTPUT / "invalido_corrompido.mp3").write_bytes(b"ID3" + bytes(range(256)) * 20)
    shutil.copy(OUTPUT / "wav_mono_44100.wav", OUTPUT / "invalido_wav_renomeado.ogg")
    (OUTPUT / "invalido_vazio.wav").write_bytes(b"")
    (OUTPUT / "invalido_texto.wav").write_text("isto não é um áudio", encoding="utf-8")
    sf.write(OUTPUT / "invalido_extensao.flac", build_signal(44100, 1), 44100, format="FLAC")

    for path in sorted(OUTPUT.iterdir()):
        print(f"{path.name:32} {path.stat().st_size:>9} bytes")
    if not m4a_created:
        print("m4a_aac_44100.m4a não foi gerado: o PyAV (av) ainda não está instalado.")


if __name__ == "__main__":
    main()
