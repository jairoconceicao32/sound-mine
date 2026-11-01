from src.controllers.menu_model import Menu, MenuItem
from src.controllers.settings import build_settings_form
from src.view.settings_screen import SettingsScreen


def build_main_menu(manager) -> Menu:
    def not_implemented(name: str):
        return lambda: manager.announcer.info(f"{name}: ainda não implementado.")

    def open_settings() -> None:
        manager.push(SettingsScreen(manager.parent, manager, build_settings_form(manager)))
    return Menu(
        title="Menu principal",
        intro=(
            "Menu principal. Use as setas para cima e para baixo para navegar "
            "entre as opções do programa. Enter ativa uma opção."
        ),
        items=[
            MenuItem("A", "Abrir arquivo", not_implemented("Abrir arquivo")),
            MenuItem("C", "Configurações", open_settings),
            MenuItem("S", "Sair", manager.close),
        ],
    )
