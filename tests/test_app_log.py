import logging
import os
import re
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from src.controllers import main_menu
from src.models import app_log
from src.models.app_log import BACKUP_COUNT, MAX_BYTES, operation, sanitize, setup_logging, shutdown_logging
from src.models.audio_output import OutputCoordinator
from src.models.audio_player import AudioLoadError, load_audio
from src.models.audio_save import AudioSaveError, save_audio
from src.models.errors import OPEN_FILE, RUN_OPTION, SAVE
from src.view.announcer import Announcer
from src.view.speaker import Speaker
from tests.test_audio_output import HEADSET, FakeBackend
from tests.test_exit_flow import FakeSpeaker, ScreenFlowCase

VERSION = "Sound Mine teste"

_app = None


def setUpModule() -> None:
    global _app
    import wx
    _app = wx.GetApp() or wx.App(False)
RECORD = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} ", re.MULTILINE)
logger = logging.getLogger("tests.app_log")


class SanitizeTests(unittest.TestCase):
    def test_module_paths_become_relative(self):
        line = f'  File "{app_log.PROJECT_ROOT / "src" / "models" / "audio_player.py"}", line 76'
        self.assertEqual(sanitize(line), r'  File "src\models\audio_player.py", line 76')

    def test_python_installation_is_hidden(self):
        line = f'  File "{Path(sys.base_prefix) / "Lib" / "logging" / "__init__.py"}", line 1'
        self.assertIn(r'"<python>\Lib\logging\__init__.py"', sanitize(line))

    def test_quoted_audio_paths_keep_only_extension(self):
        for text in (r"Permission denied: 'D:\Musicas\Maria voz.mp3'",
                     r"Permission denied: 'D:\\Musicas\\Maria voz.MP3'",
                     'No such file: "\\\\servidor\\pasta\\Maria.wav"'):
            with self.subTest(text=text):
                result = sanitize(text)
                self.assertNotIn("Maria", result)
                self.assertNotIn("Musicas", result)
                self.assertRegex(result, r"<arquivo>\.(mp3|wav)")

    def test_quoted_folder_becomes_generic(self):
        self.assertEqual(sanitize(r"pasta 'D:\Particular\Projetos'"), "pasta '<caminho>'")

    def test_loose_audio_paths_are_hidden(self):
        self.assertEqual(sanitize(r"falha em D:\audio\Maria.ogg agora"), "falha em <arquivo>.ogg agora")

    def test_user_profile_and_user_names_are_hidden(self):
        profile = os.environ.get("USERPROFILE", r"C:\Users\Fulano")
        result = sanitize(f"{profile}\\Documents e C:\\Users\\Outra\\AppData")
        self.assertIn("%USERPROFILE%\\Documents", result)
        self.assertIn("C:\\Users\\<usuário>\\AppData", result)
        self.assertNotIn("Outra", result)
        user = os.environ.get("USERNAME")
        if user:
            self.assertNotIn(user, result)


