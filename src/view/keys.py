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
}

_BLOCKED_KEYS = {
    wx.WXK_HOME, wx.WXK_END, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN,
    wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_SPACE,
    wx.WXK_NUMPAD_HOME, wx.WXK_NUMPAD_END,
    wx.WXK_NUMPAD_PAGEUP, wx.WXK_NUMPAD_PAGEDOWN,
    wx.WXK_NUMPAD_LEFT, wx.WXK_NUMPAD_RIGHT,
}


_SYSTEM_MENU_KEYS = {wx.WXK_ALT, wx.WXK_MENU}


def translate(event: wx.KeyEvent) -> KeyCommand | None:
    code = event.GetKeyCode()
    if code in _SYSTEM_MENU_KEYS:
        return KeyCommand(Command.BLOCKED)
    if event.AltDown() and code == wx.WXK_SPACE:
        return KeyCommand(Command.BLOCKED)
    if event.HasModifiers():
        return None

    if code in _KEY_MAP:
        return KeyCommand(_KEY_MAP[code])
    if code in _BLOCKED_KEYS:
        return KeyCommand(Command.BLOCKED)

    char_code = event.GetUnicodeKey()
    if char_code != wx.WXK_NONE:
        char = chr(char_code)
        if char.isalnum():
            return KeyCommand(Command.LETTER, char.upper())
    return None
