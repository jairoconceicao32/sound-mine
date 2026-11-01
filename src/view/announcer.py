import wx

from src.view.speaker import Speaker


class Announcer:
    def __init__(self, parent: wx.Window | None, speaker: Speaker, version: str) -> None:
        self._parent = parent
        self._speaker = speaker
        self._version = version

    def info(self, message: str) -> None:
        self._speaker.speak(message)

    def error(self, message: str) -> None:
        self.dialog(message, f"Erro - {self._version}", wx.ICON_ERROR)

    def done(self, message: str) -> None:
        self.dialog(message, self._version, wx.ICON_INFORMATION)

    def dialog(self, message: str, title: str, icon: int = wx.ICON_INFORMATION) -> None:
        with wx.MessageDialog(self._parent, message, title, wx.OK | icon) as dialog:
            dialog.ShowModal()
