import contextlib
import contextvars
import logging
import logging.handlers
import os
import platform
import re
import sys
import tempfile
import threading
from importlib import metadata
from pathlib import Path

LOG_FILE_NAME = "sound_mine.log"
MAX_BYTES = 1024 * 1024
BACKUP_COUNT = 3
LEVEL = logging.WARNING
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROGRAM_LOG_FOLDER = PROJECT_ROOT / "logs"
PACKAGES = (("wxPython", "wxPython"), ("PyAV", "av"), ("sounddevice", "sounddevice"), ("soundfile", "soundfile"))
NO_VALUE = "-"
FORMAT = ("%(asctime)s %(levelname)s [%(version)s] %(module)s.%(funcName)s:%(lineno)d "
          "operação=%(operation)s%(audio_text)s | %(message)s")

logger = logging.getLogger(__name__)

_version = NO_VALUE
_operation: contextvars.ContextVar = contextvars.ContextVar("sound_mine_operation", default=None)
_handlers: list[logging.Handler] = []
_previous_hooks: tuple | None = None
_base_factory = logging.getLogRecordFactory()


class _OperationState:
    def __init__(self, name: str, audio: str | None) -> None:
        self.name = name
        self.audio = audio
        self.records = 0


def describe_audio_file(path: Path | None, with_size: bool = True) -> str | None:
    if path is None:
        return None
    extension = path.suffix.lower() or "sem extensão"
    if not with_size:
        return extension
    try:
        return f"{extension}, {path.stat().st_size} bytes"
    except OSError:
        return f"{extension}, tamanho indisponível"


@contextlib.contextmanager
def operation(name: str, audio_file: Path | None = None, with_size: bool = True):
    token = _operation.set(_OperationState(name, describe_audio_file(audio_file, with_size)))
    try:
        yield
    finally:
        _operation.reset(token)


def operation_logged() -> bool:
    state = _operation.get()
    return state is not None and state.records > 0


def _record_factory(*args, **kwargs) -> logging.LogRecord:
    record = _base_factory(*args, **kwargs)
    state = _operation.get()
    record.version = _version
    record.operation = state.name if state is not None else NO_VALUE
    record.audio = state.audio if state is not None else None
    if state is not None and record.levelno >= logging.WARNING:
        state.records += 1
    return record


logging.setLogRecordFactory(_record_factory)


def _path_variants(path: Path | str | None) -> list[str]:
    if not path:
        return []
    text = str(path).rstrip("\\/")
    variants = {text, text.replace("\\", "/"), text.replace("\\", "\\\\")}
    return sorted((variant for variant in variants if len(variant) > 3), key=len, reverse=True)


def _replace_prefix(text: str, prefix: str, replacement: str) -> str:
    return re.sub(re.escape(prefix), lambda match: replacement, text, flags=re.IGNORECASE)


def _hidden_path(match: re.Match) -> str:
    quote, path = match.group(1), match.group(2)
    name = re.split(r"[\\/]+", path.rstrip("\\/"))[-1]
    suffix = Path(name).suffix
    hidden = f"<arquivo>{suffix.lower()}" if suffix and len(suffix) <= 6 else "<caminho>"
    return f"{quote}{hidden}{quote}"


_QUOTED_PATH = re.compile(r"""(['"])((?:[A-Za-z]:[\\/]|\\\\|//)[^'"\r\n]*)\1""")
_LOOSE_AUDIO_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|\\\\)\S*?\.(mp3|m4a|wav|ogg)\b", re.IGNORECASE)
_USERS_FOLDER = re.compile(r"([A-Za-z]:[\\/]+Users[\\/]+)[^\\/\s'\"]+", re.IGNORECASE)


def _home() -> Path | None:
    try:
        return Path.home()
    except Exception:
        return None


def _separator(prefix: str) -> str:
    if "\\\\" in prefix:
        return "\\\\"
    return "/" if "/" in prefix else "\\"


