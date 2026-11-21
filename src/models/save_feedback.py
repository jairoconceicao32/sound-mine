from collections.abc import Callable

BEEP_INTERVAL_SECONDS = 1.0
LOW_PITCH = 0.7
HIGH_PITCH = 1.5
ANNOUNCE_STEP = 10


def percent(fraction: float) -> int:
    return int(min(max(fraction, 0.0), 1.0) * 100)


def progress_text(fraction: float) -> str:
    return f"Salvando: {percent(fraction)} por cento."


def pitch(fraction: float) -> float:
    return LOW_PITCH + (HIGH_PITCH - LOW_PITCH) * min(max(fraction, 0.0), 1.0)


class SaveFeedback:
    def __init__(self, beep: Callable[[float], None], announce: Callable[[str], None],
                 confirm: Callable[[], None]) -> None:
        self._beep = beep
        self._announce = announce
        self._confirm = confirm
        self._started = False
        self._finished = False
        self._next_beep = 0.0
        self._announced = 0

    @property
    def started(self) -> bool:
        return self._started

    def update(self, active: bool, elapsed: float, fraction: float) -> None:
        if not active or self._finished:
            return
        if not self._started:
            self._started = True
            self._next_beep = elapsed
        if elapsed >= self._next_beep:
            self._beep(pitch(fraction))
            self._next_beep = elapsed + BEEP_INTERVAL_SECONDS
        step = percent(fraction) // ANNOUNCE_STEP * ANNOUNCE_STEP
        if self._announced < step < 100:
            self._announced = step
            self._announce(progress_text(step / 100))

    def finish(self, saved: bool) -> None:
        if self._finished:
            return
        self._finished = True
        if saved and self._started:
            self._confirm()
