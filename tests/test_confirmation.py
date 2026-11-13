import unittest

from src.controllers.confirmation import Confirmation, ConfirmationError, ConfirmOption, yes_no


def noop() -> None:
    pass


def yes() -> None:
    pass


def no() -> None:
    pass


def three_options() -> Confirmation:
    return Confirmation(
        title="Sair",
        question="O que deseja fazer?",
        options=(
            ConfirmOption("Salvar e sair", noop),
            ConfirmOption("Sair sem salvar", noop),
            ConfirmOption("Cancelar", noop),
        ),
        on_cancel=noop,
    )


class YesNoTests(unittest.TestCase):
    def build(self, **changes) -> Confirmation:
        values = {
            "title": "Teste",
            "question": "Deseja continuar?",
            "on_yes": yes,
            "on_no": no,
            "on_cancel": noop,
        }
        values.update(changes)
        return yes_no(**values)

    def test_options_are_only_yes_and_no_in_full(self):
        self.assertEqual(self.build().labels, ("Sim", "Não"))

    def test_initial_option_follows_default(self):
        self.assertEqual(self.build().initial_index, 0)
        self.assertEqual(self.build(default_yes=False).initial_index, 1)

    def test_action_maps_index_to_answer(self):
        confirmation = self.build()
        self.assertIs(confirmation.action(0), yes)
        self.assertIs(confirmation.action(1), no)

    def test_letter_finds_option_ignoring_case(self):
        confirmation = self.build()
        self.assertEqual(confirmation.index_for_key("S"), 0)
        self.assertEqual(confirmation.index_for_key("n"), 1)

    def test_same_letter_keeps_unique_option(self):
        self.assertEqual(self.build().index_for_key("S", current=0), 0)

    def test_other_letters_find_nothing(self):
        for key in ("A", "", "SN", None):
            with self.subTest(key=key):
                self.assertIsNone(self.build().index_for_key(key))

    def test_rejects_invalid_index(self):
        for index in (-1, 2):
            with self.subTest(index=index), self.assertRaises(ConfirmationError):
                self.build().action(index)

    def test_rejects_empty_texts(self):
        for name in ("title", "question"):
            with self.subTest(name=name), self.assertRaises(ConfirmationError):
                self.build(**{name: "  "})

    def test_rejects_non_callable_actions(self):
        for name in ("on_yes", "on_no", "on_cancel"):
            with self.subTest(name=name), self.assertRaises(ConfirmationError):
                self.build(**{name: None})


class ConfirmationTests(unittest.TestCase):
    def test_keeps_options_in_order(self):
        self.assertEqual(three_options().labels, ("Salvar e sair", "Sair sem salvar", "Cancelar"))

    def test_repeated_letter_cycles_through_options_with_same_initial(self):
        confirmation = three_options()
        self.assertEqual(confirmation.index_for_key("S", current=0), 1)
        self.assertEqual(confirmation.index_for_key("S", current=1), 0)
        self.assertEqual(confirmation.index_for_key("S", current=2), 0)
        self.assertEqual(confirmation.index_for_key("C", current=0), 2)

    def test_letter_without_option_finds_nothing(self):
        self.assertIsNone(three_options().index_for_key("N", current=0))

    def test_requires_at_least_two_options(self):
        with self.assertRaises(ConfirmationError):
            Confirmation("Teste", "Pergunta?", (ConfirmOption("Sim", noop),), noop)

    def test_rejects_invalid_initial_option(self):
        options = (ConfirmOption("Sim", noop), ConfirmOption("Não", noop))
        for index in (-1, 2):
            with self.subTest(index=index), self.assertRaises(ConfirmationError):
                Confirmation("Teste", "Pergunta?", options, noop, initial_index=index)

    def test_rejects_invalid_option(self):
        for label, action in (("  ", noop), ("Sim", None)):
            with self.subTest(label=label), self.assertRaises(ConfirmationError):
                ConfirmOption(label, action)


if __name__ == "__main__":
    unittest.main()
