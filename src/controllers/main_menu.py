from src.controllers.menu_model import Menu, MenuItem


def build_main_menu(manager) -> Menu:
    def not_implemented(name: str):
        return lambda: manager.announcer.info(f"{name}: ainda não implementado.")

    return Menu(
        title="Menu principal",
        intro=(
            "Menu principal. Use as setas para cima e para baixo para navegar "
            "entre as opções do programa. Enter ativa a ação."
        ),
        items=[
            MenuItem("A", "Abrir arquivo", not_implemented("Abrir arquivo")),
            MenuItem("C", "Configurações", not_implemented("Configurações")),
            MenuItem("S", "Sair", manager.close),
        ],
    )
