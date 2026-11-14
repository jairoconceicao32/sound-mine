import unittest
from pathlib import Path
from unittest import mock

import wx

from src.controllers import editor_menu
from src.controllers.editor_exit import CANCELED_MESSAGE, NOT_SAVED_MESSAGE, QUESTION
from src.models.screen_manager import ScreenManager
from src.view.confirm_screen import ConfirmScreen
from src.view.screen import Screen

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


class FakeSpeaker:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def speak(self, text: str, interrupt: bool = True) -> None:
        self._log.append(f"fala: {text}")


class FakeSounds:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def play(self, name: str) -> None:
        pass

    def play_and_wait(self, name: str) -> None:
        self._log.append(f"som: {name}")

    def close(self) -> None:
        pass


class FakeAnnouncer:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def done(self, message: str) -> None:
        self._log.append(f"concluído: {message}")

    def error(self, message: str, operation: str | None = None, error: BaseException | None = None) -> None:
        self._log.append(f"erro [{operation}]: {message}")


class FakeSettings:
    disable_tips = False


class FakePlayer:
    path = Path("musica.wav")
    file_name = "musica.wav"
    duration = 10.0

    def __init__(self, changes: bool) -> None:
        self.has_changes = changes
        self.closed = False
        self.paused = 0

    def position(self) -> float:
        return 0.0

    def pause(self) -> None:
        self.paused += 1

    def close(self) -> None:
        self.closed = True


class MainMenu(Screen):
    @property
    def title(self) -> str:
        return "Menu principal"


def flush() -> None:
    for _ in range(10):
        wx.SafeYield(None, True)


class ScreenFlowCase(unittest.TestCase):
    def setUp(self) -> None:
        self.log: list[str] = []
        self.frame = wx.Frame(None)
        self.manager = ScreenManager(self.frame, FakeAnnouncer(self.log), FakeSpeaker(self.log),
                                     FakeSounds(self.log), "Sound Mine", FakeSettings())
        self.main_menu = MainMenu(self.manager.parent, self.manager)
        self.manager.push(self.main_menu)

    def tearDown(self) -> None:
        flush()
        if self.frame:
            self.frame.Destroy()
        flush()

    def open(self, changes: bool = True) -> FakePlayer:
        player = FakePlayer(changes)
        editor_menu.open_editor(self.manager, player)
        self.log.clear()
        return player

    def press(self, key_code: int, char: str | None = None) -> None:
        event = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
        event.SetKeyCode(key_code)
        if char is not None:
            event.SetUnicodeKey(ord(char))
        self.manager._on_char_hook(event)
        flush()

    def letter(self, char: str) -> None:
        self.press(ord(char), char)

    def alt_f4(self) -> bool:
        closed = self.frame.Close()
        flush()
        return closed

    def confirmation(self) -> ConfirmScreen:
        screen = self.manager.current
        self.assertIsInstance(screen, ConfirmScreen)
        return screen

    def choose(self, label: str) -> None:
        screen = self.confirmation()
        for _ in range(5):
            if screen.selected == label:
                break
            self.press(wx.WXK_DOWN)
        self.assertEqual(screen.selected, label)
        self.press(wx.WXK_RETURN)

    def program_closed(self) -> bool:
        return "som: close" in self.log


