import tempfile
import unittest
from dataclasses import asdict, fields
from pathlib import Path
from unittest import mock

from src.controllers.settings import (
    ButtonField,
    NumberField,
    OptionField,
    SettingsDefinitionError,
    SettingsForm,
    SettingsTab,
    ToggleField,
    build_settings_form,
    load_startup_settings,
)
from src.models.settings import OPTIONS, RANGES, NumberRange, Settings
from src.models.settings_store import (
    SAVE_FAILED_MESSAGE,
    TAMPERED_MESSAGE,
    UNREADABLE_MESSAGE,
    encode,
    load_settings,
    save_settings,
    signature,
)
from tests.test_settings_store import decoded


def noop() -> None:
    pass


def make_form(values: dict | None = None) -> SettingsForm:
    return SettingsForm(
        "Configurações",
        [
            SettingsTab("Geral", [OptionField("language", "Idioma", ["Português", "Inglês"])]),
            SettingsTab("Áudio", [OptionField("channels", "Canais", ["Estéreo", "Mono"])]),
        ],
        [ButtonField("Salvar", noop), ButtonField("Cancelar", noop)],
        values or {},
    )


class SettingsFormTests(unittest.TestCase):
    def setUp(self):
        self.form = make_form()

    def test_starts_on_tab_selector(self):
        self.assertEqual(self.form.tab.name, "Geral")
        self.assertEqual(self.form.text_of(self.form.current()), "Guia: Geral")

    def test_invalid_value_falls_back_to_first_option(self):
        form = make_form({"language": "Klingon"})
        self.assertEqual(form.values["language"], "Português")

    def test_fields_order_is_tab_then_fields_then_buttons(self):
        labels = [self.form.text_of(field) for field in self.form.fields]
        self.assertEqual(labels, ["Guia: Geral", "Idioma: Português", "Salvar", "Cancelar"])

    def test_field_navigation_stops_at_ends(self):
        self.assertFalse(self.form.prev_field())
        for _ in range(3):
            self.assertTrue(self.form.next_field())
        self.assertFalse(self.form.next_field())
        self.assertEqual(self.form.current().label, "Cancelar")

    def test_arrows_on_tab_selector_change_tab(self):
        self.assertFalse(self.form.change_value(-1))
        self.assertTrue(self.form.change_value(1))
        self.assertEqual(self.form.text_of(self.form.current()), "Guia: Áudio")
        self.assertFalse(self.form.change_value(1))

    def test_ctrl_tab_navigation_returns_to_selector_and_stops_at_ends(self):
        self.form.next_field()
        self.assertFalse(self.form.prev_tab())
        self.assertTrue(self.form.next_tab())
        self.assertEqual(self.form.tab.name, "Áudio")
        self.assertEqual(self.form.field_index, 0)
        self.assertFalse(self.form.next_tab())

    def test_change_value_stops_at_ends(self):
        self.form.next_field()
        self.assertFalse(self.form.change_value(-1))
        self.assertTrue(self.form.change_value(1))
        self.assertEqual(self.form.values["language"], "Inglês")
        self.assertFalse(self.form.change_value(1))

    def test_change_value_on_button_does_nothing(self):
        self.form.next_field()
        self.form.next_field()
        self.assertFalse(self.form.change_value(1))

    def test_values_returns_copy(self):
        self.form.values["language"] = "Inglês"
        self.assertEqual(self.form.values["language"], "Português")

    def test_rejects_empty_options(self):
        with self.assertRaises(SettingsDefinitionError):
            OptionField("x", "X", [])

    def test_rejects_repeated_keys(self):
        field = OptionField("language", "Idioma", ["Português"])
        with self.assertRaises(SettingsDefinitionError):
            SettingsForm("T", [SettingsTab("A", [field]), SettingsTab("B", [field])], [], {})


def make_number_form(value=None) -> SettingsForm:
    form = SettingsForm(
        "Configurações",
        [SettingsTab("Efeitos", [
            NumberField("delay", "Eco", minimum=10, maximum=2000, step=10, big_step=100),
        ])],
        [ButtonField("Salvar", noop)],
        {"delay": value} if value is not None else {},
    )
    form.next_field()
    return form


