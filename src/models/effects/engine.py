import logging
from collections.abc import Mapping
from types import MappingProxyType

import numpy as np

from src.models.effects.contract import CHANNELS, SOURCE_FIXED, EffectSpec
from src.models.effects.errors import INTERNAL_ERROR, EffectError

logger = logging.getLogger(__name__)

PEAK_LIMIT = 0.98
PEAK_TOLERANCE = 1e-6
MAX_TAIL_SECONDS = 120


def _is_audio(data: object) -> bool:
    return (isinstance(data, np.ndarray) and data.dtype == np.float32
            and data.ndim == 2 and data.shape[1] == CHANNELS)


def selection(length: int, cursor: int, marked: int | None) -> tuple[int, int]:
    if not 0 <= cursor <= length or (marked is not None and not 0 <= marked <= length):
        raise EffectError(*INTERNAL_ERROR)
    if marked is None or marked == cursor:
        return 0, length
    start, end = sorted((cursor, marked))
    return start, end


def validate_parameters(effect: EffectSpec, values: Mapping[str, object]) -> Mapping[str, int]:
    known = {parameter.name for parameter in effect.parameters}
    unknown = set(values) - known
    if unknown:
        logger.warning("Parâmetros desconhecidos no efeito %s: %s.", effect.effect_id, ", ".join(sorted(unknown)))
        raise EffectError(*INTERNAL_ERROR)
    validated = {}
    for parameter in effect.parameters:
        if parameter.source == SOURCE_FIXED:
            validated[parameter.name] = parameter.default
            continue
        value = values.get(parameter.name)
        if not parameter.accepts(value):
            logger.warning("Parâmetro inválido no efeito %s: %s.", effect.effect_id, parameter.name)
            raise EffectError(*INTERNAL_ERROR)
        validated[parameter.name] = value
    return MappingProxyType(validated)


def peak(data: np.ndarray) -> float:
    return float(np.abs(data).max()) if data.size else 0.0


def protect(candidate: np.ndarray, original_peak: float) -> np.ndarray:
    if not np.isfinite(candidate).all():
        raise EffectError(*INTERNAL_ERROR)
    current = peak(candidate)
    if current > PEAK_LIMIT and current > original_peak:
        candidate *= np.float32(PEAK_LIMIT / current)
        if peak(candidate) > PEAK_LIMIT + PEAK_TOLERANCE:
            raise EffectError(*INTERNAL_ERROR)
    return candidate


def _valid_result(result: object, effect: EffectSpec, length: int, rate: int) -> bool:
    if not _is_audio(result) or not bool(np.isfinite(result).all()):
        return False
    if not effect.adds_tail:
        return len(result) == length
    return length <= len(result) <= length + MAX_TAIL_SECONDS * rate


def run(effect: EffectSpec, data: np.ndarray, rate: int, start: int, end: int,
        values: Mapping[str, object]) -> np.ndarray:
    return apply(effect, data, rate, start, end, values)[0]


def apply(effect: EffectSpec, data: np.ndarray, rate: int, start: int, end: int,
          values: Mapping[str, object]) -> tuple[np.ndarray, int]:
    if not _is_audio(data) or type(rate) is not int or rate <= 0 or not 0 <= start < end <= len(data):
        raise EffectError(*INTERNAL_ERROR)
    parameters = validate_parameters(effect, values)
    chunk = data[start:end].copy()
    chunk.flags.writeable = False
    try:
        result = effect.process(chunk, rate, parameters)
    except EffectError:
        raise
    except Exception:
        logger.exception("Falha no processamento do efeito %s.", effect.effect_id)
        raise EffectError(*INTERNAL_ERROR) from None
    if not _valid_result(result, effect, len(chunk), rate):
        logger.warning("Resultado inválido do efeito %s.", effect.effect_id)
        raise EffectError(*INTERNAL_ERROR)
    tail = len(result) - len(chunk)
    effect_end = end + tail
    candidate = np.zeros((max(len(data), effect_end), CHANNELS), dtype=np.float32)
    candidate[:len(data)] = data
    candidate[start:end] = result[:len(chunk)]
    if tail:
        candidate[end:effect_end] += result[len(chunk):]
    return protect(candidate, peak(data)), effect_end
