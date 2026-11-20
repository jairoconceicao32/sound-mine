import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import wx

from src.controllers import effects_menu
from src.models import audio_player
from src.models.audio_edit import EditError
from src.models.audio_player import (
    SUBSTITUTION_NO_DATA,
    SUBSTITUTION_NONE,
    SUBSTITUTION_NOT_LAST,
    SUBSTITUTION_READY,
)
from src.models.effects.contract import EffectSpec
from src.view.confirm_screen import ConfirmScreen
from src.view.editor_screen import EditorScreen
from src.view.preview_screen import PreviewScreen
from tests.test_effect_preview import RATE, make_player
from tests.test_exit_flow import ScreenFlowCase, flush

_app: wx.App | None = None


def setUpModule() -> None:
    global _app
    _app = wx.GetApp() or wx.App(False)


def multiply(factor: float):
    return lambda chunk, rate, parameters: chunk * np.float32(factor)


ECHO = EffectSpec("eco", "Eco", "E", "eco", True, (), "Eco de teste.", multiply(1.5))
SUPER_ECHO = EffectSpec("super_eco", "Super eco", "S", "eco", True, (), "Super eco de teste.", multiply(2.0))
REVERB = EffectSpec("reverberacao", "Reverberação", "R", "reverberacao", True, (), "Reverberação de teste.",
                    multiply(1.2))


def save(player) -> None:
    with mock.patch.object(audio_player, "save_audio", return_value=RATE):
        player.save(Path("musica_editado.wav"), "wav", "Estéreo", RATE)


class PlayerRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.player = make_player(self)
        self.original = self.player.data

    def apply(self, factor: float, family: str | None = "eco", effect_id: str | None = "eco",
              replacing: bool = False) -> None:
        base = self.player.before_effect(family)[0] if replacing else self.player.data
        self.player.apply_effect(base * np.float32(factor), None, family, effect_id, replacing)

    def test_no_family_registered_at_start(self):
        self.assertEqual(self.player.effects, {})
        self.assertEqual(self.player.substitution("eco"), SUBSTITUTION_NONE)

    def test_effect_with_family_is_registered_and_ready_for_substitution(self):
        self.apply(1.5)
        self.assertEqual(self.player.effects, {"eco": "eco"})
        self.assertEqual(self.player.substitution("eco"), SUBSTITUTION_READY)
        self.assertEqual(self.player.substitution("reverberacao"), SUBSTITUTION_NONE)

    def test_substitution_does_not_stack(self):
        self.apply(1.5)
        self.apply(2.0, effect_id="super_eco", replacing=True)
        np.testing.assert_allclose(self.player.data, self.original * 2.0, rtol=1e-6)
        self.assertEqual(self.player.effects, {"eco": "super_eco"})
        self.apply(1.5, replacing=True)
        np.testing.assert_allclose(self.player.data, self.original * 1.5, rtol=1e-6)

    def test_substitution_preserves_changes_before_the_effect(self):
        self.apply(1.2, "reverberacao", "reverberacao")
        before = self.player.data
        self.apply(1.5)
        self.apply(2.0, effect_id="super_eco", replacing=True)
        np.testing.assert_allclose(self.player.data, before * 2.0, rtol=1e-6)
        self.assertEqual(self.player.effects, {"reverberacao": "reverberacao", "eco": "super_eco"})

    def test_any_later_change_blocks_substitution(self):
        changes = {
            "edição": lambda: self.player.edit(lambda data, cursor, marked: (data, cursor)),
            "efeito sem família": lambda: self.apply(0.5, None, None),
            "outra família": lambda: self.apply(1.2, "reverberacao", "reverberacao"),
        }
        for name, change in changes.items():
            with self.subTest(change=name):
                self.player.undo()
                self.apply(1.5)
                change()
                self.assertEqual(self.player.substitution("eco"), SUBSTITUTION_NOT_LAST)
                with self.assertRaises(EditError):
                    self.player.before_effect("eco")

    def test_removal_keeps_family_registered(self):
        self.apply(1.5)
        self.player.edit(lambda data, cursor, marked: (data[RATE:], 0),
                         lambda levels, cursor, marked: levels[RATE:])
        self.assertEqual(self.player.effects, {"eco": "eco"})

    def test_registry_and_substitution_survive_save(self):
        self.apply(1.5)
        save(self.player)
        self.assertEqual(self.player.effects, {"eco": "eco"})
        self.assertEqual(self.player.substitution("eco"), SUBSTITUTION_READY)

    def test_undo_restores_saved_registry_without_substitution_data(self):
        self.apply(1.5)
        save(self.player)
        self.apply(1.2, "reverberacao", "reverberacao")
        self.player.undo()
        self.assertEqual(self.player.effects, {"eco": "eco"})
        self.assertEqual(self.player.substitution("eco"), SUBSTITUTION_NO_DATA)

    def test_undo_before_any_save_clears_registry(self):
        self.apply(1.5)
        self.player.undo()
        self.assertEqual(self.player.effects, {})

    def test_without_memory_for_the_copy_substitution_has_no_data(self):
        self.player._memory_mb = 1
        self.player._saved = self.player.data[:1]
        self.player.apply_effect(self.player.data[:RATE] * 1.5, np.full(RATE, 100, dtype=np.float32),
                                 "eco", "eco")
        self.assertEqual(self.player.substitution("eco"), SUBSTITUTION_NO_DATA)

    def test_invalid_requests_are_refused(self):
        with self.assertRaises(EditError):
            self.player.apply_effect(self.original, None, "eco", None)
        with self.assertRaises(EditError):
            self.player.apply_effect(self.original, None, "eco", "eco", replacing=True)
        with self.assertRaises(EditError):
            self.player.apply_effect(self.original[:10])


