import logging

import wx

from src.models.app_log import NO_VALUE, operation_logged
from src.models.errors import error_title
from src.view.speaker import Speaker

logger = logging.getLogger(__name__)


def error_details(error: BaseException | None) -> str:
    if error is None:
        return ""
    parts = [type(error).__name__]
    cause = error.__cause__ or error.__context__
    if cause is not None:
        parts.append(type(cause).__name__)
    for item in (error, cause):
        if isinstance(item, OSError) and item.errno is not None:
            parts.append(f"errno {item.errno}")
            break
    return f" ({', '.join(parts)})"


class Announcer:
    def __init__(self, parent: wx.Window | None, speaker: Speaker, version: str) -> None:
        self._parent = parent
        self._speaker = speaker
        self._version = version

    def info(self, message: str) -> None:
        self._speaker.speak(message)

    def error(self, message: str, operation: str | None = None, error: BaseException | None = None) -> None:
        if not operation_logged():
            logger.warning("Erro informado ao usuário: %s%s", operation or NO_VALUE, error_details(error))
        self.dialog(message, error_title(operation), wx.ICON_ERROR)

    def done(self, message: str) -> None:
        self.dialog(message, self._version, wx.ICON_INFORMATION)

    def dialog(self, message: str, title: str, icon: int = wx.ICON_INFORMATION) -> None:
        with wx.MessageDialog(self._parent, message, title, wx.OK | icon) as dialog:
            dialog.ShowModal()
