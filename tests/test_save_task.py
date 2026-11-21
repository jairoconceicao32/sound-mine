import threading
import unittest

from src.models.audio_save import SaveCanceled
from src.models.save_task import PROGRESS_AFTER_SECONDS, SaveTask


class Clock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class SaveTaskTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = Clock()
        self.finished = threading.Event()
        self.results: list = []

    def on_finish(self, result, error) -> None:
        self.results.append((result, error))
        self.finished.set()

    def task(self, work) -> SaveTask:
        return SaveTask(work, self.on_finish, lambda action: action(), self.clock)

    def wait(self) -> None:
        self.assertTrue(self.finished.wait(5))

    def test_result_is_delivered_and_task_stops_running(self):
        task = self.task(lambda progress: 44100)
        task.start()
        self.wait()
        self.assertEqual(self.results, [(44100, None)])
        self.assertFalse(task.running)

    def test_progress_reflects_the_work(self):
        reached = threading.Event()
        release = threading.Event()

        def work(progress):
            progress(0.4)
            reached.set()
            release.wait(5)
            return 1

        task = self.task(work)
        task.start()
        self.assertTrue(reached.wait(5))
        self.assertEqual(task.progress, 0.4)
        self.assertTrue(task.running)
        release.set()
        self.wait()

    def test_progress_is_only_shown_after_the_small_file_limit(self):
        release = threading.Event()
        task = self.task(lambda progress: release.wait(5))
        task.start()
        self.assertFalse(task.shows_progress)
        self.clock.now += PROGRESS_AFTER_SECONDS - 0.1
        self.assertFalse(task.shows_progress)
        self.clock.now += 0.1
        self.assertTrue(task.shows_progress)
        release.set()
        self.wait()
        self.assertFalse(task.shows_progress)

    def test_cancel_interrupts_at_the_next_progress(self):
        started = threading.Event()
        release = threading.Event()

        def work(progress):
            progress(0.1)
            started.set()
            release.wait(5)
            progress(0.2)
            return 1

        task = self.task(work)
        task.start()
        self.assertTrue(started.wait(5))
        task.cancel()
        self.assertTrue(task.canceling)
        release.set()
        self.wait()
        result, error = self.results[0]
        self.assertIsNone(result)
        self.assertIsInstance(error, SaveCanceled)
        self.assertEqual(task.progress, 0.1)

    def test_errors_are_delivered_instead_of_lost_in_the_thread(self):
        def work(progress):
            raise OSError("disco cheio")

        task = self.task(work)
        task.start()
        self.wait()
        result, error = self.results[0]
        self.assertIsNone(result)
        self.assertIsInstance(error, OSError)
        self.assertFalse(task.running)

    def test_cancel_after_finishing_does_nothing(self):
        task = self.task(lambda progress: 1)
        task.start()
        self.wait()
        task.cancel()
        self.assertFalse(task.canceling)

    def test_start_twice_runs_only_once(self):
        calls = []
        task = self.task(lambda progress: calls.append(1))
        task.start()
        task.start()
        self.wait()
        self.assertEqual(calls, [1])


if __name__ == "__main__":
    unittest.main()
