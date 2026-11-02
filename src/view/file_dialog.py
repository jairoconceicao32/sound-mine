from pathlib import Path

import wx

from src.models.audio_player import ACCEPTED_FORMATS

DIALOG_TITLE = "Abrir arquivo de áudio"
SAVE_TITLE = "Salvar arquivo de áudio"


def audio_wildcard() -> str:
    patterns = ";".join(f"*{extension}" for extension in ACCEPTED_FORMATS)
    return f"Arquivos de áudio ({patterns})|{patterns}"


def choose_audio_file(parent: wx.Window, folder: Path | None = None) -> Path | None:
    default_dir = str(folder) if folder is not None and folder.is_dir() else ""
    with wx.FileDialog(parent, DIALOG_TITLE, defaultDir=default_dir, wildcard=audio_wildcard(),
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
        if dialog.ShowModal() != wx.ID_OK:
            return None
        return Path(dialog.GetPath())


def choose_save_file(parent: wx.Window, folder: Path, name: str, extension: str) -> Path | None:
    pattern = f"*.{extension}"
    wildcard = f"Arquivo {extension.upper()} ({pattern})|{pattern}"
    default_dir = str(folder) if folder.is_dir() else ""
    with wx.FileDialog(parent, SAVE_TITLE, defaultDir=default_dir, defaultFile=name, wildcard=wildcard,
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
        if dialog.ShowModal() != wx.ID_OK:
            return None
        return Path(dialog.GetPath())
