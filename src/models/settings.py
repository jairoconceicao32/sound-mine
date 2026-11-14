from collections.abc import Mapping
from dataclasses import dataclass, fields

LANGUAGES = ("Português", "inglês", "espanhol")
SAVE_FORMATS = ("mp3", "m4a", "wav", "ogg")
CHANNELS = ("Estéreo", "Mono")
SAMPLE_RATES = ("44100", "48000", "96000")


@dataclass(frozen=True)
class NumberRange:
    minimum: int
    maximum: int


OPTIONS = {
    "language": LANGUAGES,
    "format": SAVE_FORMATS,
    "channel": CHANNELS,
    "sample_rate": SAMPLE_RATES,
}
RANGES = {
    "echo_delay": NumberRange(10, 2000),
    "echo_percent": NumberRange(0, 100),
    "reverb_delay": NumberRange(10, 2000),
    "reverb_percent": NumberRange(0, 100),
    "memory_mb": NumberRange(0, 4096),
}


@dataclass
class Settings:
    language: str = "Português"
    format: str = "mp3"
    channel: str = "Estéreo"
    sample_rate: str = "44100"
    echo_delay: int = 300
    echo_percent: int = 75
    reverb_percent: int = 80
    reverb_delay: int = 200
    memory_mb: int = 0
    disable_sounds: bool = False
    disable_tips: bool = False


def is_valid(key: str, value: object) -> bool:
    if key in OPTIONS:
        return isinstance(value, str) and value in OPTIONS[key]
    if key in RANGES:
        limits = RANGES[key]
        return type(value) is int and limits.minimum <= value <= limits.maximum
    return type(value) is bool


def settings_from(data: Mapping[str, object]) -> tuple[Settings, tuple[str, ...]]:
    defaults = Settings()
    values = {}
    corrected = []
    for field in fields(Settings):
        value = data.get(field.name)
        if field.name in data and is_valid(field.name, value):
            values[field.name] = value
        else:
            values[field.name] = getattr(defaults, field.name)
            corrected.append(field.name)
    return Settings(**values), tuple(corrected)