def sanitize(text: str) -> str:
    for prefix in _path_variants(PROJECT_ROOT):
        text = _replace_prefix(text, prefix + _separator(prefix), "")
    for root in {sys.base_prefix, sys.prefix}:
        for prefix in _path_variants(root):
            text = _replace_prefix(text, prefix, "<python>")
    text = _QUOTED_PATH.sub(_hidden_path, text)
    text = _LOOSE_AUDIO_PATH.sub(lambda match: f"<arquivo>.{match.group(1).lower()}", text)
    for prefix in _path_variants(os.environ.get("USERPROFILE")) + _path_variants(_home()):
        text = _replace_prefix(text, prefix, "%USERPROFILE%")
    return _USERS_FOLDER.sub(lambda match: f"{match.group(1)}<usuário>", text)


class PrivacyFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__(FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        for name, default in (("version", NO_VALUE), ("operation", NO_VALUE), ("audio", None)):
            if not hasattr(record, name):
                setattr(record, name, default)
        record.audio_text = f" arquivo=({record.audio})" if record.audio else ""
        return sanitize(super().format(record))


class SessionFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, folders: list[Path], header: str) -> None:
        super().__init__(folders[0] / LOG_FILE_NAME, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT,
                         encoding="utf-8", delay=True)
        self._folders = folders
        self._header = header
        self._resolved = False
        self.path: Path | None = None

    def emit(self, record: logging.LogRecord) -> None:
        if not self._resolved:
            self._resolved = True
            self.path = self._choose_folder()
            if self.path is None:
                logger.warning("Nenhuma pasta disponível para o arquivo de log; os erros ficam só no console.")
                return
            self.baseFilename = os.path.abspath(self.path)
            try:
                self.stream = self._open()
                self.stream.write(self._header + self.terminator)
            except Exception:
                self.handleError(record)
        if self.path is None:
            return
        super().emit(record)

    def _choose_folder(self) -> Path | None:
        for folder in self._folders:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryFile(dir=folder):
                    pass
            except Exception:
                continue
            return folder / LOG_FILE_NAME
        return None


def log_folders() -> list[Path]:
    folders = [PROGRAM_LOG_FOLDER]
    base = os.environ.get("LOCALAPPDATA")
    if base:
        folders.append(Path(base) / "Sound Mine" / "logs")
    return folders


def log_path() -> Path | None:
    for handler in _handlers:
        if isinstance(handler, SessionFileHandler):
            return handler.path
    return None


def environment_header(version: str, speech_available: bool) -> str:
    versions = []
    for label, package in PACKAGES:
        try:
            versions.append(f"{label} {metadata.version(package)}")
        except Exception:
            versions.append(f"{label} indisponível")
    reader = "disponível" if speech_available else "indisponível"
    return sanitize(
        f"=== {version} | Windows {platform.release()} ({platform.version()}) | "
        f"Python {platform.python_version()} | {' | '.join(versions)} | leitor de tela: {reader}"
    )


def setup_logging(version: str, speech_available: bool = True, console: bool = True) -> None:
    global _version
    _version = version
    logging.raiseExceptions = False
    root = logging.getLogger()
    root.setLevel(LEVEL)
    formatter = PrivacyFormatter()
    if console:
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        _add_handler(root, stream)
    handler = SessionFileHandler(log_folders(), environment_header(version, speech_available))
    handler.setFormatter(formatter)
    _add_handler(root, handler)
    _install_hooks()


def shutdown_logging() -> None:
    global _version, _previous_hooks
    root = logging.getLogger()
    for handler in list(_handlers):
        root.removeHandler(handler)
        handler.close()
    _handlers.clear()
    if _previous_hooks is not None:
        sys.excepthook, threading.excepthook = _previous_hooks
        _previous_hooks = None
    _version = NO_VALUE


def _add_handler(root: logging.Logger, handler: logging.Handler) -> None:
    root.addHandler(handler)
    _handlers.append(handler)


def _install_hooks() -> None:
    global _previous_hooks
    if _previous_hooks is not None:
        return
    previous_excepthook, previous_thread_hook = sys.excepthook, threading.excepthook
    _previous_hooks = (previous_excepthook, previous_thread_hook)

    def excepthook(error_type, error, traceback) -> None:
        logger.critical("Erro não tratado (%s).", error_type.__name__, exc_info=(error_type, error, traceback))
        previous_excepthook(error_type, error, traceback)

    def thread_excepthook(args) -> None:
        if args.exc_type is not SystemExit:
            logger.critical("Erro não tratado em uma thread (%s).", args.exc_type.__name__,
                            exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        previous_thread_hook(args)

    sys.excepthook = excepthook
    threading.excepthook = thread_excepthook
