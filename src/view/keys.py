from dataclasses import dataclass
from enum import Enum, auto

import wx


class Command(Enum):
    UP = auto()
    DOWN = auto()
    ACTIVATE = auto()
    BACK = auto()
    HELP = auto()
    LETTER = auto()
    BLOCKED = auto()
    NEXT_FIELD = auto()
    PREV_FIELD = auto()
    NEXT_TAB = auto()
    PREV_TAB = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()
    HOME = auto()
    END = auto()
    ERASE = auto()
    LEFT = auto()
    RIGHT = auto()
    SPACE = auto()


@dataclass(frozen=True)
class KeyCommand:
    command: Command
    char: str | None = None


_KEY_MAP = {
    wx.WXK_UP: Command.UP,
    wx.WXK_NUMPAD_UP: Command.UP,
    wx.WXK_DOWN: Command.DOWN,
    wx.WXK_NUMPAD_DOWN: Command.DOWN,
    wx.WXK_RETURN: Command.ACTIVATE,
    wx.WXK_NUMPAD_ENTER: Command.ACTIVATE,
    wx.WXK_ESCAPE: Command.BACK,
    wx.WXK_F1: Command.HELP,
    wx.WXK_PAGEUP: Command.PAGE_UP,
    wx.WXK_NUMPAD_PAGEUP: Command.PAGE_UP,
    wx.WXK_PAGEDOWN: Command.PAGE_DOWN,
    wx.WXK_NUMPAD_PAGEDOWN: Command.PAGE_DOWN,
    wx.WXK_HOME: Command.HOME,
    wx.WXK_NUMPAD_HOME: Command.HOME,
    wx.WXK_END: Command.END,
    wx.WXK_NUMPAD_END: Command.END,
    wx.WXK_BACK: Command.ERASE,
    wx.WXK_LEFT: Command.LEFT,
    wx.WXK_NUMPAD_LEFT: Command.LEFT,
    wx.WXK_RIGHT: Command.RIGHT,
    wx.WXK_NUMPAD_RIGHT: Command.RIGHT,
    wx.WXK_SPACE: Command.SPACE,
}

_BLOCKED_KEYS: set[int] = set()


_SYSTEM_MENU_KEYS = {wx.WXK_ALT, wx.WXK_MENU}


def translate(event: wx.KeyEvent) -> KeyCommand | None:
    code = event.GetKeyCode()
    if code in _SYSTEM_MENU_KEYS:
        return KeyCommand(Command.BLOCKED)
    if event.AltDown() and code == wx.WXK_SPACE:
        return KeyCommand(Command.BLOCKED)
    if code in (wx.WXK_TAB, wx.WXK_NUMPAD_TAB) and not event.AltDown():
        if event.ControlDown():
            return KeyCommand(Command.PREV_TAB if event.ShiftDown() else Command.NEXT_TAB)
        return KeyCommand(Command.PREV_FIELD if event.ShiftDown() else Command.NEXT_FIELD)
    if event.HasModifiers():
        return None

    if code in _KEY_MAP:
        return KeyCommand(_KEY_MAP[code])
    if code in _BLOCKED_KEYS:
        return KeyCommand(Command.BLOCKED)

    if wx.WXK_NUMPAD0 <= code <= wx.WXK_NUMPAD9:
        return KeyCommand(Command.LETTER, str(code - wx.WXK_NUMPAD0))

    char_code = event.GetUnicodeKey()
    if char_code != wx.WXK_NONE:
        char = chr(char_code)
        if char.isalnum():
            return KeyCommand(Command.LETTER, char.upper())
    return None
