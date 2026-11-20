from collections.abc import Iterable

from src.models.effects.contract import EffectDefinitionError, EffectSpec
from src.models.effects.echo import ECHO, SUPER_ECHO
from src.models.effects.fade import FADE_IN, FADE_OUT
from src.models.effects.reverb import REVERB


def check_catalog(effects: Iterable[EffectSpec]) -> tuple[EffectSpec, ...]:
    effects = tuple(effects)
    ids: set[str] = set()
    keys: dict[str, str] = {}
    for effect in effects:
        if not isinstance(effect, EffectSpec):
            raise EffectDefinitionError("O catálogo só pode conter efeitos.")
        if effect.effect_id in ids:
            raise EffectDefinitionError(f"Efeito repetido no catálogo: {effect.effect_id!r}.")
        if effect.key in keys:
            raise EffectDefinitionError(
                f"Letra {effect.key!r} repetida no catálogo: {keys[effect.key]!r} e {effect.effect_id!r}."
            )
        ids.add(effect.effect_id)
        keys[effect.key] = effect.effect_id
    return effects


EFFECTS: tuple[EffectSpec, ...] = check_catalog((FADE_IN, FADE_OUT, ECHO, SUPER_ECHO, REVERB))


def find_effect(effect_id: str, effects: Iterable[EffectSpec] = EFFECTS) -> EffectSpec | None:
    return next((effect for effect in effects if effect.effect_id == effect_id), None)