class NumberFieldTests(unittest.TestCase):
    def test_uses_given_value_and_suffix(self):
        form = make_number_form(300)
        self.assertEqual(form.text_of(form.current()), "Eco: 300%")

    def test_invalid_initial_value_falls_back_to_minimum(self):
        self.assertEqual(make_number_form(5000).values["delay"], 10)
        self.assertEqual(make_number_form("300").values["delay"], 10)
        self.assertEqual(make_number_form(True).values["delay"], 10)

    def test_up_increases_and_down_decreases(self):
        form = make_number_form(300)
        self.assertTrue(form.change_value(-1))
        self.assertEqual(form.values["delay"], 310)
        self.assertTrue(form.change_value(1))
        self.assertTrue(form.change_value(1))
        self.assertEqual(form.values["delay"], 290)

    def test_big_step_and_limits(self):
        form = make_number_form(300)
        self.assertTrue(form.change_big(1))
        self.assertEqual(form.values["delay"], 400)
        self.assertTrue(form.go_to_limit(maximum=True))
        self.assertEqual(form.values["delay"], 2000)
        self.assertFalse(form.change_value(-1))
        self.assertTrue(form.go_to_limit(maximum=False))
        self.assertFalse(form.change_value(1))
        self.assertEqual(form.values["delay"], 10)

    def test_typing_valid_value(self):
        form = make_number_form(300)
        for digit in "450":
            self.assertTrue(form.type_digit(digit))
        self.assertTrue(form.confirm_typing())
        self.assertEqual(form.values["delay"], 450)
        self.assertIsNone(form.typing)

    def test_typing_out_of_range_is_not_applied(self):
        form = make_number_form(300)
        form.type_digit("5")
        self.assertFalse(form.confirm_typing())
        self.assertEqual(form.values["delay"], 300)

    def test_typing_limits_digits_and_rejects_non_digits(self):
        form = make_number_form(300)
        for digit in "1234":
            self.assertTrue(form.type_digit(digit))
        self.assertFalse(form.type_digit("5"))
        self.assertFalse(form.type_digit("A"))
        self.assertFalse(form.type_digit("²"))

    def test_erase_and_cancel(self):
        form = make_number_form(300)
        form.type_digit("4")
        form.type_digit("5")
        self.assertTrue(form.erase())
        self.assertEqual(form.typing, "4")
        self.assertTrue(form.cancel_typing())
        self.assertFalse(form.cancel_typing())
        self.assertEqual(form.values["delay"], 300)

    def test_moving_field_discards_typing(self):
        form = make_number_form(300)
        form.type_digit("4")
        form.next_field()
        self.assertIsNone(form.typing)

    def test_typing_not_accepted_on_option_field(self):
        self.assertFalse(make_form().type_digit("1"))

    def make_editable_form(self) -> SettingsForm:
        form = SettingsForm(
            "Configurações",
            [SettingsTab("Efeitos", [
                NumberField("delay", "Eco", minimum=10, maximum=2000, suffix=" ms", slider=False),
            ])],
            [],
            {"delay": 300},
        )
        form.next_field()
        return form

    def test_editable_field_ignores_arrows(self):
        form = self.make_editable_form()
        self.assertEqual(form.text_of(form.current()), "Eco: 300 ms")
        self.assertFalse(form.change_value(-1))
        self.assertFalse(form.change_big(1))
        self.assertFalse(form.go_to_limit(maximum=True))
        self.assertEqual(form.values["delay"], 300)

    def test_set_text_applies_valid_value(self):
        form = self.make_editable_form()
        self.assertTrue(form.set_text(" 450 "))
        self.assertEqual(form.values["delay"], 450)

    def test_set_text_rejects_invalid_text(self):
        form = self.make_editable_form()
        for text in ["", "5", "2001", "12a", "1.5", "-20", "²", "00010000"]:
            self.assertFalse(form.set_text(text), text)
        self.assertEqual(form.values["delay"], 300)

    def test_set_text_on_option_field_does_nothing(self):
        form = make_form()
        form.next_field()
        self.assertFalse(form.set_text("10"))

    def test_slider_erase_without_typing_does_nothing(self):
        form = make_number_form(300)
        self.assertFalse(form.erase())

    def test_rejects_invalid_range(self):
        with self.assertRaises(SettingsDefinitionError):
            NumberField("x", "X", minimum=10, maximum=10)


class ToggleFieldTests(unittest.TestCase):
    def make(self, value=None) -> SettingsForm:
        form = SettingsForm(
            "Configurações",
            [SettingsTab("Geral", [ToggleField("mute", "Desativar sons")])],
            [],
            {"mute": value} if value is not None else {},
        )
        form.next_field()
        return form

    def test_default_is_unchecked(self):
        form = self.make()
        self.assertIs(form.values["mute"], False)
        self.assertEqual(form.text_of(form.current()), "Desativar sons: não marcado")

    def test_invalid_initial_value_falls_back_to_unchecked(self):
        self.assertIs(self.make("sim").values["mute"], False)
        self.assertIs(self.make(1).values["mute"], False)

    def test_set_toggle(self):
        form = self.make()
        self.assertTrue(form.set_toggle(True))
        self.assertEqual(form.text_of(form.current()), "Desativar sons: marcado")
        self.assertFalse(form.set_toggle("sim"))
        self.assertIs(form.values["mute"], True)

    def test_set_toggle_on_other_field_does_nothing(self):
        self.assertFalse(make_form().set_toggle(True))


