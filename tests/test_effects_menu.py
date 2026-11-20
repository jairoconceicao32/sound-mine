import unittest

import numpy as np
import wx

from src.controllers import effects_menu
from src.controllers.effect_form import CONFIRM_LABEL
from src.models.effects import fade, volume
from src.models.effects.catalog import EFFECTS
from src.view.confirm_screen import ConfirmScreen
from src.view.editor_screen import EditorScreen
from src.view.preview_screen import PreviewScreen
from src.view.settings_screen import SettingsScreen
from tests.test_effect_preview import RATE, SECONDS, make_player
from tests.test_exit_flow import ScreenFlowCase, flush

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


class EffectsMenuTests(ScreenFlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.player = make_player(self)
        self.original = self.player.data
        self.menu = effects_menu.build_effects_menu(self.manager, self.player)
        self.screen = EditorScreen(self.manager.parent, self.manager, self.menu, self.player)
        self.manager.push(self.screen)
        flush()
        self.log.clear()

    def apply_preview(self) -> None:
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.press(wx.WXK_ESCAPE)
        self.assertIsInstance(self.manager.current, ConfirmScreen)
        self.press(wx.WXK_RETURN)
        flush()

    def confirm_form(self, **values) -> SettingsScreen:
        screen = self.manager.current
        self.assertIsInstance(screen, SettingsScreen)
        screen._form._values.update(values)
        next(button for button in screen._form.buttons if button.label == CONFIRM_LABEL).action()
        flush()
        return screen

    def test_items_follow_the_official_order_and_letters(self):
        self.assertEqual(
            [(item.key, item.label) for item in self.menu.items],
            [("A", "Aumentar o volume"), ("D", "Diminuir o volume"), ("I", "Fade in"), ("O", "Fade out"),
             ("E", "Eco"), ("S", "Super eco"), ("R", "Reverberação"), ("X", "Super reverberação")],
        )

    def test_unavailable_effects_are_announced(self):
        implemented = {effect.key for effect in EFFECTS}
        pending = [(key, label) for key, label in effects_menu.UNAVAILABLE_ITEMS if key not in implemented]
        self.assertEqual(pending, [])
        for key, label in pending:
            with self.subTest(label=label):
                self.letter(key)
                self.assertIn(f"fala: {effects_menu.unavailable_message(label)}", self.log)
                self.assertIs(self.manager.current, self.screen)
        self.assertIs(self.player.data, self.original)

    def test_volume_increase_is_previewed_and_applied(self):
        self.letter("A")
        self.assertIn("fala: Prévia do efeito Aumentar o volume", self.log)
        self.apply_preview()
        np.testing.assert_allclose(self.player.data, self.original * 1.25, rtol=1e-6)
        self.assertTrue(np.all(self.player.levels == 125))
        self.assertIs(self.manager.current, self.screen)

    def test_volume_limit_is_reported(self):
        self.player.edit(lambda data, cursor, marked: (data, cursor),
                         lambda levels, cursor, marked: np.full_like(levels, 25))
        self.letter("D")
        self.assertIn(f"erro [aplicar efeito]: {volume.MIN_MESSAGE}", self.log)
        self.assertIs(self.manager.current, self.screen)

    def test_volume_uses_selection(self):
        self.player.seek(2)
        self.player.mark()
        self.player.seek(6)
        self.letter("A")
        self.apply_preview()
        levels = self.player.levels
        self.assertTrue(np.all(levels[:2 * RATE] == 100))
        self.assertTrue(np.all(levels[3 * RATE:5 * RATE] == 125))
        self.assertTrue(np.all(levels[6 * RATE:] == 100))

    def test_fade_asks_duration_then_previews_and_applies(self):
        self.letter("I")
        form = self.manager.current
        self.assertIsInstance(form, SettingsScreen)
        self.assertEqual(form._form.values, {fade.DURATION: fade.DURATION_DEFAULT})
        self.confirm_form(duracao=2)
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.apply_preview()
        self.assertEqual(float(self.player.data[0, 0]), 0.0)
        np.testing.assert_array_equal(self.player.data[2 * RATE:], self.original[2 * RATE:])
        self.assertIs(self.manager.current, self.screen)

    def test_fade_duration_longer_than_audio_keeps_form_open(self):
        self.letter("O")
        form = self.confirm_form(duracao=SECONDS + 1)
        self.assertIn(f"erro [aplicar efeito]: {fade.TOO_LONG[0]} {fade.TOO_LONG[1]}", self.log)
        self.assertIs(self.manager.current, form)
        self.assertFalse(self.player.previewing)
        self.confirm_form(duracao=3)
        self.assertIsInstance(self.manager.current, PreviewScreen)

    def test_cancelling_form_returns_to_menu(self):
        self.letter("I")
        form = self.manager.current
        next(button for button in form._form.buttons if button.label != CONFIRM_LABEL).action()
        flush()
        self.assertIs(self.manager.current, self.screen)
        self.assertIs(self.player.data, self.original)


if __name__ == "__main__":
    unittest.main()