class ExitFlowTests(ScreenFlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.save = mock.patch.object(editor_menu, "save_audio_file", return_value=True)
        self.save_mock = self.save.start()
        self.addCleanup(self.save.stop)

    def test_esc_without_changes_returns_to_main_menu(self):
        player = self.open(changes=False)
        self.press(wx.WXK_ESCAPE)
        self.assertIs(self.manager.current, self.main_menu)
        self.assertTrue(player.closed)

    def test_alt_f4_without_changes_closes_program(self):
        player = self.open(changes=False)
        self.alt_f4()
        self.assertTrue(self.program_closed())
        self.assertTrue(player.closed)

    def test_esc_with_changes_asks_with_three_options(self):
        player = self.open()
        self.press(wx.WXK_ESCAPE)
        screen = self.confirmation()
        self.assertEqual(screen.selected, "Salvar e sair")
        self.assertIn(f"fala: {QUESTION}", self.log)
        self.assertIn("fala: Salvar e sair", self.log)
        self.assertEqual(player.paused, 1)
        self.assertFalse(player.closed)

    def test_alt_f4_with_changes_is_vetoed_and_asks(self):
        player = self.open()
        self.assertFalse(self.alt_f4())
        self.assertTrue(self.frame)
        self.assertFalse(self.program_closed())
        self.confirmation()
        self.assertFalse(player.closed)

    def test_esc_save_and_leave_saves_then_returns_to_main_menu(self):
        player = self.open()
        self.press(wx.WXK_ESCAPE)
        self.choose("Salvar e sair")
        self.save_mock.assert_called_once()
        self.assertIs(self.manager.current, self.main_menu)
        self.assertTrue(player.closed)

    def test_alt_f4_save_and_leave_saves_then_closes_program(self):
        player = self.open()
        self.alt_f4()
        self.choose("Salvar e sair")
        self.save_mock.assert_called_once()
        self.assertTrue(self.program_closed())
        self.assertTrue(player.closed)

    def test_esc_leave_without_saving_returns_to_main_menu(self):
        player = self.open()
        self.press(wx.WXK_ESCAPE)
        self.choose("Sair sem salvar")
        self.save_mock.assert_not_called()
        self.assertIs(self.manager.current, self.main_menu)
        self.assertTrue(player.closed)

    def test_alt_f4_leave_without_saving_closes_program(self):
        player = self.open()
        self.alt_f4()
        self.choose("Sair sem salvar")
        self.save_mock.assert_not_called()
        self.assertTrue(self.program_closed())
        self.assertTrue(player.closed)

    def test_cancel_option_returns_to_editor(self):
        for close in ("esc", "alt+f4"):
            with self.subTest(close=close):
                player = self.open()
                editor = self.manager.current
                self.press(wx.WXK_ESCAPE) if close == "esc" else self.alt_f4()
                self.choose("Cancelar")
                self.assertIs(self.manager.current, editor)
                self.assertIn(f"fala: {CANCELED_MESSAGE}", self.log)
                self.assertFalse(player.closed)
                self.save_mock.assert_not_called()
                self.manager.pop()
                flush()

    def test_esc_on_confirmation_cancels(self):
        player = self.open()
        editor = self.manager.current
        self.press(wx.WXK_ESCAPE)
        self.press(wx.WXK_ESCAPE)
        self.assertIs(self.manager.current, editor)
        self.assertIn(f"fala: {CANCELED_MESSAGE}", self.log)
        self.assertFalse(player.closed)

    def test_failed_save_keeps_editor_open(self):
        for close in ("esc", "alt+f4"):
            with self.subTest(close=close):
                self.save_mock.return_value = False
                player = self.open()
                editor = self.manager.current
                self.press(wx.WXK_ESCAPE) if close == "esc" else self.alt_f4()
                self.choose("Salvar e sair")
                self.assertIs(self.manager.current, editor)
                self.assertIn(f"fala: {NOT_SAVED_MESSAGE}", self.log)
                self.assertFalse(self.program_closed())
                self.assertFalse(player.closed)
                self.manager.pop()
                flush()

    def test_alt_f4_while_confirmation_is_open_does_not_stack(self):
        self.open()
        self.press(wx.WXK_ESCAPE)
        screen = self.confirmation()
        self.log.clear()
        self.assertFalse(self.alt_f4())
        self.assertIs(self.manager.current, screen)
        self.assertIn(f"fala: {QUESTION}", self.log)
        self.choose("Sair sem salvar")
        self.assertTrue(self.program_closed())

    def test_letters_s_and_n_only_select_in_exit_confirmation(self):
        player = self.open()
        self.press(wx.WXK_ESCAPE)
        screen = self.confirmation()
        self.letter("S")
        self.assertEqual(screen.selected, "Sair sem salvar")
        self.letter("S")
        self.assertEqual(screen.selected, "Salvar e sair")
        self.letter("N")
        self.assertEqual(screen.selected, "Salvar e sair")
        self.letter("C")
        self.assertEqual(screen.selected, "Cancelar")
        self.assertIs(self.manager.current, screen)
        self.save_mock.assert_not_called()
        self.assertFalse(player.closed)

    def test_letters_s_and_n_only_select_in_undo_confirmation(self):
        player = self.open()
        self.letter("D")
        screen = self.confirmation()
        self.assertEqual(screen.title, "Desfazer alterações")
        self.assertEqual(screen.selected, "Não")
        self.letter("S")
        self.assertEqual(screen.selected, "Sim")
        self.letter("N")
        self.assertEqual(screen.selected, "Não")
        self.assertIs(self.manager.current, screen)
        self.assertTrue(player.has_changes)

    def test_editor_letter_shortcuts_still_work(self):
        self.open()
        editor = self.manager.current
        self.letter("R")
        self.assertEqual(self.manager.current.title, "Remover")
        self.press(wx.WXK_ESCAPE)
        self.assertIs(self.manager.current, editor)
        self.letter("M")
        self.assertEqual(self.manager.current.title, "Misturar")
        self.press(wx.WXK_ESCAPE)
        self.letter("S")
        self.save_mock.assert_called_once()
        self.assertIs(self.manager.current, editor)


if __name__ == "__main__":
    unittest.main()
