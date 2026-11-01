import logging

import wx

from src import SOUND_MINE_VER
from src.controllers.main_menu import build_main_menu
from src.models.screen_manager import ScreenManager
from src.view.announcer import Announcer
from src.view.interface_sounds import InterfaceSounds
from src.view.menu_screen import MenuScreen
from src.view.speaker import Speaker


def main():
    logging.basicConfig(level=logging.WARNING)

    app = wx.App(False)
    frame = wx.Frame(None, title=SOUND_MINE_VER, size=(500, 400))
    speaker = Speaker()
    sounds = InterfaceSounds()
    announcer = Announcer(frame, speaker)
    manager = ScreenManager(frame, announcer, speaker, sounds)

    frame.Centre()
    frame.Show()
    sounds.play("startup")
    if not speaker.available:
        announcer.error(
            "A fala pelo leitor de tela não está disponível. "
            "Instale as dependências com: python -m pip install -r requirements.txt"
        )
    manager.push(MenuScreen(manager.parent, manager, build_main_menu(manager)))

    app.MainLoop()