class SubstitutionFlowTests(ScreenFlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.player = make_player(self)
        self.original = self.player.data
        menu = effects_menu.build_effects_menu(self.manager, self.player, (ECHO, SUPER_ECHO, REVERB))
        self.menu_screen = EditorScreen(self.manager.parent, self.manager, menu, self.player)
        self.manager.push(self.menu_screen)
        flush()

    def apply_preview(self) -> None:
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.press(wx.WXK_ESCAPE)
        self.press(wx.WXK_RETURN)
        flush()

    def test_conflict_is_explained_with_cancel_selected(self):
        self.letter("E")
        self.apply_preview()
        self.log.clear()
        self.letter("S")
        screen = self.manager.current
        self.assertIsInstance(screen, ConfirmScreen)
        self.assertEqual(screen.selected, effects_menu.CANCEL_LABEL)
        self.assertIn(f"fala: {effects_menu.conflict_question('Eco', 'Super eco')}", self.log)

    def test_cancel_keeps_previous_effect(self):
        self.letter("E")
        self.apply_preview()
        data = self.player.data
        self.letter("S")
        self.press(wx.WXK_RETURN)
        self.assertIn("fala: Operação cancelada.", self.log)
        self.assertIs(self.player.data, data)
        self.assertIs(self.manager.current, self.menu_screen)

    def test_escape_on_conflict_cancels(self):
        self.letter("E")
        self.apply_preview()
        self.letter("S")
        self.press(wx.WXK_ESCAPE)
        self.assertIn("fala: Operação cancelada.", self.log)
        self.assertEqual(self.player.effects, {"eco": "eco"})

    def test_continue_previews_and_replaces(self):
        self.letter("E")
        self.apply_preview()
        self.letter("S")
        self.press(wx.WXK_UP)
        self.press(wx.WXK_RETURN)
        self.assertIsInstance(self.manager.current, PreviewScreen)
        self.apply_preview()
        np.testing.assert_allclose(self.player.data, self.original * 2.0, rtol=1e-6)
        self.assertEqual(self.player.effects, {"eco": "super_eco"})
        self.assertIs(self.manager.current, self.menu_screen)

    def test_not_applying_the_new_effect_keeps_previous(self):
        self.letter("E")
        self.apply_preview()
        data = self.player.data
        self.letter("S")
        self.press(wx.WXK_UP)
        self.press(wx.WXK_RETURN)
        self.press(wx.WXK_ESCAPE)
        self.press(wx.WXK_DOWN)
        self.press(wx.WXK_RETURN)
        self.assertIs(self.player.data, data)
        self.assertEqual(self.player.effects, {"eco": "eco"})

    def test_same_effect_also_offers_substitution(self):
        self.letter("E")
        self.apply_preview()
        self.letter("E")
        self.assertIsInstance(self.manager.current, ConfirmScreen)

    def test_other_family_is_combined_without_question(self):
        self.letter("E")
        self.apply_preview()
        self.letter("R")
        self.assertIsInstance(self.manager.current, PreviewScreen)

    def test_change_after_effect_reports_reason(self):
        self.letter("E")
        self.apply_preview()
        self.letter("R")
        self.apply_preview()
        self.letter("S")
        error = effects_menu.not_last_error("Eco", "Super eco")
        self.assertIn(f"erro [aplicar efeito]: {error.reason} {error.hint}", self.log)
        self.assertIs(self.manager.current, self.menu_screen)

    def test_missing_data_is_reported(self):
        self.letter("E")
        self.apply_preview()
        save(self.player)
        self.player.undo()
        self.letter("S")
        error = effects_menu.no_data_error("Eco")
        self.assertIn(f"erro [aplicar efeito]: {error.reason} {error.hint}", self.log)

    def test_unavailable_placeholders_are_replaced_by_real_effects(self):
        labels = [item.label for item in self.menu_screen._navigator.menu.items]
        self.assertEqual(labels.count("Eco"), 1)
        self.assertIn("Super reverberação", labels)


if __name__ == "__main__":
    unittest.main()
