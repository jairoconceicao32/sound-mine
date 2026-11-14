import base64
import hashlib
import json
import tempfile
import unittest
import zlib
from dataclasses import asdict
from pathlib import Path
from unittest import mock

from src.models.settings import Settings, is_valid, settings_from
from src.models.settings_store import (
    INVALID_SUFFIX,
    MAX_FILE_BYTES,
    SETTINGS_PATH,
    LoadStatus,
    SettingsSaveError,
    encode,
    encode_bytes,
    load_settings,
    save_settings,
    signature,
)

LOGGER = "src.models.settings_store"


def decoded(path: Path) -> dict:
    return json.loads(zlib.decompress(base64.b64decode(path.read_bytes())).decode("utf-8"))


def changed_settings() -> Settings:
    return Settings(language="inglês", format="ogg", channel="Mono", sample_rate="96000",
                    echo_delay=2000, echo_percent=0, reverb_percent=100, reverb_delay=10,
                    memory_mb=4096, disable_sounds=True, disable_tips=True)


def signed(values: dict, version: int = 1) -> dict:
    return {"versao": version, "configuracoes": values, "verificacao": signature(values)}


class SettingsValidationTests(unittest.TestCase):
    def test_accepts_valid_values(self):
        for key, value in asdict(changed_settings()).items():
            with self.subTest(key=key):
                self.assertTrue(is_valid(key, value))

    def test_rejects_wrong_types_and_out_of_range(self):
        cases = [
            ("memory_mb", 4097), ("memory_mb", -1), ("memory_mb", True), ("memory_mb", 4.5),
            ("memory_mb", "4"), ("memory_mb", None), ("echo_delay", 9), ("echo_percent", 101),
            ("language", "Klingon"), ("language", 1), ("format", "MP3"), ("sample_rate", 44100),
            ("disable_sounds", 1), ("disable_tips", "true"), ("disable_tips", None),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                self.assertFalse(is_valid(key, value))

    def test_settings_from_keeps_valid_and_corrects_only_invalid(self):
        values = asdict(changed_settings())
        values["memory_mb"] = 9999
        del values["channel"]
        values["desconhecida"] = "x"
        settings, corrected = settings_from(values)
        self.assertEqual(settings.memory_mb, 0)
        self.assertEqual(settings.channel, "Estéreo")
        self.assertEqual(settings.language, "inglês")
        self.assertEqual(set(corrected), {"memory_mb", "channel"})

    def test_settings_from_valid_data_has_no_corrections(self):
        settings, corrected = settings_from(asdict(changed_settings()))
        self.assertEqual(settings, changed_settings())
        self.assertEqual(corrected, ())


class SettingsPathTests(unittest.TestCase):
    def test_file_is_in_program_folder(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(SETTINGS_PATH, root / "settings.dat")
        self.assertTrue((SETTINGS_PATH.parent / "sound_mine.py").is_file())


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "Sound Mine" / "settings.dat"
        self.invalid = self.path.with_name(self.path.name + INVALID_SUFFIX)

    def write_raw(self, data: bytes) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(data)

    def write(self, content) -> None:
        self.write_raw(encode_bytes(content) if isinstance(content, bytes) else encode(content))

    def assert_tampered(self) -> None:
        with self.assertLogs(LOGGER, "WARNING"):
            result = load_settings(self.path)
        self.assertIs(result.status, LoadStatus.TAMPERED)
        self.assertEqual(result.settings, Settings())
        self.assertFalse(self.path.exists())
        self.assertTrue(self.invalid.exists())

    def test_missing_file_gives_defaults(self):
        result = load_settings(self.path)
        self.assertIs(result.status, LoadStatus.NEW)
        self.assertEqual(result.settings, Settings())
        self.assertFalse(self.path.exists())

    def test_save_and_load_round_trip(self):
        save_settings(changed_settings(), self.path)
        result = load_settings(self.path)
        self.assertIs(result.status, LoadStatus.LOADED)
        self.assertEqual(result.settings, changed_settings())

    def test_saved_file_hides_values(self):
        save_settings(changed_settings(), self.path)
        text = self.path.read_bytes().decode("ascii")
        for hidden in ("inglês", "ingl", "ogg", "4096", "memory_mb", "configuracoes", "verificacao", "{"):
            with self.subTest(hidden=hidden):
                self.assertNotIn(hidden, text)

    def test_saved_file_contains_version_values_and_signature(self):
        save_settings(Settings(), self.path)
        content = decoded(self.path)
        self.assertEqual(content["versao"], 1)
        self.assertEqual(content["configuracoes"], asdict(Settings()))
        self.assertEqual(content["verificacao"], signature(asdict(Settings())))

    def test_save_replaces_previous_file_without_leftovers(self):
        save_settings(Settings(), self.path)
        save_settings(changed_settings(), self.path)
        self.assertEqual(load_settings(self.path).settings, changed_settings())
        self.assertEqual([item.name for item in self.path.parent.iterdir()], ["settings.dat"])

    def test_edited_value_is_detected(self):
        save_settings(Settings(), self.path)
        content = decoded(self.path)
        content["configuracoes"]["memory_mb"] = 2048
        self.write(content)
        self.assert_tampered()

    def test_signature_recalculated_without_the_key_is_detected(self):
        values = asdict(Settings())
        values["memory_mb"] = 2048
        text = json.dumps({"versao": 1, "configuracoes": values}, sort_keys=True,
                          ensure_ascii=False, separators=(",", ":"))
        plain = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.write({"versao": 1, "configuracoes": values, "verificacao": plain})
        self.assert_tampered()

    def test_edited_character_is_detected(self):
        save_settings(changed_settings(), self.path)
        data = bytearray(self.path.read_bytes())
        data[10] = ord("A") if data[10] != ord("A") else ord("B")
        self.write_raw(bytes(data))
        self.assert_tampered()

    def test_invalid_encodings_are_detected(self):
        compressed = zlib.compress(encode(signed(asdict(Settings()))))
        cases = {
            "texto qualquer": "isto não é base64 válido!".encode("utf-8"),
            "json legível antigo": json.dumps(signed(asdict(Settings()))).encode("utf-8"),
            "base64 sem zlib": base64.b64encode(b"qualquer coisa"),
            "zlib cortado": base64.b64encode(zlib.compress(b"x" * 1000)[:-6]),
            "dados depois do zlib": base64.b64encode(zlib.compress(b"{}") + b"extra"),
            "bomba zip": base64.b64encode(zlib.compress(b" " * (MAX_FILE_BYTES * 50), 9)),
            "codificado duas vezes": base64.b64encode(compressed),
        }
        for name, data in cases.items():
            with self.subTest(name):
                self.write_raw(data)
                self.assert_tampered()
                self.invalid.unlink()

    def test_edited_check_is_detected(self):
        content = signed(asdict(Settings()))
        content["verificacao"] = "0" * 64
        self.write(content)
        self.assert_tampered()

    def test_non_ascii_check_is_detected(self):
        content = signed(asdict(Settings()))
        content["verificacao"] = "ção"
        self.write(content)
        self.assert_tampered()

    def test_invalid_contents_are_detected(self):
        values = asdict(Settings())
        cases = {
            "json inválido": b"{ isto nao e json",
            "utf-8 inválido": b"\xff\xfe\x00",
            "vazio": b"",
            "lista": [],
            "texto": "configuracoes",
            "sem verificação": {"versao": 1, "configuracoes": values},
            "chave a mais": {**signed(values), "extra": 1},
            "versão desconhecida": signed(values, version=2),
            "versão booleana": {**signed(values), "versao": True},
            "configurações em lista": {"versao": 1, "configuracoes": [], "verificacao": signature([])},
            "verificação numérica": {**signed(values), "verificacao": 1},
            "chave repetida": ('{"versao": 1, "versao": 1, "configuracoes": {}, "verificacao": "%s"}'
                               % signature({})).encode("utf-8"),
            "aninhamento profundo": b"[" * 20000 + b"]" * 20000,
        }
        for name, content in cases.items():
            with self.subTest(name):
                self.write(content)
                self.assert_tampered()
                self.invalid.unlink()

    def test_file_too_large_is_detected(self):
        self.write_raw(b"A" * (MAX_FILE_BYTES + 1))
        self.assert_tampered()

    def test_signed_value_outside_rules_is_corrected_alone(self):
        values = asdict(changed_settings())
        values["memory_mb"] = 9999
        del values["disable_tips"]
        values["desconhecida"] = 1
        self.write(signed(values))
        with self.assertLogs(LOGGER, "WARNING"):
            result = load_settings(self.path)
        self.assertIs(result.status, LoadStatus.CORRECTED)
        self.assertEqual(result.settings.memory_mb, 0)
        self.assertFalse(result.settings.disable_tips)
        self.assertEqual(result.settings.language, "inglês")
        self.assertTrue(self.path.exists())

    def test_signed_wrong_types_are_corrected(self):
        values = asdict(Settings())
        values.update(memory_mb=True, echo_delay=4.5, reverb_delay="200", disable_sounds=1)
        self.write(signed(values))
        with self.assertLogs(LOGGER, "WARNING"):
            result = load_settings(self.path)
        self.assertEqual(result.settings, Settings())

    def test_previous_invalid_copy_is_replaced(self):
        self.write_raw(b"antigo")
        self.assert_tampered()
        self.write_raw(b"novo")
        self.assert_tampered()
        self.assertEqual(self.invalid.read_bytes(), b"novo")

    def test_unreadable_file_gives_defaults_and_keeps_file(self):
        save_settings(changed_settings(), self.path)
        with mock.patch.object(Path, "open", side_effect=PermissionError(13, "negado")), \
                self.assertLogs(LOGGER, "WARNING"):
            result = load_settings(self.path)
        self.assertIs(result.status, LoadStatus.UNREADABLE)
        self.assertEqual(result.settings, Settings())
        self.assertTrue(self.path.exists())
        self.assertFalse(self.invalid.exists())

    def test_failed_save_keeps_previous_file(self):
        save_settings(Settings(), self.path)
        with mock.patch("src.models.settings_store.os.replace", side_effect=OSError(28, "sem espaço")), \
                self.assertLogs(LOGGER, "ERROR"), self.assertRaises(SettingsSaveError) as raised:
            save_settings(changed_settings(), self.path)
        self.assertIsNotNone(raised.exception.hint)
        self.assertEqual(load_settings(self.path).settings, Settings())
        self.assertEqual([item.name for item in self.path.parent.iterdir()], ["settings.dat"])

    def test_save_failure_when_folder_cannot_be_created(self):
        with mock.patch.object(Path, "mkdir", side_effect=PermissionError(13, "negado")), \
                self.assertLogs(LOGGER, "ERROR"), self.assertRaises(SettingsSaveError):
            save_settings(Settings(), self.path)

    def test_log_does_not_contain_path_or_values(self):
        values = asdict(changed_settings())
        values["memory_mb"] = 9999
        self.write(signed(values))
        with self.assertLogs(LOGGER, "WARNING") as logs:
            load_settings(self.path)
        text = "\n".join(logs.output)
        self.assertNotIn(self.folder.name, text)
        self.assertNotIn("9999", text)
        self.assertNotIn("inglês", text)


if __name__ == "__main__":
    unittest.main()
