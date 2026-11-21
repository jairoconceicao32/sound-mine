import unittest

from src.models.save_feedback import (
    BEEP_INTERVAL_SECONDS,
    HIGH_PITCH,
    LOW_PITCH,
    SaveFeedback,
    pitch,
    progress_text,
)


class SaveFeedbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.beeps: list[float] = []
        self.spoken: list[str] = []
        self.confirmed = 0
        self.feedback = SaveFeedback(self.beeps.append, self.spoken.append, self.confirm)

    def confirm(self) -> None:
        self.confirmed += 1

    def test_pitch_goes_from_low_to_high(self):
        self.assertAlmostEqual(pitch(0.0), LOW_PITCH)
        self.assertAlmostEqual(pitch(1.0), HIGH_PITCH)
        self.assertLess(pitch(0.3), pitch(0.6))
        self.assertAlmostEqual(pitch(2.0), HIGH_PITCH)

    def test_nothing_happens_while_inactive(self):
        for second in range(5):
            self.feedback.update(False, second, 0.5)
        self.feedback.finish(True)
        self.assertEqual((self.beeps, self.spoken, self.confirmed), ([], [], 0))

    def test_first_beep_when_activated_then_one_per_interval(self):
        self.feedback.update(True, 2.0, 0.05)
        self.feedback.update(True, 2.5, 0.06)
        self.feedback.update(True, 2.0 + BEEP_INTERVAL_SECONDS, 0.08)
        self.assertEqual(len(self.beeps), 2)

    def test_beeps_get_higher_as_progress_grows(self):
        for second, fraction in enumerate((0.0, 0.2, 0.5, 0.9)):
            self.feedback.update(True, 2.0 + second * BEEP_INTERVAL_SECONDS, fraction)
        self.assertEqual(self.beeps, sorted(self.beeps))
        self.assertLess(self.beeps[0], self.beeps[-1])

    def test_announces_each_ten_percent_once(self):
        for fraction in (0.05, 0.1, 0.12, 0.19, 0.2, 0.35):
            self.feedback.update(True, 2.0, fraction)
        self.assertEqual(self.spoken, [progress_text(0.1), progress_text(0.2), progress_text(0.3)])
        self.assertEqual(progress_text(0.3), "Salvando: 30 por cento.")

    def test_one_hundred_percent_is_left_for_the_completion_message(self):
        self.feedback.update(True, 2.0, 0.95)
        self.feedback.update(True, 3.0, 1.0)
        self.assertEqual(self.spoken, [progress_text(0.9)])

    def test_confirmation_only_after_a_long_successful_save(self):
        self.feedback.update(True, 2.0, 0.5)
        self.feedback.finish(True)
        self.feedback.finish(True)
        self.assertEqual(self.confirmed, 1)

    def test_no_confirmation_for_small_files(self):
        self.feedback.finish(True)
        self.assertEqual(self.confirmed, 0)

    def test_no_confirmation_after_failure_or_cancel(self):
        self.feedback.update(True, 2.0, 0.5)
        self.feedback.finish(False)
        self.assertEqual(self.confirmed, 0)

    def test_beeps_stop_after_finishing(self):
        self.feedback.update(True, 2.0, 0.5)
        self.feedback.finish(True)
        count = len(self.beeps)
        self.feedback.update(True, 10.0, 0.9)
        self.assertEqual(len(self.beeps), count)
        self.assertEqual(self.spoken, [progress_text(0.5)])


if __name__ == "__main__":
    unittest.main()
