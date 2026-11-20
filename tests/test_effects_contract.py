import unittest

import numpy as np

from src.models.effects.catalog import EFFECTS, check_catalog, find_effect
from src.models.effects.contract import (
    SOURCE_ASKED,
    SOURCE_FIXED,
    SOURCE_SETTINGS,
    EffectDefinitionError,
    EffectParameter,
    EffectSpec,
)


def same(data: np.ndarray, rate: int, parameters) -> np.ndarray:
    return data.copy()


def parameter(**changes) -> EffectParameter:
    values = dict(name="duracao", label="Duração", minimum=1, maximum=60, default=5, source=SOURCE_ASKED)
    values.update(changes)
    return EffectParameter(**values)


def effect(**changes) -> EffectSpec:
    values = dict(effect_id="teste", label="Teste", key="t", family=None, uses_selection=True,
                  parameters=(), help_text="Efeito de teste.", process=same)
    values.update(changes)
    return EffectSpec(**values)


class EffectParameterTests(unittest.TestCase):
    def test_accepts_only_integers_inside_limits(self):
        duration = parameter()
        self.assertTrue(duration.accepts(1))
        self.assertTrue(duration.accepts(60))
        for value in (0, 61, 5.0, "5", True, None):
            with self.subTest(value=value):
                self.assertFalse(duration.accepts(value))

    def test_rejects_invalid_definitions(self):
        cases = [
            dict(name=""),
            dict(name="Duração"),
            dict(label="  "),
            dict(minimum=1.5),
            dict(default=True),
            dict(default=0),
            dict(minimum=10, maximum=5, default=7),
            dict(source="arquivo"),
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(EffectDefinitionError):
                parameter(**changes)

    def test_all_sources_are_accepted(self):
        for source in (SOURCE_SETTINGS, SOURCE_ASKED, SOURCE_FIXED):
            with self.subTest(source=source):
                self.assertEqual(parameter(source=source).source, source)


class EffectSpecTests(unittest.TestCase):
    def test_key_is_stored_in_uppercase(self):
        self.assertEqual(effect(key="e").key, "E")

    def test_parameters_become_a_tuple(self):
        spec = effect(parameters=[parameter()])
        self.assertIsInstance(spec.parameters, tuple)
        self.assertEqual(spec.parameter("duracao").default, 5)
        self.assertIsNone(spec.parameter("outro"))

    def test_rejects_invalid_definitions(self):
        cases = [
            dict(effect_id="Eco"),
            dict(effect_id=""),
            dict(label=""),
            dict(key="ab"),
            dict(key="-"),
            dict(family="Família"),
            dict(uses_selection=1),
            dict(parameters=("duracao",)),
            dict(parameters=(parameter(), parameter())),
            dict(help_text=" "),
            dict(process=None),
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(EffectDefinitionError):
                effect(**changes)


class CatalogTests(unittest.TestCase):
    def test_official_catalog_is_valid(self):
        self.assertEqual(check_catalog(EFFECTS), EFFECTS)
        for spec in EFFECTS:
            with self.subTest(effect=spec.effect_id):
                self.assertIsInstance(spec, EffectSpec)

    def test_new_effect_is_accepted_without_specific_rules(self):
        catalog = check_catalog((effect(), effect(effect_id="outro", key="o", family="eco")))
        self.assertEqual(find_effect("outro", catalog).family, "eco")
        self.assertIsNone(find_effect("inexistente", catalog))

    def test_repeated_identifier_is_refused(self):
        with self.assertRaises(EffectDefinitionError):
            check_catalog((effect(), effect(key="o")))

    def test_repeated_key_is_refused(self):
        with self.assertRaises(EffectDefinitionError):
            check_catalog((effect(), effect(effect_id="outro", key="T")))

    def test_only_effects_are_accepted(self):
        with self.assertRaises(EffectDefinitionError):
            check_catalog(("eco",))


if __name__ == "__main__":
    unittest.main()
