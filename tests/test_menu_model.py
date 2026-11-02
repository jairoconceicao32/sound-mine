import unittest

from src.controllers.menu_model import LetterMode, Menu, MenuDefinitionError, MenuItem


def noop() -> None:
    pass


class MenuItemTests(unittest.TestCase):
    def test_display_text_shows_key_and_label(self):
        item = MenuItem("a", "Abrir arquivo", noop)
        self.assertEqual(item.display_text, "A - Abrir arquivo")

    def test_rejects_invalid_key(self):
        for key in ("", "AB", " ", "-"):
            with self.subTest(key=key), self.assertRaises(MenuDefinitionError):
                MenuItem(key, "Opção", noop)

    def test_rejects_empty_label(self):
        with self.assertRaises(MenuDefinitionError):
            MenuItem("A", "   ", noop)

    def test_rejects_non_callable_action(self):
        with self.assertRaises(MenuDefinitionError):
            MenuItem("A", "Abrir arquivo", None)

    def test_availability_error_hides_item(self):
        def broken() -> bool:
            raise RuntimeError("falha")

        item = MenuItem("E", "Editar", noop, available=broken)
        self.assertFalse(item.is_available())


class MenuTests(unittest.TestCase):
    def test_rejects_duplicate_keys_ignoring_case(self):
        with self.assertRaises(MenuDefinitionError):
            Menu("Teste", [MenuItem("a", "Abrir", noop), MenuItem("A", "Ajuda", noop)])

    def test_rejects_menu_without_items(self):
        with self.assertRaises(MenuDefinitionError):
            Menu("Teste", [])

    def test_rejects_empty_title(self):
        with self.assertRaises(MenuDefinitionError):
            Menu(" ", [MenuItem("A", "Abrir", noop)])

    def test_default_letter_mode_is_select(self):
        menu = Menu("Teste", [MenuItem("A", "Abrir", noop)])
        self.assertIs(menu.letter_mode, LetterMode.SELECT)

    def test_editor_menu_can_use_activate_mode(self):
        menu = Menu("Editor", [MenuItem("T", "Tocar", noop)], LetterMode.ACTIVATE)
        self.assertIs(menu.letter_mode, LetterMode.ACTIVATE)

    def test_visible_items_hides_unavailable(self):
        menu = Menu(
            "Teste",
            [
                MenuItem("A", "Abrir", noop),
                MenuItem("E", "Editar", noop, available=lambda: False),
                MenuItem("S", "Sair", noop),
            ],
        )
        self.assertEqual([i.key for i in menu.visible_items()], ["A", "S"])

    def test_opening_message_defaults_to_title(self):
        menu = Menu("Configurações", [MenuItem("I", "Idioma", noop)])
        self.assertEqual(menu.opening_message, "Configurações")

    def test_opening_message_uses_intro(self):
        menu = Menu("Menu principal", [MenuItem("A", "Abrir", noop)], intro="Use as setas.")
        self.assertEqual(menu.opening_message, "Use as setas.")

    def test_help_is_disabled_by_default(self):
        menu = Menu("Menu principal", [MenuItem("A", "Abrir", noop)])
        self.assertFalse(menu.has_help)

    def test_select_mode_shows_label_without_key(self):
        item = MenuItem("A", "Abrir arquivo", noop)
        menu = Menu("Teste", [item])
        self.assertEqual(menu.item_text(item), "Abrir arquivo")

    def test_activate_mode_shows_key_and_label(self):
        item = MenuItem("T", "Tocar arquivo", noop)
        menu = Menu("Editor", [item], LetterMode.ACTIVATE)
        self.assertEqual(menu.item_text(item), "T - Tocar arquivo")


if __name__ == "__main__":
    unittest.main()
