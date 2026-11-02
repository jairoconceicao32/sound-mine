from collections.abc import Callable

from src.controllers.settings import ButtonField, NumberField, SettingsForm, SettingsTab

MAIN_VOLUME_DEFAULT = 100
BACKGROUND_VOLUME_DEFAULT = 30


def build_background_form(title: str, apply: Callable[[int, int], None],
                          cancel: Callable[[], None]) -> SettingsForm:
    def confirm() -> None:
        apply(form.values["main_volume"], form.values["background_volume"])

    form = SettingsForm(
        title=title,
        tabs=[
            SettingsTab("Volumes", [
                NumberField("main_volume", "Volume do áudio original"),
                NumberField("background_volume", "Volume da música de fundo"),
            ]),
        ],
        buttons=[
            ButtonField("Adicionar fundo sonoro", confirm),
            ButtonField("Cancelar", cancel),
        ],
        values={
            "main_volume": MAIN_VOLUME_DEFAULT,
            "background_volume": BACKGROUND_VOLUME_DEFAULT,
        },
        show_tab_selector=False,
    )
    return form
