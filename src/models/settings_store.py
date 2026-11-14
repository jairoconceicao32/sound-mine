import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
import tempfile
import zlib
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

from src.models.errors import SoundMineError
from src.models.settings import Settings, settings_from

logger = logging.getLogger(__name__)

FILE_NAME = "settings.dat"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = PROJECT_ROOT / FILE_NAME
INVALID_SUFFIX = ".invalido"
MAX_FILE_BYTES = 64 * 1024
FORMAT_VERSION = 1
VERSION_KEY = "versao"
SETTINGS_KEY = "configuracoes"
CHECK_KEY = "verificacao"
SIGNING_KEY = bytes.fromhex("0e969d6b66da0295e08f2e2e8369d10f6004b432ebfa9e02616f4e03a10d0b69")
SAVE_FAILED_MESSAGE = "As configurações foram aplicadas, mas não puderam ser guardadas."
SAVE_FAILED_HINT = ("Elas voltarão ao padrão quando o programa for fechado. "
                    "Verifique se há espaço livre no disco.")
TAMPERED_MESSAGE = ("As configurações estavam danificadas ou foram alteradas fora do Sound Mine. "
                    "Os valores padrão foram restaurados. Revise as opções em Configurações.")
UNREADABLE_MESSAGE = ("O arquivo de configurações está em uso por outro programa ou sem permissão de leitura. "
                      "Os valores padrão serão usados até o programa ser fechado. "
                      "Feche o programa que está usando o arquivo settings.dat e abra o Sound Mine novamente.")


class LoadStatus(Enum):
    NEW = "new"
    LOADED = "loaded"
    CORRECTED = "corrected"
    TAMPERED = "tampered"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class LoadResult:
    settings: Settings
    status: LoadStatus


class SettingsSaveError(SoundMineError):
    pass


class _InvalidFile(Exception):
    pass


def signature(values: dict) -> str:
    content = {VERSION_KEY: FORMAT_VERSION, SETTINGS_KEY: values}
    text = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hmac.new(SIGNING_KEY, text.encode("utf-8"), hashlib.sha256).hexdigest()


def encode(content: object) -> bytes:
    text = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    return encode_bytes(text.encode("utf-8"))


def encode_bytes(data: bytes) -> bytes:
    return base64.b64encode(zlib.compress(data, 9)) + b"\n"


def load_message(status: LoadStatus) -> str | None:
    if status is LoadStatus.TAMPERED:
        return TAMPERED_MESSAGE
    if status is LoadStatus.UNREADABLE:
        return UNREADABLE_MESSAGE
    return None


def load_settings(path: Path) -> LoadResult:
    try:
        raw = _read(path)
    except FileNotFoundError:
        return LoadResult(Settings(), LoadStatus.NEW)
    except _InvalidFile as error:
        return _tampered(path, str(error))
    except OSError as error:
        logger.warning("Não foi possível ler as configurações (%s, errno %s).",
                       type(error).__name__, error.errno)
        return LoadResult(Settings(), LoadStatus.UNREADABLE)

    try:
        values = _verified_values(raw)
    except _InvalidFile as error:
        return _tampered(path, str(error))

    settings, corrected = settings_from(values)
    if corrected:
        logger.warning("Configurações fora das regras voltaram ao padrão: %s.", ", ".join(corrected))
        return LoadResult(settings, LoadStatus.CORRECTED)
    return LoadResult(settings, LoadStatus.LOADED)


def save_settings(settings: Settings, path: Path) -> None:
    values = asdict(settings)
    data = encode({VERSION_KEY: FORMAT_VERSION, SETTINGS_KEY: values, CHECK_KEY: signature(values)})
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, name = tempfile.mkstemp(prefix=".sound_mine_", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(handle, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    except OSError as error:
        logger.error("Falha ao guardar as configurações (%s, errno %s).",
                     type(error).__name__, error.errno)
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise SettingsSaveError(SAVE_FAILED_MESSAGE, SAVE_FAILED_HINT) from None


def _read(path: Path) -> bytes:
    with path.open("rb") as file:
        raw = file.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise _InvalidFile("arquivo grande demais")
    return raw


def _decode_bytes(raw: bytes) -> bytes:
    try:
        compressed = base64.b64decode(raw.strip(), validate=True)
        decompressor = zlib.decompressobj()
        data = decompressor.decompress(compressed, MAX_FILE_BYTES)
    except (binascii.Error, ValueError, zlib.error):
        raise _InvalidFile("conteúdo ilegível") from None
    if decompressor.unconsumed_tail:
        raise _InvalidFile("conteúdo grande demais")
    if not decompressor.eof or decompressor.unused_data:
        raise _InvalidFile("conteúdo ilegível")
    return data


def _verified_values(raw: bytes) -> dict:
    data = _decode_bytes(raw)
    try:
        content = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_keys)
    except _InvalidFile:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise _InvalidFile("conteúdo ilegível") from None
    if not isinstance(content, dict) or set(content) != {VERSION_KEY, SETTINGS_KEY, CHECK_KEY}:
        raise _InvalidFile("estrutura inválida")
    if type(content[VERSION_KEY]) is not int or content[VERSION_KEY] != FORMAT_VERSION:
        raise _InvalidFile("versão desconhecida")
    values, check = content[SETTINGS_KEY], content[CHECK_KEY]
    if not isinstance(values, dict) or not isinstance(check, str):
        raise _InvalidFile("estrutura inválida")
    if not hmac.compare_digest(check.encode("utf-8"), signature(values).encode("ascii")):
        raise _InvalidFile("verificação não confere")
    return values


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    content = {}
    for key, value in pairs:
        if key in content:
            raise _InvalidFile("chave repetida")
        content[key] = value
    return content


def _tampered(path: Path, reason: str) -> LoadResult:
    logger.warning("Configurações descartadas: %s.", reason)
    try:
        os.replace(path, path.with_name(path.name + INVALID_SUFFIX))
    except OSError as error:
        logger.warning("Não foi possível guardar a cópia das configurações descartadas (%s, errno %s).",
                       type(error).__name__, error.errno)
    return LoadResult(Settings(), LoadStatus.TAMPERED)
