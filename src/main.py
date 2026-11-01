import logging

import wx

from src.controllers.main_menu import build_main_menu
from src.models.screen_manager import ScreenManager
from src.view.announcer import Announcer
from src.view.interface_sounds import InterfaceSounds
from src.view.menu_screen import MenuScreen
from src.view.speaker import Speaker
from src.view.startup_screen import StartupScreen


def main(version: str):
    logging.basicConfig(level=logging.WARNING)

    app = wx.App(False)
    frame = wx.Frame(None, title=version, size=(500, 400))
    speaker = Speaker()
    sounds = InterfaceSounds()
    announcer = Announcer(frame, speaker, version)
    manager = ScreenManager(frame, announcer, speaker, sounds, version)

    frame.Centre()
    frame.Show()
    if not speaker.available:
        announcer.error(
            "A fala pelo leitor de tela não está disponível. "
            "Instale as dependências com: python -m pip install -r requirements.txt"
        )

    def open_main_menu() -> None:
        manager.replace(MenuScreen(manager.parent, manager, build_main_menu(manager)))

    manager.push(StartupScreen(manager.parent, manager, open_main_menu))

    app.MainLoop()