class SettingsModelTests(unittest.TestCase):
    def test_ranges_keep_current_values(self):
        self.assertEqual(RANGES, {
            "echo_delay": NumberRange(10, 2000),
            "echo_percent": NumberRange(0, 100),
            "reverb_delay": NumberRange(10, 2000),
            "reverb_percent": NumberRange(0, 100),
            "memory_mb": NumberRange(0, 4096),
        })

    def test_options_keep_current_values(self):
        self.assertEqual(OPTIONS, {
            "language": ("Português", "inglês", "espanhol"),
            "format": ("mp3", "m4a", "wav", "ogg"),
            "channel": ("Estéreo", "Mono"),
            "sample_rate": ("44100", "48000", "96000"),
        })

    def test_memory_default_is_automatic(self):
        self.assertEqual(Settings().memory_mb, 0)
        self.assertEqual(RANGES["memory_mb"].minimum, 0)

    def test_defaults_are_inside_options_and_ranges(self):
        settings = Settings()
        for key, options in OPTIONS.items():
            with self.subTest(key=key):
                self.assertIn(getattr(settings, key), options)
        for key, limits in RANGES.items():
            with self.subTest(key=key):
                self.assertTrue(limits.minimum <= getattr(settings, key) <= limits.maximum)

    def test_every_setting_has_a_rule(self):
        for field in fields(Settings):
            with self.subTest(key=field.name):
                if field.type in (bool, "bool"):
                    self.assertIsInstance(field.default, bool)
                else:
                    self.assertIn(field.name, OPTIONS.keys() | RANGES.keys())


class FakeSounds:
    def __init__(self):
        self.enabled = True


class FakeAnnouncer:
    def __init__(self):
        self.messages: list[str] = []
        self.errors: list[tuple[str, str]] = []

    def info(self, message: str) -> None:
        self.messages.append(message)

    def error(self, message: str, operation: str | None = None, error=None) -> None:
        self.errors.append((message, operation))


class FakeManager:
    def __init__(self):
        self.settings = Settings()
        self.sounds = FakeSounds()
        self.announcer = FakeAnnouncer()
        self.popped = 0

    def pop(self) -> None:
        self.popped += 1


class TemporaryFileTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "settings.dat"
        self.manager = FakeManager()


