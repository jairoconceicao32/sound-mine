import unittest

from src.controllers.background_form import build_background_form
from src.controllers.settings import ButtonField, NumberField


class BackgroundFormTests(unittest.TestCase):
    def setUp(self):
        self.applied = []
        self.cancelled = []
        self.form = build_background_form(
            "Fundo sonoro no cursor",
            lambda main, background: self.applied.append((main, background)),
            lambda: self.cancelled.append(True),
        )

    def test_has_two_sliders_and_two_buttons_without_tab_selector(self):
        fields = self.form.fields
        self.assertEqual(len(fields), 4)
        self.assertTrue(all(isinstance(field, NumberField) and field.slider for field in fields[:2]))
        self.assertTrue(all(isinstance(field, ButtonField) for field in fields[2:]))
        self.assertEqual(fields[0].label, "Volume do áudio original")
        self.assertEqual(fields[1].label, "Volume da música de fundo")

    def test_default_volumes(self):
        self.assertEqual(self.form.values["main_volume"], 100)
        self.assertEqual(self.form.values["background_volume"], 30)

    def test_tab_moves_through_fields_without_wrapping(self):
        self.assertTrue(self.form.next_field())
        self.assertTrue(self.form.next_field())
        self.assertTrue(self.form.next_field())
        self.assertFalse(self.form.next_field())
        self.assertEqual(self.form.current().label, "Cancelar")

    def test_confirm_sends_chosen_volumes(self):
        self.form.next_field()
        self.form.set_text("45")
        self.form.next_field()
        self.form.current().action()
        self.assertEqual(self.applied, [(100, 45)])

    def test_cancel(self):
        self.form.fields[3].action()
        self.assertEqual(self.cancelled, [True])
        self.assertEqual(self.applied, [])


if __name__ == "__main__":
    unittest.main()
