import unittest

from src.controllers.menu_model import Menu, MenuItem
from src.controllers.menu_navigator import MenuNavigator


def noop() -> None:
    pass


def make_menu(state: dict) -> Menu:
    return Menu(
        "Teste",
        [
            MenuItem("A", "Abrir", noop),
            MenuItem("E", "Editar", noop, available=lambda: state["file_open"]),
            MenuItem("S", "Sair", noop),
        ],
    )


class NavigatorTests(unittest.TestCase):
    def setUp(self):
        self.state = {"file_open": False}
        self.nav = MenuNavigator(make_menu(self.state))

    def test_starts_on_first_visible_item(self):
        self.assertEqual(self.nav.current().key, "A")

    def test_move_up_stops_at_first(self):
        self.assertFalse(self.nav.move_up())
        self.assertEqual(self.nav.current().key, "A")

    def test_move_down_stops_at_last(self):
        self.assertTrue(self.nav.move_down())
        self.assertFalse(self.nav.move_down())
        self.assertEqual(self.nav.current().key, "S")

    def test_select_by_key_ignores_case(self):
        item = self.nav.select_by_key("s")
        self.assertEqual(item.key, "S")
        self.assertEqual(self.nav.current().key, "S")

    def test_hidden_item_cannot_be_selected_by_key(self):
        self.assertIsNone(self.nav.select_by_key("E"))
        self.assertEqual(self.nav.current().key, "A")

    def test_unknown_key_keeps_selection(self):
        self.nav.move_down()
        self.assertIsNone(self.nav.select_by_key("Z"))
        self.assertEqual(self.nav.current().key, "S")

    def test_refresh_keeps_same_item_when_options_appear(self):
        self.nav.select_by_key("S")
        self.state["file_open"] = True
        self.nav.refresh()
        self.assertEqual(self.nav.current().key, "S")
        self.assertEqual([i.key for i in self.nav.items], ["A", "E", "S"])

    def test_refresh_stays_in_bounds_when_current_item_disappears(self):
        self.state["file_open"] = True
        self.nav.refresh()
        self.nav.select_by_key("E")
        self.state["file_open"] = False
        self.nav.refresh()
        self.assertIsNotNone(self.nav.current())
        self.assertNotEqual(self.nav.current().key, "E")

    def test_select_index_valid(self):
        self.assertTrue(self.nav.select_index(1))
        self.assertEqual(self.nav.current().key, "S")

    def test_select_index_out_of_range_keeps_selection(self):
        for index in (-1, 2, 99):
            with self.subTest(index=index):
                self.assertFalse(self.nav.select_index(index))
                self.assertEqual(self.nav.current().key, "A")

    def test_menu_with_no_visible_items(self):
        menu = Menu("Vazio", [MenuItem("E", "Editar", noop, available=lambda: False)])
        nav = MenuNavigator(menu)
        self.assertIsNone(nav.current())
        self.assertIsNone(nav.index)
        self.assertFalse(nav.move_down())
        self.assertFalse(nav.move_up())


if __name__ == "__main__":
    unittest.main()
