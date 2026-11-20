import unittest

import numpy as np

from src.models.effects import engine
from src.models.effects.contract import SOURCE_ASKED, SOURCE_FIXED, SOURCE_SETTINGS, EffectParameter, EffectSpec
from src.models.effects.errors import EffectError

RATE = 48000


def frames(count: int) -> np.ndarray:
    values = np.linspace(-0.5, 0.5, count, dtype=np.float32)
    return np.column_stack((values, values))


def halve(data: np.ndarray, rate: int, parameters) -> np.ndarray:
    return data * np.float32(0.5)


def effect(process=halve, parameters=()) -> EffectSpec:
    return EffectSpec(effect_id="teste", label="Teste", key="T", family=None, uses_selection=True,
                      parameters=parameters, help_text="Efeito de teste.", process=process)


class SelectionTests(unittest.TestCase):
    def test_without_marked_point_uses_whole_audio(self):
        self.assertEqual(engine.selection(100, 40, None), (0, 100))

    def test_marked_point_at_cursor_uses_whole_audio(self):
        self.assertEqual(engine.selection(100, 40, 40), (0, 100))

    def test_order_does_not_matter(self):
        self.assertEqual(engine.selection(100, 20, 70), (20, 70))
        self.assertEqual(engine.selection(100, 70, 20), (20, 70))

    def test_positions_outside_audio_are_refused(self):
        for cursor, marked in ((-1, None), (101, None), (10, 101), (10, -1)):
            with self.subTest(cursor=cursor, marked=marked), self.assertRaises(EffectError):
                engine.selection(100, cursor, marked)


class ParameterValidationTests(unittest.TestCase):
    def setUp(self):
        self.effect = effect(parameters=(
            EffectParameter("duracao", "Duração", 1, 60, 5, SOURCE_ASKED),
            EffectParameter("atraso", "Atraso", 10, 2000, 300, SOURCE_SETTINGS),
            EffectParameter("fixo", "Fixo", 0, 10, 3, SOURCE_FIXED),
        ))

    def test_valid_values_are_returned_read_only(self):
        values = engine.validate_parameters(self.effect, {"duracao": 5, "atraso": 300})
        self.assertEqual(dict(values), {"duracao": 5, "atraso": 300, "fixo": 3})
        with self.assertRaises(TypeError):
            values["duracao"] = 10

    def test_fixed_parameter_always_uses_default(self):
        values = engine.validate_parameters(self.effect, {"duracao": 5, "atraso": 300, "fixo": 9})
        self.assertEqual(values["fixo"], 3)

    def test_invalid_values_are_refused(self):
        cases = [
            {"atraso": 300},
            {"duracao": 0, "atraso": 300},
            {"duracao": 61, "atraso": 300},
            {"duracao": 5.0, "atraso": 300},
            {"duracao": "5", "atraso": 300},
            {"duracao": True, "atraso": 300},
            {"duracao": 5, "atraso": 9},
            {"duracao": 5, "atraso": 300, "outro": 1},
        ]
        for values in cases:
            with self.subTest(values=values), self.assertLogs(engine.logger, level="WARNING"):
                with self.assertRaises(EffectError):
                    engine.validate_parameters(self.effect, values)


class RunTests(unittest.TestCase):
    def test_whole_audio_is_processed(self):
        data = frames(10)
        candidate = engine.run(effect(), data, RATE, 0, 10, {})
        np.testing.assert_array_equal(candidate, data * np.float32(0.5))

    def test_audio_outside_selection_is_preserved(self):
        data = frames(10)
        candidate = engine.run(effect(), data, RATE, 3, 7, {})
        np.testing.assert_array_equal(candidate[:3], data[:3])
        np.testing.assert_array_equal(candidate[7:], data[7:])
        np.testing.assert_array_equal(candidate[3:7], data[3:7] * np.float32(0.5))

    def test_input_is_not_changed(self):
        data = frames(10)
        original = data.copy()
        engine.run(effect(), data, RATE, 2, 8, {})
        np.testing.assert_array_equal(data, original)

    def test_effect_receives_read_only_copy(self):
        def change_in_place(chunk, rate, parameters):
            chunk *= 2
            return chunk

        data = frames(10)
        original = data.copy()
        with self.assertLogs(engine.logger, level="ERROR"), self.assertRaises(EffectError):
            engine.run(effect(change_in_place), data, RATE, 0, 10, {})
        np.testing.assert_array_equal(data, original)

    def test_effect_receives_rate_and_parameters(self):
        received = {}

        def record(chunk, rate, parameters):
            received.update(rate=rate, parameters=dict(parameters), length=len(chunk))
            return chunk.copy()

        spec = effect(record, (EffectParameter("duracao", "Duração", 1, 60, 5, SOURCE_ASKED),))
        engine.run(spec, frames(10), RATE, 2, 6, {"duracao": 7})
        self.assertEqual(received, {"rate": RATE, "parameters": {"duracao": 7}, "length": 4})

    def test_invalid_results_are_refused(self):
        def nan(chunk, rate, parameters):
            result = chunk.copy()
            result[0, 0] = np.nan
            return result

        def infinite(chunk, rate, parameters):
            result = chunk.copy()
            result[-1, 1] = np.inf
            return result

        results = {
            "nan": nan,
            "infinito": infinite,
            "duração": lambda chunk, rate, parameters: chunk[:-1].copy(),
            "canais": lambda chunk, rate, parameters: chunk[:, :1].copy(),
            "tipo": lambda chunk, rate, parameters: chunk.astype(np.float64),
            "não array": lambda chunk, rate, parameters: chunk.tolist(),
            "nada": lambda chunk, rate, parameters: None,
        }
        for name, process in results.items():
            data = frames(10)
            original = data.copy()
            with self.subTest(result=name):
                with self.assertLogs(engine.logger, level="WARNING"), self.assertRaises(EffectError):
                    engine.run(effect(process), data, RATE, 0, 10, {})
                np.testing.assert_array_equal(data, original)

    def test_effect_exception_becomes_internal_error(self):
        def broken(chunk, rate, parameters):
            raise RuntimeError("falha")

        with self.assertLogs(engine.logger, level="ERROR"):
            with self.assertRaises(EffectError):
                engine.run(effect(broken), frames(10), RATE, 0, 10, {})

    def test_invalid_input_is_refused(self):
        data = frames(10)
        cases = [
            (data.astype(np.float64), RATE, 0, 10),
            (data[:, :1].copy(), RATE, 0, 10),
            (data, 0, 0, 10),
            (data, 48000.0, 0, 10),
            (data, RATE, 5, 5),
            (data, RATE, 6, 4),
            (data, RATE, -1, 4),
            (data, RATE, 0, 11),
        ]
        for audio, rate, start, end in cases:
            with self.subTest(rate=rate, start=start, end=end), self.assertRaises(EffectError):
                engine.run(effect(), audio, rate, start, end, {})


if __name__ == "__main__":
    unittest.main()
