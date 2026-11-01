from collections.abc import Callable, Sequence
from dataclasses import dataclass

LANGUAGES = ("Português", "inglês", "espanhol")
formate_file = (
    "mp3",
    "m4a",
    "wav",
    "ogg",
)
chanel_audio = (
    "Estéreo",
    "Mono"
)
sample_rate = (
    "44100",
    "48000",
    "96000"
)

DIGITS = "0123456789"


class SettingsDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class OptionField:
    key: str
    label: str
    options: Sequence[str]

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise SettingsDefinitionError("Todo campo precisa de um rótulo.")
        options = tuple(self.options)
        if not options:
            raise SettingsDefinitionError(f"O campo {self.label!r} não tem opções.")
        object.__setattr__(self, "options", options)


@dataclass(frozen=True)
class NumberField:
    key: str
    label: str
    minimum: int = 0
    maximum: int = 100
    step: int = 5
    big_step: int = 10
    suffix: str = "%"
    slider: bool = True
    zero_text: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise SettingsDefinitionError("Todo campo precisa de um rótulo.")
        if self.minimum < 0 or self.minimum >= self.maximum:
            raise SettingsDefinitionError(f"Faixa inválida no campo {self.label!r}.")
        if self.step <= 0 or self.big_step <= 0:
            raise SettingsDefinitionError(f"Passo inválido no campo {self.label!r}.")


@dataclass(frozen=True)
class ToggleField:
    key: str
    label: str

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise SettingsDefinitionError("Todo campo precisa de um rótulo.")


@dataclass(frozen=True)
class ButtonField:
    label: str
    action: Callable[[], None]

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise SettingsDefinitionError("Todo botão precisa de um rótulo.")
        if not callable(self.action):
            raise SettingsDefinitionError(f"O botão {self.label!r} não tem uma ação válida.")


@dataclass(frozen=True)
class TabField:
    label: str = "Guia"


TAB_FIELD = TabField()

InputField = OptionField | NumberField | ToggleField
Field = TabField | OptionField | NumberField | ToggleField | ButtonField


@dataclass(frozen=True)
class SettingsTab:
    name: str
    fields: Sequence[InputField]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise SettingsDefinitionError("Toda guia precisa de um nome.")
        fields = tuple(self.fields)
        if not fields:
            raise SettingsDefinitionError(f"A guia {self.name!r} não tem campos.")
        object.__setattr__(self, "fields", fields)


def _initial_value(field: InputField, value: str | int | bool | None) -> str | int | bool:
    if isinstance(field, ToggleField):
        return value if isinstance(value, bool) else False
    if isinstance(field, NumberField):
        if isinstance(value, int) and not isinstance(value, bool) \
                and field.minimum <= value <= field.maximum:
            return value
        return field.minimum
    return value if value in field.options else field.options[0]


class SettingsForm:
    def __init__(self, title: str, tabs: Sequence[SettingsTab],
                 buttons: Sequence[ButtonField], values: dict[str, str | int | bool]) -> None:
        self.title = title
        self._tabs = tuple(tabs)
        if not self._tabs:
            raise SettingsDefinitionError(f"O formulário {title!r} não tem guias.")
        self._buttons = tuple(buttons)
        self._values: dict[str, str | int | bool] = {}
        for tab in self._tabs:
            for field in tab.fields:
                if field.key in self._values:
                    raise SettingsDefinitionError(f"Campo {field.key!r} repetido.")
                self._values[field.key] = _initial_value(field, values.get(field.key))
        self._tab_index = 0
        self._field_index = 0
        self._typing: str | None = None

    @property
    def values(self) -> dict[str, str | int | bool]:
        return dict(self._values)

    @property
    def tabs(self) -> tuple[SettingsTab, ...]:
        return self._tabs

    @property
    def tab(self) -> SettingsTab:
        return self._tabs[self._tab_index]

    @property
    def tab_index(self) -> int:
        return self._tab_index

    @property
    def tab_count(self) -> int:
        return len(self._tabs)

    @property
    def fields(self) -> tuple[Field, ...]:
        return (TAB_FIELD, *self.tab.fields, *self._buttons)

    @property
    def field_index(self) -> int:
        return self._field_index

    @property
    def typing(self) -> str | None:
        return self._typing

    def current(self) -> Field:
        return self.fields[self._field_index]

    def value_of(self, field: TabField | InputField) -> str:
        if isinstance(field, TabField):
            return self.tab.name
        if isinstance(field, ToggleField):
            return "marcado" if self._values[field.key] else "não marcado"
        if isinstance(field, NumberField):
            value = self._values[field.key]
            if value == 0 and field.zero_text:
                return field.zero_text
            return f"{value}{field.suffix}"
        return self._values[field.key]

    def text_of(self, field: Field) -> str:
        if isinstance(field, ButtonField):
            return field.label
        return f"{field.label}: {self.value_of(field)}"

    def next_field(self) -> bool:
        if self._field_index >= len(self.fields) - 1:
            return False
        self._typing = None
        self._field_index += 1
        return True

    def prev_field(self) -> bool:
        if self._field_index == 0:
            return False
        self._typing = None
        self._field_index -= 1
        return True

    def next_tab(self) -> bool:
        return self._select_tab(self._tab_index + 1)

    def prev_tab(self) -> bool:
        return self._select_tab(self._tab_index - 1)

    def change_value(self, step: int) -> bool:
        field = self.current()
        if isinstance(field, TabField):
            return self._select_tab(self._tab_index + step)
        if isinstance(field, NumberField):
            return self._set_number(field, self._values[field.key] - step * field.step)
        if not isinstance(field, OptionField):
            return False
        position = field.options.index(self._values[field.key]) + step
        if not 0 <= position < len(field.options):
            return False
        self._values[field.key] = field.options[position]
        return True

    def change_big(self, step: int) -> bool:
        field = self.current()
        if not isinstance(field, NumberField):
            return False
        return self._set_number(field, self._values[field.key] + step * field.big_step)

    def go_to_limit(self, maximum: bool) -> bool:
        field = self.current()
        if not isinstance(field, NumberField):
            return False
        return self._set_number(field, field.maximum if maximum else field.minimum)

    def type_digit(self, digit: str) -> bool:
        field = self.current()
        if not isinstance(field, NumberField) or len(digit) != 1 or digit not in DIGITS:
            return False
        typed = (self._typing or "") + digit
        if len(typed) > len(str(field.maximum)):
            return False
        self._typing = typed
        return True

    def erase(self) -> bool:
        if not self._typing:
            return False
        self._typing = self._typing[:-1]
        return True

    def set_toggle(self, checked: bool) -> bool:
        field = self.current()
        if not isinstance(field, ToggleField) or not isinstance(checked, bool):
            return False
        self._values[field.key] = checked
        return True

    def set_text(self, text: str) -> bool:
        field = self.current()
        if not isinstance(field, NumberField):
            return False
        text = text.strip()
        if not text or len(text) > len(str(field.maximum)) \
                or any(char not in DIGITS for char in text):
            return False
        value = int(text)
        if not field.minimum <= value <= field.maximum:
            return False
        self._typing = None
        self._values[field.key] = value
        return True

    def confirm_typing(self) -> bool:
        field = self.current()
        typed, self._typing = self._typing, None
        if not isinstance(field, NumberField) or not typed:
            return False
        value = int(typed)
        if not field.minimum <= value <= field.maximum:
            return False
        self._values[field.key] = value
        return True

    def cancel_typing(self) -> bool:
        if self._typing is None:
            return False
        self._typing = None
        return True

    def _set_number(self, field: NumberField, value: int) -> bool:
        if not field.slider:
            return False
        value = max(field.minimum, min(field.maximum, value))
        if value == self._values[field.key]:
            return False
        self._typing = None
        self._values[field.key] = value
        return True

    def _select_tab(self, index: int) -> bool:
        if not 0 <= index < len(self._tabs):
            return False
        self._typing = None
        self._tab_index = index
        self._field_index = 0
        return True


