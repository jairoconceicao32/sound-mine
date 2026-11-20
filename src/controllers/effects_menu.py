from collections.abc import Callable, Iterable, Mapping

import numpy as np
import wx

from src.controllers.confirmation import Confirmation, ConfirmOption
from src.controllers.editor_exit import CANCELED_MESSAGE
from src.controllers.effect_form import build_effect_form
from src.controllers.effect_preview import open_preview
from src.controllers.menu_model import LetterMode, Menu, MenuItem
from src.models.app_log import operation as log_operation
from src.models.audio_edit import EditError
from src.models.audio_player import SUBSTITUTION_NO_DATA, SUBSTITUTION_NONE, SUBSTITUTION_NOT_LAST
from src.models.effects import engine, volume
from src.models.effects.catalog import EFFECTS, find_effect
from src.models.effects.contract import SOURCE_ASKED, SOURCE_SETTINGS, EffectSpec
from src.models.effects.errors import EffectError
from src.models.errors import APPLY_EFFECT, user_message
from src.view.confirm_screen import ConfirmScreen
from src.view.settings_screen import SettingsScreen

TITLE = "Qual efeito"
QUESTION = "Qual sua opção?"
SUBSTITUTION_TITLE = "Substituir efeito"
CONTINUE_LABEL = "Continuar"
CANCEL_LABEL = "Cancelar"
VOLUME_ITEMS = (
    ("A", "Aumentar o volume", volume.UP),
    ("D", "Diminuir o volume", volume.DOWN),
)
UNAVAILABLE_ITEMS = (
    ("E", "Eco"),
    ("S", "Super eco"),
    ("R", "Reverberação"),
    ("X", "Super reverberação"),
)


def unavailable_message(label: str) -> str:
    return f"O efeito {label} ainda não está disponível."


def conflict_question(previous: str, new: str) -> str:
    return (f"Este áudio já possui o efeito {previous} aplicado. "
            f"Para utilizar {new}, será necessário substituir o efeito existente.")


def not_last_error(previous: str, new: str) -> EffectError:
    return EffectError(f"O efeito {previous} não pode ser substituído, porque o áudio foi alterado depois dele.",
                       f"Para aplicar {new}, desfaça as alterações feitas depois do efeito {previous}.")


def no_data_error(previous: str) -> EffectError:
    return EffectError(f"Não há dados suficientes para substituir o efeito {previous}.",
                       "O áudio foi mantido como está.")


def build_effects_menu(manager, player, effects: Iterable[EffectSpec] = EFFECTS) -> Menu:
    effects = tuple(effects)

    def fail(error: Exception) -> None:
        manager.announcer.error(user_message(error), APPLY_EFFECT, error)

    def label_of(effect_id: str) -> str:
        effect = find_effect(effect_id, effects)
        return effect.label if effect is not None else effect_id

    def selection(length: int | None = None) -> tuple[int, int]:
        length = len(player.data) if length is None else length
        marked = player.marked_frame
        return engine.selection(length, min(player.cursor_frame, length),
                                None if marked is None else min(marked, length))

    def adjust_volume(label: str, direction: str) -> None:
        with log_operation(APPLY_EFFECT):
            try:
                start, end = selection()
                candidate, levels = volume.adjust(player.data, player.levels, player.rate, start, end, direction)
            except EffectError as error:
                fail(error)
                return
        open_preview(manager, player, label, candidate, start, end, levels=levels)

    def process(effect: EffectSpec, values: Mapping[str, int], base: np.ndarray):
        with log_operation(APPLY_EFFECT):
            try:
                start, end = selection(len(base))
                candidate, effect_end = engine.apply(effect, base, player.rate, start, end, values)
            except EffectError as error:
                fail(error)
                return None
        return candidate, start, effect_end

    def run_effect(effect: EffectSpec, replacing: bool) -> None:
        base, base_levels = player.data, player.levels
        if replacing:
            try:
                base, base_levels = player.before_effect(effect.family)
            except EditError as error:
                with log_operation(APPLY_EFFECT):
                    fail(error)
                return

        def preview(result) -> None:
            candidate, start, end = result
            levels = volume.extend_levels(base_levels, len(candidate))
            open_preview(manager, player, effect.label, candidate, start, end, levels=levels,
                         family=effect.family, effect_id=effect.effect_id if effect.family else None,
                         replacing=replacing)

        values = {parameter.name: getattr(manager.settings, parameter.name)
                  for parameter in effect.parameters if parameter.source == SOURCE_SETTINGS}
        asked = [parameter for parameter in effect.parameters if parameter.source == SOURCE_ASKED]
        if not asked:
            result = process(effect, values, base)
            if result is not None:
                preview(result)
            return

        def confirm(answers: Mapping[str, int]) -> None:
            result = process(effect, {**values, **answers}, base)
            if result is None:
                return
            manager.pop()
            preview(result)

        form = build_effect_form(effect, asked, confirm, manager.pop)
        manager.push(SettingsScreen(manager.parent, manager, form))

    def ask_substitution(effect: EffectSpec, previous: str) -> None:
        def go_on() -> None:
            def next_step() -> None:
                manager.pop()
                run_effect(effect, replacing=True)
            wx.CallAfter(next_step)

        def cancel() -> None:
            def back() -> None:
                manager.pop()
                manager.speaker.speak(CANCELED_MESSAGE)
            wx.CallAfter(back)

        manager.push(ConfirmScreen(manager.parent, manager, Confirmation(
            title=SUBSTITUTION_TITLE,
            question=conflict_question(previous, effect.label),
            options=(ConfirmOption(CONTINUE_LABEL, go_on), ConfirmOption(CANCEL_LABEL, cancel)),
            on_cancel=cancel,
            initial_index=1,
        )))

    def start_effect(effect: EffectSpec) -> None:
        if effect.family is None:
            run_effect(effect, replacing=False)
            return
        state = player.substitution(effect.family)
        if state == SUBSTITUTION_NONE:
            run_effect(effect, replacing=False)
            return
        previous = label_of(player.effects[effect.family])
        if state == SUBSTITUTION_NOT_LAST:
            with log_operation(APPLY_EFFECT):
                fail(not_last_error(previous, effect.label))
        elif state == SUBSTITUTION_NO_DATA:
            with log_operation(APPLY_EFFECT):
                fail(no_data_error(previous))
        else:
            ask_substitution(effect, previous)

    def volume_action(label: str, direction: str) -> Callable[[], None]:
        return lambda: adjust_volume(label, direction)

    def effect_action(effect: EffectSpec) -> Callable[[], None]:
        return lambda: start_effect(effect)

    def unavailable_action(label: str) -> Callable[[], None]:
        return lambda: manager.speaker.speak(unavailable_message(label))

    keys = {effect.key for effect in effects}
    items = [MenuItem(key, label, volume_action(label, direction)) for key, label, direction in VOLUME_ITEMS]
    items += [MenuItem(effect.key, effect.label, effect_action(effect)) for effect in effects]
    items += [MenuItem(key, label, unavailable_action(label))
              for key, label in UNAVAILABLE_ITEMS if key not in keys]
    return Menu(
        title=TITLE,
        intro=f"{TITLE}. {QUESTION}",
        items=items,
        letter_mode=LetterMode.ACTIVATE,
        has_help=True,
    )
