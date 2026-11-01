import wx

from src import SOUND_MINE_VER
from src.view.speaker import Speaker


class Announcer:
    def __init__(self, parent: wx.Window | None, speaker: Speaker) -> None:
        self._parent = parent
        self._speaker = speaker

    def info(self, message: str) -> None:
        self._speaker.speak(message)

    def error(self, message: str) -> None:
        self.dialog(message, f"Erro - {SOUND_MINE_VER}", wx.ICON_ERROR)

    def done(self, message: str) -> None:
        self.dialog(message, SOUND_MINE_VER, wx.ICON_INFORMATION)

    def dialog(self, message: str, title: str, icon: int = wx.ICON_INFORMATION) -> None:
        with wx.MessageDialog(self._parent, message, title, wx.OK | icon) as dialog:
            dialog.ShowModal()
