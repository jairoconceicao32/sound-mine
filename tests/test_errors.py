import unittest
from pathlib import Path
from unittest import mock

import wx

from src.controllers import editor_menu, main_menu
from src.controllers.menu_model import Menu, MenuItem
from src.models.audio_edit import EditError
from src.models.audio_player import AudioLoadError
from src.models.audio_save import AudioSaveError
from src.models.errors import (
    ADD_AUDIO,
    ADD_BACKGROUND,
    OPEN_FILE,
    REMOVE,
    RUN_OPTION,
    SAVE,
    UNDO,
    SoundMineError,
    error_title,
)
from src.view.menu_screen import MenuScreen
from tests.test_exit_flow import FakePlayer, ScreenFlowCase, flush

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


class SoundMineErrorTests(unittest.TestCase):
    def test_program_errors_share_the_base_exception(self):
        for error_class in (AudioLoadError, AudioSaveError, EditError):
            with self.subTest(error_class=error_class.__name__):
                self.assertTrue(issubclass(error_class, SoundMineError))

    def test_edit_error_is_still_a_value_error(self):
        self.assertTrue(issubclass(EditError, ValueError))

    def test_text_shown_to_the_user_does_not_change(self):
        for error_class in (AudioLoadError, AudioSaveError, EditError):
            with self.subTest(error_class=error_class.__name__):
                error = error_class("O arquivo não foi encontrado.")
                self.assertEqual(str(error), "O arquivo não foi encontrado.")
                self.assertEqual(error.reason, "O arquivo não foi encontrado.")
                self.assertIsNone(error.hint)

    def test_keeps_optional_hint(self):
        error = AudioSaveError("Não há espaço no disco.", "Escolha outra pasta.")
        self.assertEqual(str(error), "Não há espaço no disco.")
        self.assertEqual(error.hint, "Escolha outra pasta.")


class ErrorTitleTests(unittest.TestCase):
    def test_title_names_the_operation(self):
        self.assertEqual(error_title(SAVE), "Erro ao salvar")
        self.assertEqual(error_title(OPEN_FILE), "Erro ao abrir arquivo")

    def test_title_without_operation(self):
        for operation in (None, "", "  "):
            with self.subTest(operation=operation):
                self.assertEqual(error_title(operation), "Erro")

    def test_title_does_not_include_version(self):
        self.assertNotIn("Sound Mine", error_title(SAVE))


class EditorPlayer(FakePlayer):
    def __init__(self, changes: bool = True) -> None:
        super().__init__(changes)
        self.edit_error: EditError | None = None
        self.load_error: AudioLoadError | None = None
        self.save_error: AudioSaveError | None = None

    def edit(self, operation) -> None:
        if self.edit_error is not None:
            raise self.edit_error

    def load_compatible(self, path: Path):
        if self.load_error is not None:
            raise self.load_error
        return [0.0]

    def save(self, path, file_format, channel, sample_rate) -> int:
        raise self.save_error


class SaveSettings:
    disable_tips = False
    format = "wav"
    sample_rate = "44100"
    channel = "Estéreo"
    memory_mb = 0


class OperationTitleTests(ScreenFlowCase):
    def open_editor(self, changes: bool = True) -> EditorPlayer:
        player = EditorPlayer(changes)
        editor_menu.open_editor(self.manager, player)
        self.log.clear()
        return player

    def errors(self) -> list[str]:
        return [entry for entry in self.log if entry.startswith("erro")]

    def test_remove_reports_remove_operation(self):
        player = self.open_editor()
        player.edit_error = EditError("o cursor está no início do áudio.")
        self.letter("R")
        self.letter("A")
        self.assertEqual(self.errors(), [
            f"erro [{REMOVE}]: A operação não pode ser realizada: o cursor está no início do áudio.",
        ])

    def test_undo_without_changes_reports_undo_operation(self):
        self.open_editor(changes=False)
        self.letter("D")
        self.assertEqual(self.errors(), [
            f"erro [{UNDO}]: A operação não pode ser realizada: não há alterações para desfazer.",
        ])

    def test_failed_load_names_the_mix_operation(self):
        for key, operation in (("A", ADD_AUDIO), ("F", ADD_BACKGROUND)):
            with self.subTest(operation=operation):
                player = self.open_editor()
                player.load_error = AudioLoadError("O arquivo não foi encontrado.")
                with mock.patch.object(editor_menu, "choose_audio_file", return_value=Path("outro.wav")):
                    self.letter("M")
                    self.letter(key)
                    self.letter("I")
                self.assertEqual(self.errors(), [f"erro [{operation}]: O arquivo não foi encontrado."])
                self.manager.pop_through(self.manager._stack[1])
                flush()

    def test_failed_edit_names_the_add_audio_operation(self):
        player = self.open_editor()
        player.edit_error = EditError("o arquivo escolhido não tem áudio.")
        with mock.patch.object(editor_menu, "choose_audio_file", return_value=Path("outro.wav")):
            self.letter("M")
            self.letter("A")
            self.letter("I")
        self.assertEqual(self.errors(), [
            f"erro [{ADD_AUDIO}]: A operação não pode ser realizada: o arquivo escolhido não tem áudio.",
        ])

    def test_failed_save_reports_save_operation(self):
        player = EditorPlayer()
        player.save_error = AudioSaveError("Não foi possível salvar o arquivo.")
        self.manager.settings = SaveSettings()
        with mock.patch.object(editor_menu, "choose_save_file", return_value=Path("saida.wav")):
            saved = editor_menu.save_audio_file(self.manager, player)
        self.assertFalse(saved)
        self.assertEqual(self.errors(), [f"erro [{SAVE}]: Não foi possível salvar o arquivo."])

    def test_failed_open_reports_open_operation(self):
        self.manager.settings = SaveSettings()
        menu = main_menu.build_main_menu(self.manager)
        open_file = menu.items[0].action
        with mock.patch.object(main_menu, "choose_audio_file", return_value=Path("musica.wav")), \
                mock.patch.object(main_menu, "AudioPlayer", side_effect=AudioLoadError("O arquivo não foi encontrado.")):
            open_file()
        self.assertEqual(self.errors(), [f"erro [{OPEN_FILE}]: O arquivo não foi encontrado."])

    def test_unexpected_option_error_reports_run_option(self):
        def broken() -> None:
            raise RuntimeError("falha")

        screen = MenuScreen(self.manager.parent, self.manager, Menu("Teste", [MenuItem("A", "Quebrada", broken)]))
        self.manager.push(screen)
        self.log.clear()
        with self.assertLogs("src.view.menu_screen", level="ERROR"):
            self.press(wx.WXK_RETURN)
        self.assertEqual(self.errors(), [f"erro [{RUN_OPTION}]: Não foi possível executar a opção Quebrada."])


if __name__ == "__main__":
    unittest.main()
