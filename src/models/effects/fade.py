from collections.abc import Mapping

import numpy as np

from src.models.effects.contract import SOURCE_ASKED, EffectParameter, EffectSpec
from src.models.effects.errors import EffectError

DURATION = "duracao"
DURATION_MIN = 1
DURATION_MAX = 60
DURATION_DEFAULT = 5
TOO_LONG = ("A duração informada é maior que o trecho disponível.", "Informe uma duração menor.")

DURATION_PARAMETER = EffectParameter(
    name=DURATION,
    label="Duração em segundos",
    minimum=DURATION_MIN,
    maximum=DURATION_MAX,
    default=DURATION_DEFAULT,
    source=SOURCE_ASKED,
)


def _curve(data: np.ndarray, rate: int, parameters: Mapping[str, int], rising: bool) -> np.ndarray:
    frames = parameters[DURATION] * rate
    if frames > len(data):
        raise EffectError(*TOO_LONG)
    start, end = (0.0, 1.0) if rising else (1.0, 0.0)
    return np.linspace(start, end, frames, dtype=np.float32)


def fade_in(data: np.ndarray, rate: int, parameters: Mapping[str, int]) -> np.ndarray:
    curve = _curve(data, rate, parameters, rising=True)
    result = data.copy()
    result[:len(curve)] *= curve[:, np.newaxis]
    return result


FADE_IN = EffectSpec(
    effect_id="fade_in",
    label="Fade in",
    key="I",
    family=None,
    uses_selection=True,
    parameters=(DURATION_PARAMETER,),
    help_text="Aumenta gradativamente o volume a partir do silêncio, no início do áudio ou do trecho selecionado.",
    process=fade_in,
)

