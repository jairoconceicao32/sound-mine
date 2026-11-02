from src.controllers.editor_menu import open_editor
from src.controllers.menu_model import Menu, MenuItem
from src.controllers.settings import build_settings_form
from src.models.audio_player import AudioLoadError, AudioPlayer
from src.view.file_dialog import choose_audio_file
from src.view.settings_screen import SettingsScreen


def build_main_menu(manager) -> Menu:
    def open_file() -> None:
        path = choose_audio_file(manager.parent.GetTopLevelParent())
        if path is None:
            return
        try:
            player = AudioPlayer(path, manager.settings.memory_mb)
        except AudioLoadError as error:
            manager.announcer.error(str(error))
            return
        open_editor(manager, player)

    def open_settings() -> None:
        manager.push(SettingsScreen(manager.parent, manager, build_settings_form(manager)))
    return Menu(
        title="Menu principal",
        intro=(
            "Menu principal. Use as setas para cima e para baixo para navegar "
            "entre as opções do programa. Enter ativa uma opção."
        ),
        items=[
            MenuItem("A", "Abrir arquivo", open_file),
            MenuItem("C", "Configurações", open_settings),
            MenuItem("S", "Sair", manager.close),
        ],
    )
