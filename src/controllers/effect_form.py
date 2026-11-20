from collections.abc import Callable, Mapping, Sequence

from src.controllers.settings import ButtonField, NumberField, SettingsForm, SettingsTab
from src.models.effects.contract import EffectParameter, EffectSpec

CONFIRM_LABEL = "Ouvir prévia"
CANCEL_LABEL = "Cancelar"


def build_effect_form(effect: EffectSpec, parameters: Sequence[EffectParameter],
                      confirm: Callable[[Mapping[str, int]], None],
                      cancel: Callable[[], None]) -> SettingsForm:
    def on_confirm() -> None:
        values = form.values
        confirm({parameter.name: values[parameter.name] for parameter in parameters})

    form = SettingsForm(
        title=effect.label,
        tabs=[
            SettingsTab(effect.label, [
                NumberField(parameter.name, parameter.label, minimum=parameter.minimum,
                            maximum=parameter.maximum, suffix="", slider=False)
                for parameter in parameters
            ]),
        ],
        buttons=[
            ButtonField(CONFIRM_LABEL, on_confirm),
            ButtonField(CANCEL_LABEL, cancel),
        ],
        values={parameter.name: parameter.default for parameter in parameters},
        show_tab_selector=False,
    )
    return form
