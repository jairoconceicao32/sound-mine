import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

SOURCE_SETTINGS = "settings"
SOURCE_ASKED = "asked"
SOURCE_FIXED = "fixed"
SOURCES = (SOURCE_SETTINGS, SOURCE_ASKED, SOURCE_FIXED)
CHANNELS = 2
IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*")

ProcessFunction = Callable[[np.ndarray, int, Mapping[str, int]], np.ndarray]


class EffectDefinitionError(ValueError):
    pass


def _is_identifier(value: object) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True)
class EffectParameter:
    name: str
    label: str
    minimum: int
    maximum: int
    default: int
    source: str

    def __post_init__(self) -> None:
        if not _is_identifier(self.name):
            raise EffectDefinitionError(f"Nome de parâmetro inválido: {self.name!r}.")
        if not _is_text(self.label):
            raise EffectDefinitionError(f"O parâmetro {self.name!r} não tem rótulo.")
        if any(type(value) is not int for value in (self.minimum, self.maximum, self.default)):
            raise EffectDefinitionError(f"Os limites do parâmetro {self.name!r} devem ser inteiros.")
        if not self.minimum <= self.default <= self.maximum:
            raise EffectDefinitionError(f"O padrão do parâmetro {self.name!r} está fora dos limites.")
        if self.source not in SOURCES:
            raise EffectDefinitionError(f"Origem inválida para o parâmetro {self.name!r}: {self.source!r}.")

    def accepts(self, value: object) -> bool:
        return type(value) is int and self.minimum <= value <= self.maximum


@dataclass(frozen=True)
class EffectSpec:
    effect_id: str
    label: str
    key: str
    family: str | None
    uses_selection: bool
    parameters: tuple[EffectParameter, ...]
    help_text: str
    process: ProcessFunction
    adds_tail: bool = False

    def __post_init__(self) -> None:
        if type(self.adds_tail) is not bool:
            raise EffectDefinitionError(f"A cauda do efeito {self.effect_id!r} deve ser verdadeira ou falsa.")
        if not _is_identifier(self.effect_id):
            raise EffectDefinitionError(f"Identificador de efeito inválido: {self.effect_id!r}.")
        if not _is_text(self.label):
            raise EffectDefinitionError(f"O efeito {self.effect_id!r} não tem nome.")
        if not isinstance(self.key, str) or len(self.key) != 1 or not self.key.isalnum():
            raise EffectDefinitionError(f"Letra inválida para o efeito {self.effect_id!r}: {self.key!r}.")
        if self.family is not None and not _is_identifier(self.family):
            raise EffectDefinitionError(f"Família inválida para o efeito {self.effect_id!r}: {self.family!r}.")
        if type(self.uses_selection) is not bool:
            raise EffectDefinitionError(f"O uso da seleção do efeito {self.effect_id!r} deve ser verdadeiro ou falso.")
        parameters = tuple(self.parameters)
        if not all(isinstance(parameter, EffectParameter) for parameter in parameters):
            raise EffectDefinitionError(f"Os parâmetros do efeito {self.effect_id!r} são inválidos.")
        names = [parameter.name for parameter in parameters]
        if len(names) != len(set(names)):
            raise EffectDefinitionError(f"O efeito {self.effect_id!r} tem parâmetros repetidos.")
        if not _is_text(self.help_text):
            raise EffectDefinitionError(f"O efeito {self.effect_id!r} não tem texto de ajuda.")
        if not callable(self.process):
            raise EffectDefinitionError(f"O efeito {self.effect_id!r} não tem uma função de processamento válida.")
        object.__setattr__(self, "key", self.key.upper())
        object.__setattr__(self, "parameters", parameters)

    def parameter(self, name: str) -> EffectParameter | None:
        return next((parameter for parameter in self.parameters if parameter.name == name), None)
