import numpy as np

from src.models.effects.contract import CHANNELS
from src.models.effects.engine import PEAK_LIMIT
from src.models.effects.errors import INTERNAL_ERROR, EffectError

SCALE = (25, 50, 75, 100, 125, 150, 175, 200)
ORIGINAL_LEVEL = 100
UP = "up"
DOWN = "down"
TRANSITION_SECONDS = 0.01
CLIP_LIMIT = PEAK_LIMIT
TOLERANCE = 1e-3
MAX_MESSAGE = "O volume máximo permitido foi atingido."
MIN_MESSAGE = "O volume mínimo permitido foi atingido."
DISTORTION_MESSAGE = "O volume não pode ser aumentado sem causar distorção."


def original_levels(length: int) -> np.ndarray:
    return np.full(length, ORIGINAL_LEVEL, dtype=np.float32)


def target_level(current: np.ndarray, direction: str) -> int:
    if direction == UP:
        highest = float(current.max())
        above = [level for level in SCALE if level > highest + TOLERANCE]
        if not above:
            raise EffectError(MAX_MESSAGE)
        return above[0]
    lowest = float(current.min())
    below = [level for level in SCALE if level < lowest - TOLERANCE]
    if not below:
        raise EffectError(MIN_MESSAGE)
    return below[-1]


def transition_frames(rate: int, length: int) -> int:
    return min(round(rate * TRANSITION_SECONDS), length // 2)


def new_levels(levels: np.ndarray, start: int, end: int, target: int, rate: int) -> np.ndarray:
    section = np.full(end - start, target, dtype=np.float32)
    size = transition_frames(rate, end - start)
    if size > 0 and start > 0:
        section[:size] = np.linspace(levels[start - 1], target, size + 2, dtype=np.float32)[1:-1]
    if size > 0 and end < len(levels):
        section[-size:] = np.linspace(target, levels[end], size + 2, dtype=np.float32)[1:-1]
    updated = levels.copy()
    updated[start:end] = section
    return updated


def _valid_input(data: object, levels: object, rate: object, start: int, end: int, direction: str) -> bool:
    if not (isinstance(data, np.ndarray) and data.dtype == np.float32
            and data.ndim == 2 and data.shape[1] == CHANNELS):
        return False
    if not (isinstance(levels, np.ndarray) and levels.dtype == np.float32
            and levels.shape == (len(data),) and bool(np.isfinite(levels).all())):
        return False
    if len(levels) and (levels.min() < SCALE[0] - TOLERANCE or levels.max() > SCALE[-1] + TOLERANCE):
        return False
    return (type(rate) is int and rate > 0 and 0 <= start < end <= len(data)
            and direction in (UP, DOWN))


def adjust(data: np.ndarray, levels: np.ndarray, rate: int, start: int, end: int,
           direction: str) -> tuple[np.ndarray, np.ndarray]:
    if not _valid_input(data, levels, rate, start, end, direction):
        raise EffectError(*INTERNAL_ERROR)
    target = target_level(levels[start:end], direction)
    updated = new_levels(levels, start, end, target, rate)
    ratio = updated[start:end] / levels[start:end]
    section = data[start:end] * ratio[:, np.newaxis]
    if not np.isfinite(section).all():
        raise EffectError(*INTERNAL_ERROR)
    if direction == UP and float(np.abs(section).max()) > CLIP_LIMIT:
        raise EffectError(DISTORTION_MESSAGE)
    candidate = data.copy()
    candidate[start:end] = section
    return candidate, updated
