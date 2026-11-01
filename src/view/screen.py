from typing import TYPE_CHECKING

import wx

from src.view.keys import KeyCommand

if TYPE_CHECKING:
    from src.models.screen_manager import ScreenManager


class NoFocusPanel(wx.Panel):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("name", "")
        super().__init__(*args, **kwargs)

    def AcceptsFocus(self) -> bool:
        return False

    def AcceptsFocusFromKeyboard(self) -> bool:
        return False


class Screen(NoFocusPanel):
    def __init__(self, parent: wx.Window, manager: "ScreenManager") -> None:
        super().__init__(parent)
        self.manager = manager

    @property
    def title(self) -> str:
        raise NotImplementedError

    def on_activate(self) -> None:
        pass

    def on_deactivate(self) -> None:
        pass

    def handle_command(self, command: KeyCommand) -> bool:
        return False

    def help_lines(self) -> list[str]:
        return []
