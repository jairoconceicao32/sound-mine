import unittest

from src.controllers.editor_exit import (
    CANCEL,
    CANCELED_MESSAGE,
    LEAVE_WITHOUT_SAVING,
    NOT_SAVED_MESSAGE,
    SAVE_AND_LEAVE,
    EditorExit,
)


class FakeScreen:
    def __init__(self, confirmation) -> None:
        self.confirmation = confirmation
        self.announced = 0

    def announce(self) -> None:
        self.announced += 1


class EditorExitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.changes = True
        self.save_result = True
        self.events: list[str] = []
        self.screens: list[FakeScreen] = []
        self.editor_exit = EditorExit(
            has_changes=lambda: self.changes,
            save=self.save,
            show=self.show,
            back=lambda message: self.events.append(f"volta: {message}"),
            schedule=lambda action: action(),
        )

    def save(self) -> bool:
        self.events.append("salvar")
        if isinstance(self.save_result, Exception):
            raise self.save_result
        return self.save_result

    def show(self, confirmation) -> FakeScreen:
        screen = FakeScreen(confirmation)
        self.screens.append(screen)
        return screen

    def leave(self, name: str):
        return lambda: self.events.append(f"sair: {name}")

    def choose(self, label: str) -> None:
        confirmation = self.screens[-1].confirmation
        confirmation.action(confirmation.labels.index(label))()

    def test_without_changes_does_not_ask(self):
        self.changes = False
        self.assertFalse(self.editor_exit.request(self.leave("esc")))
        self.assertEqual(self.screens, [])
        self.assertEqual(self.events, [])

    def test_with_changes_shows_three_options(self):
        self.assertTrue(self.editor_exit.request(self.leave("esc")))
        confirmation = self.screens[0].confirmation
        self.assertEqual(confirmation.labels, (SAVE_AND_LEAVE, LEAVE_WITHOUT_SAVING, CANCEL))
        self.assertEqual(confirmation.initial_index, 0)
        self.assertTrue(self.editor_exit.asking)

    def test_save_and_leave_saves_before_leaving(self):
        self.editor_exit.request(self.leave("esc"))
        self.choose(SAVE_AND_LEAVE)
        self.assertEqual(self.events, ["salvar", "sair: esc"])
        self.assertFalse(self.editor_exit.asking)

    def test_save_cancelled_or_failed_stays_in_editor(self):
        self.save_result = False
        self.editor_exit.request(self.leave("esc"))
        self.choose(SAVE_AND_LEAVE)
        self.assertEqual(self.events, ["salvar", f"volta: {NOT_SAVED_MESSAGE}"])
        self.assertFalse(self.editor_exit.asking)

    def test_unexpected_save_error_stays_in_editor(self):
        self.save_result = OSError("disco cheio")
        self.editor_exit.request(self.leave("esc"))
        with self.assertLogs("src.controllers.editor_exit", level="ERROR"):
            self.choose(SAVE_AND_LEAVE)
        self.assertEqual(self.events, ["salvar", f"volta: {NOT_SAVED_MESSAGE}"])

    def test_leave_without_saving_does_not_save(self):
        self.editor_exit.request(self.leave("esc"))
        self.choose(LEAVE_WITHOUT_SAVING)
        self.assertEqual(self.events, ["sair: esc"])

    def test_cancel_option_and_esc_return_to_editor(self):
        for name in ("opção", "esc"):
            with self.subTest(name=name):
                self.events.clear()
                self.editor_exit.request(self.leave("esc"))
                confirmation = self.screens[-1].confirmation
                if name == "opção":
                    self.choose(CANCEL)
                else:
                    confirmation.on_cancel()
                self.assertEqual(self.events, [f"volta: {CANCELED_MESSAGE}"])
                self.assertFalse(self.editor_exit.asking)

    def test_second_request_reuses_open_confirmation_with_new_destination(self):
        self.editor_exit.request(self.leave("esc"))
        self.assertTrue(self.editor_exit.request(self.leave("alt+f4")))
        self.assertEqual(len(self.screens), 1)
        self.assertEqual(self.screens[0].announced, 1)
        self.choose(LEAVE_WITHOUT_SAVING)
        self.assertEqual(self.events, ["sair: alt+f4"])

    def test_asks_again_after_cancel(self):
        self.editor_exit.request(self.leave("esc"))
        self.choose(CANCEL)
        self.assertTrue(self.editor_exit.request(self.leave("esc")))
        self.assertEqual(len(self.screens), 2)


if __name__ == "__main__":
    unittest.main()
