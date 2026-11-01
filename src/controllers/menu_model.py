from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum


class LetterMode(Enum):
    SELECT = "select"
    ACTIVATE = "activate"


class MenuDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class MenuItem:
    key: str
    label: str
    action: Callable[[], None]
    available: Callable[[], bool] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise MenuDefinitionError("Toda opção de menu precisa de um rótulo.")
        if not isinstance(self.key, str) or len(self.key) != 1 or not self.key.isalnum():
            raise MenuDefinitionError(
                f"Letra inválida para a opção {self.label!r}: {self.key!r}. "
                "Use uma única letra ou dígito."
            )
        if not callable(self.action):
            raise MenuDefinitionError(f"A opção {self.label!r} não tem uma ação válida.")
        object.__setattr__(self, "key", self.key.upper())

    @property
    def display_text(self) -> str:
        return f"{self.key} - {self.label}"

    def is_available(self) -> bool:
        if self.available is None:
            return True
        try:
            return bool(self.available())
        except Exception:
            return False


@dataclass(frozen=True)
class Menu:
    title: str
    items: Sequence[MenuItem]
    letter_mode: LetterMode = LetterMode.SELECT
    intro: str | None = None
    has_help: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise MenuDefinitionError("Todo menu precisa de um título.")

        items = tuple(self.items)
        if not items:
            raise MenuDefinitionError(f"O menu {self.title!r} não tem opções.")

        used: dict[str, str] = {}
        for item in items:
            if item.key in used:
                raise MenuDefinitionError(
                    f"Letra {item.key!r} repetida no menu {self.title!r}: "
                    f"{used[item.key]!r} e {item.label!r}."
                )
            used[item.key] = item.label

        object.__setattr__(self, "items", items)

    @property
    def opening_message(self) -> str:
        if self.intro and self.intro.strip():
            return self.intro
        return self.title

    def visible_items(self) -> list[MenuItem]:
        return [item for item in self.items if item.is_available()]

    def item_text(self, item: MenuItem) -> str:
        if self.letter_mode is LetterMode.ACTIVATE:
            return item.display_text
        return item.label
