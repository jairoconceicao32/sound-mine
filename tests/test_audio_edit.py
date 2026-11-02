import unittest

import numpy as np

from src.models import audio_edit
from src.models.audio_edit import EditError


def frames(count: int) -> np.ndarray:
    values = np.arange(count, dtype=np.float32)
    return np.column_stack((values, values))


class RemoveBeforeTests(unittest.TestCase):
    def test_removes_everything_before_cursor(self):
        data, cursor = audio_edit.remove_before(frames(10), 4)
        self.assertEqual(data[:, 0].tolist(), [4, 5, 6, 7, 8, 9])
        self.assertEqual(cursor, 0)

    def test_cursor_at_start_is_refused(self):
        with self.assertRaises(EditError):
            audio_edit.remove_before(frames(10), 0)

    def test_cursor_at_end_would_empty_audio(self):
        with self.assertRaises(EditError):
            audio_edit.remove_before(frames(10), 10)


class RemoveAfterTests(unittest.TestCase):
    def test_removes_everything_after_cursor(self):
        data, cursor = audio_edit.remove_after(frames(10), 4)
        self.assertEqual(data[:, 0].tolist(), [0, 1, 2, 3])
        self.assertEqual(cursor, 4)

    def test_cursor_at_end_is_refused(self):
        with self.assertRaises(EditError):
            audio_edit.remove_after(frames(10), 10)

    def test_cursor_at_start_would_empty_audio(self):
        with self.assertRaises(EditError):
            audio_edit.remove_after(frames(10), 0)


class RemoveBetweenTests(unittest.TestCase):
    def test_removes_between_cursor_and_marked_point(self):
        data, cursor = audio_edit.remove_between(frames(10), 2, 6)
        self.assertEqual(data[:, 0].tolist(), [0, 1, 6, 7, 8, 9])
        self.assertEqual(cursor, 2)

    def test_order_of_points_does_not_matter(self):
        data, cursor = audio_edit.remove_between(frames(10), 6, 2)
        self.assertEqual(data[:, 0].tolist(), [0, 1, 6, 7, 8, 9])
        self.assertEqual(cursor, 2)

    def test_missing_marked_point_is_refused(self):
        with self.assertRaises(EditError):
            audio_edit.remove_between(frames(10), 2, None)

    def test_same_point_is_refused(self):
        with self.assertRaises(EditError):
            audio_edit.remove_between(frames(10), 3, 3)

    def test_whole_audio_would_empty_audio(self):
        with self.assertRaises(EditError):
            audio_edit.remove_between(frames(10), 0, 10)


class InvalidCursorTests(unittest.TestCase):
    def test_cursor_outside_audio_is_refused(self):
        for operation in (audio_edit.remove_before, audio_edit.remove_after):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(EditError):
                    operation(frames(10), 11)
        with self.assertRaises(EditError):
            audio_edit.remove_between(frames(10), 2, -1)


class InsertTests(unittest.TestCase):
    def test_inserts_at_position(self):
        other = frames(3) + 100
        data, cursor = audio_edit.insert(frames(5), other, 2)
        self.assertEqual(data[:, 0].tolist(), [0, 1, 100, 101, 102, 2, 3, 4])
        self.assertEqual(cursor, 2)

    def test_positions(self):
        data = frames(10)
        self.assertEqual(audio_edit.insert_position(data, audio_edit.AT_START, 4), 0)
        self.assertEqual(audio_edit.insert_position(data, audio_edit.AT_CURSOR, 4), 4)
        self.assertEqual(audio_edit.insert_position(data, audio_edit.AT_END, 4), 10)

    def test_empty_file_is_refused(self):
        with self.assertRaises(EditError):
            audio_edit.insert(frames(5), frames(0), 2)


class OverlayTests(unittest.TestCase):
    def quiet(self, count: int, value: float) -> np.ndarray:
        return np.full((count, 2), value, dtype=np.float32)

    def test_mixes_with_volumes_only_where_background_exists(self):
        data, cursor = audio_edit.overlay(self.quiet(6, 0.4), self.quiet(2, 0.5), 2, 50, 20)
        self.assertEqual(len(data), 6)
        self.assertEqual(cursor, 2)
        np.testing.assert_allclose(data[:, 0], [0.4, 0.4, 0.3, 0.3, 0.4, 0.4], rtol=1e-6)

    def test_background_longer_than_audio_is_cut(self):
        data, _ = audio_edit.overlay(self.quiet(4, 0.0), self.quiet(10, 0.5), 2, 100, 100)
        self.assertEqual(len(data), 4)
        np.testing.assert_allclose(data[:, 0], [0.0, 0.0, 0.5, 0.5])

    def test_result_is_limited_to_valid_range(self):
        data, _ = audio_edit.overlay(self.quiet(2, 0.9), self.quiet(2, 0.9), 0, 100, 100)
        self.assertTrue(np.all(data <= 1.0))

    def test_original_is_not_changed(self):
        original = self.quiet(4, 0.4)
        audio_edit.overlay(original, self.quiet(2, 0.5), 0, 100, 100)
        np.testing.assert_allclose(original, 0.4)

    def test_background_at_end_finishes_with_audio(self):
        data, other = frames(10), frames(3)
        self.assertEqual(audio_edit.background_start(data, other, audio_edit.AT_END, 0), 7)
        self.assertEqual(audio_edit.background_start(data, frames(20), audio_edit.AT_END, 0), 0)

    def test_invalid_volumes_are_refused(self):
        for volumes in ((101, 30), (100, -1)):
            with self.subTest(volumes=volumes):
                with self.assertRaises(EditError):
                    audio_edit.overlay(frames(5), frames(2), 0, *volumes)

    def test_position_at_end_is_refused(self):
        with self.assertRaises(EditError):
            audio_edit.overlay(frames(5), frames(2), 5, 100, 30)


if __name__ == "__main__":
    unittest.main()
