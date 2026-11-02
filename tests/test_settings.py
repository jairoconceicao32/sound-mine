import unittest

from src.controllers.settings import (
    ButtonField,
    NumberField,
    OptionField,
    SettingsDefinitionError,
    SettingsForm,
    SettingsTab,
    ToggleField,
)


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


if __name__ == "__main__":
    unittest.main()
