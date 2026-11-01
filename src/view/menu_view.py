import wx

from src.view.screen import NoFocusPanel


class MenuView(NoFocusPanel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent)
        self._message = wx.StaticText(self, label="")
        self._item = wx.StaticText(self, label="")
        font = self._item.GetFont()
        font.SetPointSize(font.GetPointSize() + 6)
        self._item.SetFont(font)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._message, 0, wx.ALL, 10)
        sizer.Add(self._item, 0, wx.ALL, 10)
        self.SetSizer(sizer)

    def show_message(self, text: str) -> None:
        self._message.SetLabel(text)
        self.Layout()

    def show_item(self, text: str, position: int | None, total: int) -> None:
        if position is None:
            self._item.SetLabel("")
        else:
            self._item.SetLabel(f"{text}  ({position + 1} de {total})")
        self.Layout()