def build_settings_form(manager) -> SettingsForm:
    def save() -> None:
        manager.settings.language = form.values["language"]
        manager.settings.format = form.values["format"]
        manager.settings.channel = form.values["channel"]
        manager.settings.sample_rate = form.values["sample_rate"]
        manager.settings.echo_delay = form.values["echo_delay"]
        manager.settings.echo_percent = form.values["echo_percent"]
        manager.settings.reverb_percent = form.values["reverb_percent"]
        manager.settings.reverb_delay = form.values["reverb_delay"]
        manager.settings.memory_mb = form.values["memory_mb"]
        manager.settings.play_buffers = form.values["play_buffers"]
        manager.settings.record_buffers = form.values["record_buffers"]
        manager.settings.disable_sounds = form.values["disable_sounds"]
        manager.settings.disable_tips = form.values["disable_tips"]
        manager.sounds.enabled = not manager.settings.disable_sounds
        manager.pop()
        manager.announcer.info("Configurações salvas.")

    form = SettingsForm(
        title="Configurações",
        tabs=[
            SettingsTab("Geral", [
                OptionField("language", "Idioma", LANGUAGES),
                OptionField("format", "Formato de áudio que o arquivo será salvo", formate_file),
                OptionField("channel", "Tipo de canal que o arquivo será salvo", chanel_audio),
                OptionField("sample_rate", "Taxa de amostragem que o áudio será salvo", sample_rate),
                ToggleField("disable_sounds", "Desativar sons da interface"),
                ToggleField("disable_tips", "Desativar dicas do programa"),
            ]
            ),
            SettingsTab("Efeitos de áudio", [
                NumberField("echo_delay", "Milissegundos para o eco",
                            minimum=10, maximum=2000, suffix=" milissegundos",
                            slider=False),
                NumberField("echo_percent", "Percentual do eco"),
                NumberField("reverb_delay", "Milissegundos para o reverbe",
                            minimum=10, maximum=2000, suffix=" milissegundos",
                            slider=False),
                NumberField("reverb_percent", "Percentual do reverbe"),
            ]),
            SettingsTab("Desempenho", [
                NumberField("memory_mb", "Memória em megabytes",
                            minimum=0, maximum=4096, suffix=" megabytes",
                            slider=False, zero_text="Automático"),
                NumberField("play_buffers", "Buffers para tocar",
                            minimum=1, maximum=32, suffix="",
                            slider=False),
                NumberField("record_buffers", "Buffers para gravar",
                            minimum=1, maximum=32, suffix="",
                            slider=False)
            ])
        ],

        buttons=[
            ButtonField("Salvar configurações", save),
            ButtonField("Cancelar", manager.pop),
        ],
        values={
            "language": manager.settings.language,
            "format": manager.settings.format,
            "channel": manager.settings.channel,
            "sample_rate": manager.settings.sample_rate,
            "echo_delay": manager.settings.echo_delay,
            "echo_percent": manager.settings.echo_percent,
            "reverb_percent": manager.settings.reverb_percent,
            "reverb_delay": manager.settings.reverb_delay,
            "memory_mb": manager.settings.memory_mb,
            "play_buffers": manager.settings.play_buffers,
            "record_buffers": manager.settings.record_buffers,
            "disable_sounds": manager.settings.disable_sounds,
            "disable_tips": manager.settings.disable_tips,
        },
    )
    return form