class LogCase(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.base = Path(folder.name)
        self.program_logs = self.base / "programa" / "logs"
        self.local_logs = self.base / "local" / "Sound Mine" / "logs"
        for patcher in (mock.patch.dict(os.environ, {"LOCALAPPDATA": str(self.base / "local")}),
                        mock.patch.object(app_log, "PROGRAM_LOG_FOLDER", self.program_logs)):
            patcher.start()
            self.addCleanup(patcher.stop)
        setup_logging(VERSION, speech_available=True, console=False)
        self.addCleanup(shutdown_logging)

    @property
    def path(self) -> Path | None:
        return app_log.log_path()

    def text(self) -> str:
        for folder in (self.program_logs, self.local_logs):
            path = folder / "sound_mine.log"
            if path.is_file():
                return path.read_text(encoding="utf-8")
        return ""

    def records(self) -> list[str]:
        return [chunk.strip() for chunk in RECORD.split(self.text())[1:]]

    def audio_file(self, name: str, content: bytes) -> Path:
        folder = self.base / "Pessoal"
        folder.mkdir(exist_ok=True)
        path = folder / name
        path.write_bytes(content)
        return path


class FileLogTests(LogCase):
    def test_nothing_is_created_before_first_record(self):
        self.assertIsNone(self.path)
        self.assertFalse(self.program_logs.exists())
        self.assertFalse(self.local_logs.exists())

    def test_program_folder_is_used_first(self):
        logger.warning("primeiro")
        self.assertEqual(self.path, self.program_logs / "sound_mine.log")
        self.assertTrue(self.path.exists())
        self.assertFalse(self.local_logs.exists())
        self.assertEqual(os.listdir(self.program_logs), ["sound_mine.log"])

    def test_local_app_data_is_used_when_program_folder_is_not_writable(self):
        shutdown_logging()
        self.program_logs.parent.write_text("não é uma pasta")
        setup_logging(VERSION, console=False)
        logger.warning("primeiro")
        self.assertEqual(self.path, self.local_logs / "sound_mine.log")
        self.assertIn("primeiro", self.text())

    def test_rotation_limits(self):
        handler = next(item for item in app_log._handlers if isinstance(item, app_log.SessionFileHandler))
        self.assertEqual(handler.maxBytes, MAX_BYTES)
        self.assertEqual(handler.backupCount, BACKUP_COUNT)

    def test_header_with_environment_is_written_once(self):
        logger.warning("um")
        logger.error("dois")
        text = self.text()
        self.assertEqual(text.count("=== "), 1)
        self.assertIn(VERSION, text.splitlines()[0])
        self.assertIn("Python", text.splitlines()[0])
        self.assertIn("leitor de tela: disponível", text.splitlines()[0])
        self.assertEqual(len(self.records()), 2)

    def test_record_has_level_version_location_and_operation(self):
        with operation(SAVE):
            logger.warning("falha técnica")
        record = self.records()[0]
        self.assertIn("WARNING", record)
        self.assertIn(f"[{VERSION}]", record)
        self.assertIn("test_app_log.test_record_has_level_version_location_and_operation:", record)
        self.assertIn(f"operação={SAVE}", record)
        self.assertIn("falha técnica", record)

    def test_record_outside_operation(self):
        logger.warning("sem operação")
        self.assertIn("operação=-", self.records()[0])

    def test_audio_extension_and_size_are_recorded_without_name(self):
        path = self.audio_file("Maria segredo.MP3", b"x" * 10)
        with operation(OPEN_FILE, path):
            logger.warning("falha")
        record = self.records()[0]
        self.assertIn("arquivo=(.mp3, 10 bytes)", record)
        self.assertNotIn("Maria", record)

    def test_save_records_only_extension(self):
        with operation(SAVE, Path("D:/Pessoal/Maria.wav"), with_size=False):
            logger.warning("falha")
        record = self.records()[0]
        self.assertIn("arquivo=(.wav)", record)
        self.assertNotIn("bytes", record)

    def test_info_records_are_not_written(self):
        logger.info("detalhe")
        self.assertEqual(self.records(), [])


class PrivacyTests(LogCase):
    def assert_private(self, text: str) -> None:
        for forbidden in ("Maria", "Pessoal", str(self.base), os.environ.get("USERNAME") or "Maria"):
            self.assertNotIn(forbidden, text)

    def test_failed_load_records_no_name_or_folder(self):
        path = self.audio_file("Maria segredo.wav", b"isto nao e audio" * 20)
        with operation(OPEN_FILE, path):
            with self.assertRaises(AudioLoadError):
                load_audio(path)
        text = self.text()
        self.assertEqual(len(self.records()), 1)
        self.assertIn("arquivo=(.wav, 320 bytes)", text)
        self.assertIn("Traceback", text)
        self.assert_private(text)

    def test_failed_save_records_no_path(self):
        destination = self.base / "Pessoal"
        destination.mkdir(exist_ok=True)
        target = destination / "Maria.wav"
        error = OSError(28, "No space left on device", str(target))
        with mock.patch("src.models.audio_save._write_soundfile", side_effect=error):
            with operation(SAVE, target, with_size=False):
                with self.assertRaises(AudioSaveError):
                    save_audio(np.zeros((100, 2), dtype=np.float32), 44100, target, "wav", "Estéreo", 44100)
        text = self.text()
        self.assertIn("formato wav", text)
        self.assertIn("<arquivo>.wav", text)
        self.assert_private(text)

    def test_speech_failure_does_not_record_spoken_text(self):
        speaker = Speaker.__new__(Speaker)
        speaker._output = mock.Mock()
        speaker._output.speak.side_effect = RuntimeError("Arquivo salvo: Maria.mp3")
        speaker.speak("Saída de som: Fone da Maria.")
        text = self.text()
        self.assertIn("Falha ao falar pelo leitor de tela (RuntimeError)", text)
        self.assert_private(text)

    def test_user_message_is_not_recorded(self):
        announcer = Announcer(None, FakeSpeaker([]), VERSION)
        with mock.patch.object(Announcer, "dialog"):
            with operation(SAVE):
                announcer.error("Não foi possível salvar Maria.wav.", SAVE)
        self.assert_private(self.text())


class OperationRecordTests(LogCase):
    def setUp(self) -> None:
        super().setUp()
        self.announcer = Announcer(None, FakeSpeaker([]), VERSION)
        patcher = mock.patch.object(Announcer, "dialog")
        self.dialog = patcher.start()
        self.addCleanup(patcher.stop)

    def test_error_shown_without_technical_record_is_recorded_once(self):
        try:
            try:
                raise PermissionError(13, "Permission denied")
            except PermissionError:
                raise AudioSaveError("Sem permissão.") from None
        except AudioSaveError as error:
            with operation(SAVE):
                self.announcer.error(str(error), SAVE, error)
        records = self.records()
        self.assertEqual(len(records), 1)
        self.assertIn(f"Erro informado ao usuário: {SAVE} (AudioSaveError, PermissionError, errno 13)", records[0])
        self.assertIn(f"operação={SAVE}", records[0])
        self.dialog.assert_called_once()

    def test_technical_record_is_not_duplicated_by_the_shown_error(self):
        with operation(RUN_OPTION):
            try:
                raise RuntimeError("falha")
            except RuntimeError:
                logger.exception("Erro ao executar a opção 'Salvar'")
                self.announcer.error("Não foi possível executar a opção Salvar.", RUN_OPTION)
        self.assertEqual(len(self.records()), 1)
        self.dialog.assert_called_once()

    def test_inner_operation_is_recorded_once_inside_menu_option(self):
        with operation(RUN_OPTION):
            with operation(SAVE):
                self.announcer.error("Sem permissão.", SAVE, AudioSaveError("Sem permissão."))
        records = self.records()
        self.assertEqual(len(records), 1)
        self.assertIn(f"operação={SAVE}", records[0])

    def test_each_occurrence_gets_its_own_record(self):
        for _ in range(2):
            with operation(SAVE):
                self.announcer.error("Sem permissão.", SAVE, AudioSaveError("Sem permissão."))
        self.assertEqual(len(self.records()), 2)


class LogFailureTests(LogCase):
    def setUp(self) -> None:
        super().setUp()
        shutdown_logging()

    def test_no_usable_folder_keeps_program_running(self):
        self.program_logs.parent.write_text("x")
        with mock.patch.dict(os.environ, {}, clear=True):
            setup_logging(VERSION, console=False)
            with self.assertLogs("src.models.app_log", level="WARNING") as captured:
                logger.warning("continua funcionando")
                logger.error("de novo")
        self.assertIsNone(self.path)
        self.assertEqual(sum("Nenhuma pasta disponível" in line for line in captured.output), 1)
        self.assertNotIn(str(self.base), "".join(captured.output))

    def test_write_failure_is_silent(self):
        (self.program_logs / "sound_mine.log").mkdir(parents=True)
        setup_logging(VERSION, console=False)
        logger.warning("não consegue gravar")
        logger.error("de novo")
        self.assertEqual(self.path, self.program_logs / "sound_mine.log")


class UnhandledErrorTests(LogCase):
    def test_unhandled_errors_are_recorded_and_previous_hook_still_runs(self):
        shutdown_logging()
        previous = mock.Mock()
        with mock.patch.object(sys, "excepthook", previous):
            setup_logging(VERSION, console=False)
            try:
                raise ValueError(r"falha em 'D:\Pessoal\Maria.mp3'")
            except ValueError:
                sys.excepthook(*sys.exc_info())
            previous.assert_called_once()
            shutdown_logging()
        text = self.text()
        self.assertIn("CRITICAL", text)
        self.assertIn("Erro não tratado (ValueError)", text)
        self.assertNotIn("Maria", text)

    def test_thread_errors_are_recorded(self):
        def fail() -> None:
            raise RuntimeError("falha na thread")

        with mock.patch.object(app_log, "_previous_hooks", app_log._previous_hooks):
            previous = mock.Mock()
            shutdown_logging()
            with mock.patch.object(threading, "excepthook", previous):
                setup_logging(VERSION, console=False)
                thread = threading.Thread(target=fail)
                thread.start()
                thread.join()
                previous.assert_called_once()
                shutdown_logging()
        self.assertIn("Erro não tratado em uma thread (RuntimeError)", self.text())


class OpenFileIntegrationTests(ScreenFlowCase, LogCase):
    def setUp(self) -> None:
        LogCase.setUp(self)
        ScreenFlowCase.setUp(self)
        self.manager.announcer = Announcer(None, FakeSpeaker(self.log), VERSION)
        self.manager.outputs = OutputCoordinator(FakeBackend([HEADSET], HEADSET))
        patcher = mock.patch.object(Announcer, "dialog")
        self.dialog = patcher.start()
        self.addCleanup(patcher.stop)

    def test_corrupted_file_gives_one_record_with_operation_and_audio_data(self):
        path = self.audio_file("Maria segredo.wav", b"nao e audio" * 10)
        open_file = main_menu.build_main_menu(self.manager).items[0].action
        with mock.patch.object(main_menu, "choose_audio_file", return_value=path), \
                mock.patch.object(self.manager.settings, "memory_mb", 0, create=True):
            open_file()
        records = self.records()
        self.assertEqual(len(records), 1)
        self.assertIn(f"operação={OPEN_FILE}", records[0])
        self.assertIn("arquivo=(.wav, 110 bytes)", records[0])
        self.assertNotIn("Maria", self.text())
        self.dialog.assert_called_once()
        self.assertEqual(self.dialog.call_args.args[1], "Erro ao abrir arquivo")


if __name__ == "__main__":
    unittest.main()
