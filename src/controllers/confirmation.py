from collections.abc import Callable, Sequence
from dataclasses import dataclass

YES = "Sim"
NO = "Não"


class ConfirmationError(ValueError):
    pass


@dataclass(frozen=True)
class ConfirmOption:
    label: str
    action: Callable[[], None]

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise ConfirmationError("Toda opção de confirmação precisa de um rótulo.")
        if not callable(self.action):
            raise ConfirmationError(f"A opção {self.label!r} não tem uma ação válida.")


@dataclass(frozen=True)
class Confirmation:
    title: str
    question: str
    options: Sequence[ConfirmOption]
    on_cancel: Callable[[], None]
    initial_index: int = 0

    def __post_init__(self) -> None:
        for name in ("title", "question"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ConfirmationError(f"A confirmação precisa de um texto válido em {name!r}.")
        options = tuple(self.options)
        if len(options) < 2:
            raise ConfirmationError(f"A confirmação {self.title!r} precisa de pelo menos duas opções.")
        if not callable(self.on_cancel):
            raise ConfirmationError(f"A confirmação {self.title!r} não tem uma ação válida para o Esc.")
        if not 0 <= self.initial_index < len(options):
            raise ConfirmationError(f"Opção inicial inválida na confirmação {self.title!r}.")
        object.__setattr__(self, "options", options)

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(option.label for option in self.options)

    def action(self, index: int) -> Callable[[], None]:
        if not 0 <= index < len(self.options):
            raise ConfirmationError(f"Opção inválida na confirmação {self.title!r}: {index!r}.")
        return self.options[index].action

    def index_for_key(self, key: str | None, current: int = -1) -> int | None:
        if not isinstance(key, str) or len(key) != 1:
            return None
        total = len(self.options)
        for step in range(1, total + 1):
            index = (current + step) % total
            if self.options[index].label[0].upper() == key.upper():
                return index
        return None


def yes_no(title: str, question: str, on_yes: Callable[[], None], on_no: Callable[[], None],
           on_cancel: Callable[[], None], default_yes: bool = True) -> Confirmation:
    return Confirmation(
        title=title,
        question=question,
        options=(ConfirmOption(YES, on_yes), ConfirmOption(NO, on_no)),
        on_cancel=on_cancel,
        initial_index=0 if default_yes else 1,
    )
