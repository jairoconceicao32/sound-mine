import math
from collections.abc import Mapping
from functools import lru_cache

import numpy as np

from src.models.effects.contract import CHANNELS, SOURCE_SETTINGS, EffectParameter, EffectSpec
from src.models.settings import RANGES, Settings

FAMILY = "reverberacao"
DURATION = "reverb_delay"
MIX = "reverb_percent"
HALL_MIX_FACTOR = 1.2
HALL_DURATION_FACTOR = 3
PRE_DELAY_SHARE = 0.015
PRE_DELAY_MIN_SECONDS = 0.005
PRE_DELAY_MAX_SECONDS = 0.06
DECAY_DB = 60
BLOCK_FRAMES = 1 << 16
TUNING_RATE = 44100
COMB_TUNINGS = (1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617)
ALLPASS_TUNINGS = (556, 441, 341, 225)
STEREO_SPREAD = 23
ALLPASS_FEEDBACK = 0.5
DAMPING = 0.2
FULL_ROOM_SECONDS = 0.5
SMALLEST_ROOM = 0.1
ALIAS_FACTOR = 2
REFERENCE_SECONDS = 1.2

_DEFAULTS = Settings()

PARAMETERS = (
    EffectParameter(DURATION, "Milissegundos para o reverbe", RANGES[DURATION].minimum,
                    RANGES[DURATION].maximum, _DEFAULTS.reverb_delay, SOURCE_SETTINGS),
    EffectParameter(MIX, "Percentual do reverbe", RANGES[MIX].minimum, RANGES[MIX].maximum,
                    _DEFAULTS.reverb_percent, SOURCE_SETTINGS),
)


def pre_delay_frames(rate: int, milliseconds: float) -> int:
    seconds = min(max(milliseconds / 1000 * PRE_DELAY_SHARE, PRE_DELAY_MIN_SECONDS), PRE_DELAY_MAX_SECONDS)
    return round(seconds * rate)


@lru_cache(maxsize=8)
def impulse_response(rate: int, milliseconds: float) -> np.ndarray:
    tail = _tail_response(rate, milliseconds)
    response = np.concatenate((np.zeros((pre_delay_frames(rate, milliseconds), CHANNELS)), tail))
    response.flags.writeable = False
    return response


def room_scale(milliseconds: float) -> float:
    return min(1.0, max(milliseconds / 1000 / FULL_ROOM_SECONDS, SMALLEST_ROOM))


def _delays(tunings: tuple[int, ...], rate: int, scale: float, spread: int) -> list[int]:
    return [max(1, round((tuning + spread) * rate / TUNING_RATE * scale)) for tuning in tunings]


def _freeverb_spectrum(rate: int, milliseconds: float, size: int, spread: int) -> np.ndarray:
    scale = room_scale(milliseconds)
    seconds = milliseconds / 1000
    z = np.exp(-2j * np.pi * np.fft.rfftfreq(size))
    lowpass = (1 - DAMPING) / (1 - DAMPING * z)
    combs = np.zeros_like(z)
    for delay in _delays(COMB_TUNINGS, rate, scale, spread):
        feedback = 10 ** (-DECAY_DB / 20 * delay / (seconds * rate))
        shift = z ** delay
        combs += shift / (1 - feedback * lowpass * shift)
    for delay in _delays(ALLPASS_TUNINGS, rate, scale, spread):
        shift = z ** delay
        combs *= shift / (1 - ALLPASS_FEEDBACK * shift) - 1
    return combs


def _tail_response(rate: int, milliseconds: float) -> np.ndarray:
    length = max(2, round(milliseconds * rate / 1000))
    size = 1 << math.ceil(math.log2(length * ALIAS_FACTOR))
    response = np.empty((length, CHANNELS))
    energy = milliseconds / 1000 / REFERENCE_SECONDS
    for channel, spread in enumerate((0, STEREO_SPREAD)):
        shaped = np.fft.irfft(_freeverb_spectrum(rate, milliseconds, size, spread), size)[:length]
        response[:, channel] = shaped * math.sqrt(energy / float(np.sum(shaped ** 2)))
    return response


def convolve(signal: np.ndarray, response: np.ndarray) -> np.ndarray:
    length = len(signal) + len(response) - 1
    size = 1 << math.ceil(math.log2(BLOCK_FRAMES + len(response) - 1))
    block = size - len(response) + 1
    spectrum = np.fft.rfft(response, size)
    output = np.zeros(length)
    for start in range(0, len(signal), block):
        segment = signal[start:start + block]
        result = np.fft.irfft(np.fft.rfft(segment, size) * spectrum, size)
        used = len(segment) + len(response) - 1
        output[start:start + used] += result[:used]
    return output


def _reverb(data: np.ndarray, rate: int, parameters: Mapping[str, int],
            mix_factor: float, duration_factor: float) -> np.ndarray:
    mix = min(1.0, parameters[MIX] / 100 * mix_factor)
    if mix <= 0:
        return data.copy()
    response = impulse_response(rate, parameters[DURATION] * duration_factor)
    result = np.zeros((len(data) + len(response) - 1, CHANNELS), dtype=np.float32)
    result[:len(data)] = data
    for channel in range(CHANNELS):
        wet = convolve(data[:, channel].astype(np.float64), response[:, channel])
        result[:, channel] += (wet * mix).astype(np.float32)
    return result


def room_reverb(data: np.ndarray, rate: int, parameters: Mapping[str, int]) -> np.ndarray:
    return _reverb(data, rate, parameters, 1.0, 1.0)


def hall_reverb(data: np.ndarray, rate: int, parameters: Mapping[str, int]) -> np.ndarray:
    return _reverb(data, rate, parameters, HALL_MIX_FACTOR, HALL_DURATION_FACTOR)


REVERB = EffectSpec(
    effect_id="reverberacao",
    label="Reverberação",
    key="R",
    family=FAMILY,
    uses_selection=True,
    parameters=PARAMETERS,
    help_text="Acrescenta a ambientação de um salão ou de uma igreja, com o som se propagando em todas as "
              "direções, a partir dos valores definidos em Configurações, guia Efeitos de áudio.",
    process=hall_reverb,
    adds_tail=True,
)

