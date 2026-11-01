from src.controllers.menu_model import Menu, MenuItem


class MenuNavigator:
    def __init__(self, menu: Menu) -> None:
        self._menu = menu
        self._items: list[MenuItem] = []
        self._index = 0
        self.refresh()

    @property
    def menu(self) -> Menu:
        return self._menu

    @property
    def items(self) -> tuple[MenuItem, ...]:
        return tuple(self._items)

    @property
    def index(self) -> int | None:
        return self._index if self._items else None

    def current(self) -> MenuItem | None:
        return self._items[self._index] if self._items else None

    def refresh(self) -> None:
        previous = self.current()
        self._items = self._menu.visible_items()

        if not self._items:
            self._index = 0
            return

        if previous is not None:
            for position, item in enumerate(self._items):
                if item.key == previous.key:
                    self._index = position
                    return

        self._index = min(self._index, len(self._items) - 1)

    def move_up(self) -> bool:
        if not self._items or self._index == 0:
            return False
        self._index -= 1
        return True

    def move_down(self) -> bool:
        if not self._items or self._index == len(self._items) - 1:
            return False
        self._index += 1
        return True

    def select_index(self, index: int) -> bool:
        if not 0 <= index < len(self._items):
            return False
        self._index = index
        return True

    def select_by_key(self, key: str) -> MenuItem | None:
        if not isinstance(key, str) or len(key) != 1:
            return None
        wanted = key.upper()
        for position, item in enumerate(self._items):
            if item.key == wanted:
                self._index = position
                return item
        return None