class SettingsScreenFormTests(TemporaryFileTestCase):
    def setUp(self):
        super().setUp()
        self.form = build_settings_form(self.manager, self.path)

    def input_fields(self) -> list:
        return [field for tab in self.form.tabs for field in tab.fields]

    def go_to_memory(self) -> None:
        names = [tab.name for tab in self.form.tabs]
        for _ in range(names.index("Desempenho")):
            self.form.next_tab()
        self.form.next_field()
        self.assertEqual(self.form.current().key, "memory_mb")

    def test_fields_use_model_options_and_ranges(self):
        for field in self.input_fields():
            with self.subTest(key=field.key):
                if isinstance(field, OptionField):
                    self.assertEqual(field.options, OPTIONS[field.key])
                elif isinstance(field, NumberField):
                    self.assertEqual(field.minimum, RANGES[field.key].minimum)
                    self.assertEqual(field.maximum, RANGES[field.key].maximum)
                else:
                    self.assertIsInstance(field, ToggleField)

    def test_form_covers_every_setting(self):
        keys = {field.key for field in self.input_fields()}
        self.assertEqual(keys, {field.name for field in fields(Settings)})

    def test_initial_values_are_the_defaults(self):
        self.assertEqual(self.form.values, asdict(Settings()))

    def test_performance_tab_has_only_memory(self):
        tab = next(tab for tab in self.form.tabs if tab.name == "Desempenho")
        self.assertEqual([field.key for field in tab.fields], ["memory_mb"])

    def test_memory_zero_is_announced_as_automatic(self):
        self.go_to_memory()
        self.assertEqual(self.form.text_of(self.form.current()), "Memória em megabytes: Automático")

    def test_memory_accepts_4096(self):
        self.go_to_memory()
        for digit in "4096":
            self.form.type_digit(digit)
        self.assertTrue(self.form.confirm_typing())
        self.assertEqual(self.form.values["memory_mb"], 4096)
        self.assertEqual(self.form.text_of(self.form.current()), "Memória em megabytes: 4096 megabytes")

    def test_memory_rejects_4097(self):
        self.go_to_memory()
        for digit in "4097":
            self.form.type_digit(digit)
        self.assertFalse(self.form.confirm_typing())
        self.assertEqual(self.form.values["memory_mb"], 0)

    def test_save_applies_every_value(self):
        self.go_to_memory()
        self.form.set_text("2048")
        self.form.prev_field()
        self.form.prev_tab()
        self.form.prev_tab()
        self.form.next_field()
        self.form.change_value(1)
        changed = self.form.values
        self.form.buttons[0].action()
        self.assertEqual(asdict(self.manager.settings), changed)
        self.assertEqual(self.manager.settings.memory_mb, 2048)
        self.assertEqual(self.manager.settings.language, "inglês")
        self.assertEqual(self.manager.popped, 1)
        self.assertEqual(self.manager.announcer.messages, ["Configurações salvas."])

    def test_save_updates_interface_sounds(self):
        self.manager.settings.disable_sounds = True
        form = build_settings_form(self.manager, self.path)
        form.buttons[0].action()
        self.assertFalse(self.manager.sounds.enabled)

    def test_save_writes_the_file(self):
        self.go_to_memory()
        self.form.set_text("2048")
        self.form.buttons[0].action()
        result = load_settings(self.path)
        self.assertEqual(result.settings, self.manager.settings)
        self.assertEqual(result.settings.memory_mb, 2048)

    def test_save_failure_keeps_values_and_reports(self):
        self.go_to_memory()
        self.form.set_text("2048")
        with mock.patch("src.models.settings_store.os.replace", side_effect=OSError(28, "sem espaço")), \
                self.assertLogs("src.models.settings_store", "ERROR"):
            self.form.buttons[0].action()
        self.assertEqual(self.manager.settings.memory_mb, 2048)
        self.assertEqual(self.manager.popped, 1)
        self.assertEqual(self.manager.announcer.messages, [])
        self.assertEqual(len(self.manager.announcer.errors), 1)
        message, operation = self.manager.announcer.errors[0]
        self.assertTrue(message.startswith(SAVE_FAILED_MESSAGE))
        self.assertEqual(operation, "salvar as configurações")
        self.assertFalse(self.path.exists())

    def test_cancel_does_not_change_settings(self):
        self.go_to_memory()
        self.form.set_text("2048")
        self.form.buttons[1].action()
        self.assertEqual(self.manager.settings, Settings())
        self.assertEqual(self.manager.popped, 1)
        self.assertEqual(self.manager.announcer.messages, [])
        self.assertFalse(self.path.exists())


class StartupSettingsTests(TemporaryFileTestCase):
    def test_first_run_uses_defaults_silently(self):
        load_startup_settings(self.manager, self.path)
        self.assertEqual(self.manager.settings, Settings())
        self.assertTrue(self.manager.sounds.enabled)
        self.assertEqual(self.manager.announcer.errors, [])

    def test_saved_values_are_applied(self):
        save_settings(Settings(memory_mb=512, disable_sounds=True, disable_tips=True), self.path)
        load_startup_settings(self.manager, self.path)
        self.assertEqual(self.manager.settings.memory_mb, 512)
        self.assertTrue(self.manager.settings.disable_tips)
        self.assertFalse(self.manager.sounds.enabled)
        self.assertEqual(self.manager.announcer.errors, [])

    def test_tampered_file_is_reported(self):
        save_settings(Settings(memory_mb=512), self.path)
        content = decoded(self.path)
        content["configuracoes"]["memory_mb"] = 4096
        self.path.write_bytes(encode(content))
        with self.assertLogs("src.models.settings_store", "WARNING"):
            load_startup_settings(self.manager, self.path)
        self.assertEqual(self.manager.settings, Settings())
        self.assertEqual(self.manager.announcer.errors, [(TAMPERED_MESSAGE, "carregar as configurações")])

    def test_unreadable_file_is_reported(self):
        save_settings(Settings(memory_mb=512), self.path)
        with mock.patch.object(Path, "open", side_effect=PermissionError(13, "negado")), \
                self.assertLogs("src.models.settings_store", "WARNING"):
            load_startup_settings(self.manager, self.path)
        self.assertEqual(self.manager.settings, Settings())
        self.assertEqual(self.manager.announcer.errors, [(UNREADABLE_MESSAGE, "carregar as configurações")])

    def test_corrected_value_is_not_reported(self):
        save_settings(Settings(), self.path)
        content = decoded(self.path)
        content["configuracoes"].pop("disable_tips")
        content["verificacao"] = signature(content["configuracoes"])
        self.path.write_bytes(encode(content))
        with self.assertLogs("src.models.settings_store", "WARNING"):
            load_startup_settings(self.manager, self.path)
        self.assertEqual(self.manager.settings, Settings())
        self.assertEqual(self.manager.announcer.errors, [])


if __name__ == "__main__":
    unittest.main()
