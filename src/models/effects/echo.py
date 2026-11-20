import math
from collections.abc import Mapping

import numpy as np

from src.models.effects.contract import CHANNELS, SOURCE_SETTINGS, EffectParameter, EffectSpec
from src.models.settings import RANGES, Settings

FAMILY = "eco"
DELAY = "echo_delay"
MIX = "echo_percent"
FEEDBACK = 0.5
SILENCE = 0.001

_DEFAULTS = Settings()

PARAMETERS = (
    EffectParameter(DELAY, "Milissegundos para o eco", RANGES[DELAY].minimum, RANGES[DELAY].maximum,
                    _DEFAULTS.echo_delay, SOURCE_SETTINGS),
    EffectParameter(MIX, "Percentual do eco", RANGES[MIX].minimum, RANGES[MIX].maximum,
                    _DEFAULTS.echo_percent, SOURCE_SETTINGS),
)


def repetitions(mix: float, feedback: float) -> int:
    if mix <= SILENCE:
        return 0
    return math.floor(math.log(SILENCE / mix) / math.log(feedback)) + 1


def _echo(data: np.ndarray, rate: int, parameters: Mapping[str, int],
          mix_factor: float, feedback: float) -> np.ndarray:
    delay = max(1, round(parameters[DELAY] * rate / 1000))
    mix = min(1.0, parameters[MIX] / 100 * mix_factor)
    count = repetitions(mix, feedback)
    result = np.zeros((len(data) + count * delay, CHANNELS), dtype=np.float32)
    result[:len(data)] = data
    for index in range(count):
        offset = (index + 1) * delay
        result[offset:offset + len(data)] += data * np.float32(mix * feedback ** index)
    return result


def echo(data: np.ndarray, rate: int, parameters: Mapping[str, int]) -> np.ndarray:
    return _echo(data, rate, parameters, 1.0, FEEDBACK)


ECHO = EffectSpec(
    effect_id="eco",
    label="Eco",
    key="E",
    family=FAMILY,
    uses_selection=True,
    parameters=PARAMETERS,
    help_text="Acrescenta repetições do som, com o intervalo e o percentual definidos em Configurações, "
              "guia Efeitos de áudio.",
    process=echo,
    adds_tail=True,
)

