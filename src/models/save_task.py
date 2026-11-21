import threading
import time
from collections.abc import Callable

from src.models.audio_save import SaveCanceled

PROGRESS_AFTER_SECONDS = 2.0


class SaveTask:
    def __init__(self, work: Callable[[Callable[[float], None]], object],
                 on_finish: Callable[[object, BaseException | None], None],
                 schedule: Callable[[Callable[[], None]], None],
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._work = work
        self._on_finish = on_finish
        self._schedule = schedule
        self._clock = clock
        self._cancel = threading.Event()
        self._lock = threading.Lock()
        self._progress = 0.0
        self._started: float | None = None
        self._running = False

    @property
    def progress(self) -> float:
        with self._lock:
            return self._progress

    @property
    def elapsed(self) -> float:
        if self._started is None:
            return 0.0
        return self._clock() - self._started

    @property
    def running(self) -> bool:
        return self._running

    @property
    def canceling(self) -> bool:
        return self._cancel.is_set()

    @property
    def shows_progress(self) -> bool:
        return self._running and self.elapsed >= PROGRESS_AFTER_SECONDS

    def start(self) -> None:
        if self._started is not None:
            return
        self._started = self._clock()
        self._running = True
        threading.Thread(target=self._run, name="sound-mine-save", daemon=True).start()

    def cancel(self) -> None:
        if self._running:
            self._cancel.set()

    def _report(self, value: float) -> None:
        if self._cancel.is_set():
            raise SaveCanceled()
        with self._lock:
            self._progress = min(max(value, 0.0), 1.0)

    def _run(self) -> None:
        result = None
        error = None
        try:
            result = self._work(self._report)
        except BaseException as caught:
            error = caught
        self._schedule(lambda: self._finish(result, error))

    def _finish(self, result: object, error: BaseException | None) -> None:
        self._running = False
        self._on_finish(result, error)
