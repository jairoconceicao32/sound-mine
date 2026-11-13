from collections.abc import Callable

import wx

from src.controllers.background_form import build_background_form
from src.controllers.confirmation import Confirmation, yes_no
from src.controllers.editor_exit import CANCELED_MESSAGE, EditorExit
from src.controllers.menu_model import LetterMode, Menu, MenuItem
from src.models import audio_edit
from src.models.audio_edit import AT_CURSOR, AT_END, AT_START, EditError
from src.models.audio_player import AudioLoadError
from src.models.audio_save import AudioSaveError
from src.view.confirm_screen import ConfirmScreen
from src.view.editor_screen import EditorScreen
from src.view.file_dialog import choose_audio_file, choose_save_file
from src.view.player_screen import PlayerScreen
from src.view.settings_screen import SettingsScreen

QUESTION = "Qual sua opção?"
SAVED_SUFFIX = "_editado"


def _editor_menu(title: str, items: list[MenuItem], intro: str | None = None) -> Menu:
    return Menu(
        title=title,
        intro=intro or f"{title}. {QUESTION}",
        items=items,
        letter_mode=LetterMode.ACTIVATE,
        has_help=True,
    )


def _position_items(action: Callable[[str, str], None]) -> list[MenuItem]:
    return [
        MenuItem("I", "No início", lambda: action(AT_START, "no início")),
        MenuItem("C", "No cursor", lambda: action(AT_CURSOR, "no cursor")),
        MenuItem("F", "No final", lambda: action(AT_END, "no final")),
    ]


def build_editor_menu(manager, player) -> Menu:
    def open_menu(menu: Menu) -> Callable[[], None]:
        return lambda: manager.push(EditorScreen(manager.parent, manager, menu, player))

    def done(text: str) -> None:
        manager.announcer.done(text)

    def fail(text: str) -> None:
        manager.announcer.error(f"A operação não pode ser realizada: {text}")

    def play() -> None:
        manager.push(PlayerScreen(manager.parent, manager, player))

    def apply(operation, message: str) -> None:
        try:
            player.edit(operation)
        except EditError as error:
            fail(str(error))
            return
        done(message)

    def remove_before() -> None:
        apply(lambda data, cursor, marked: audio_edit.remove_before(data, cursor),
              "Trecho anterior removido.")

    def remove_after() -> None:
        apply(lambda data, cursor, marked: audio_edit.remove_after(data, cursor),
              "Trecho posterior removido.")

    def remove_between() -> None:
        apply(audio_edit.remove_between, "Trecho removido.")

    def choose_and_load():
        path = choose_audio_file(manager.parent.GetTopLevelParent())
        if path is None:
            return None
        try:
            return player.load_compatible(path)
        except AudioLoadError as error:
            manager.announcer.error(str(error))
            return None

    def add_audio(where: str, text: str) -> None:
        other = choose_and_load()
        if other is None:
            return
        apply(lambda data, cursor, marked: audio_edit.insert(
                  data, other, audio_edit.insert_position(data, where, cursor)),
              f"Arquivo adicionado {text}.")

    def add_background(where: str, text: str) -> None:
        other = choose_and_load()
        if other is None:
            return

        def apply_volumes(main_volume: int, background_volume: int) -> None:
            apply(lambda data, cursor, marked: audio_edit.overlay(
                      data, other, audio_edit.background_start(data, other, where, cursor),
                      main_volume, background_volume),
                  f"Fundo sonoro adicionado {text}.")
            manager.pop()

        form = build_background_form(f"Fundo sonoro {text}", apply_volumes, manager.pop)
        manager.push(SettingsScreen(manager.parent, manager, form))

    def save() -> None:
        save_audio_file(manager, player)

    def open_undo() -> None:
        if not player.has_changes:
            fail("não há alterações para desfazer.")
            return
        manager.push(ConfirmScreen(manager.parent, manager, yes_no(
            title="Desfazer alterações",
            question="Desfazer alterações. Deseja recuperar a última versão salva do arquivo?",
            on_yes=confirm_undo,
            on_no=lambda: cancel_confirmation(manager),
            on_cancel=lambda: cancel_confirmation(manager),
            default_yes=False,
        )))

    def confirm_undo() -> None:
        player.undo()
        done("Última versão salva recuperada.")
        wx.CallAfter(manager.pop)

    remove_menu = _editor_menu("Remover", [
        MenuItem("A", "Antes do cursor", remove_before),
        MenuItem("D", "Depois do cursor", remove_after),
        MenuItem("E", "Entre o cursor e o ponto memorizado", remove_between),
    ])
    add_menu = _editor_menu("Adição de áudio", _position_items(add_audio))
    background_menu = _editor_menu("Fundo sonoro", _position_items(add_background))
    mix_menu = _editor_menu("Misturar", [
        MenuItem("A", "Adição de áudio", open_menu(add_menu)),
        MenuItem("F", "Fundo sonoro", open_menu(background_menu)),
    ])
    return _editor_menu(
        "Menu de edição",
        [
            MenuItem("T", "Tocar arquivo", play),
            MenuItem("R", "Remover", open_menu(remove_menu)),
            MenuItem("M", "Misturar", open_menu(mix_menu)),
            MenuItem("D", "Desfazer", open_undo),
            MenuItem("S", "Salvar", save),
        ],
        intro=QUESTION,
    )


def save_audio_file(manager, player) -> bool:
    settings = manager.settings
    file_format = settings.format
    requested_rate = int(settings.sample_rate)
    stem = player.path.stem
    if not stem.endswith(SAVED_SUFFIX):
        stem += SAVED_SUFFIX
    name = f"{stem}.{file_format}"
    path = choose_save_file(manager.parent.GetTopLevelParent(), player.path.parent, name, file_format)
    if path is None:
        return False
    manager.speaker.speak("Salvando o arquivo.")
    try:
        saved_rate = player.save(path, file_format, settings.channel, requested_rate)
    except AudioSaveError as error:
        manager.announcer.error(str(error))
        return False
    message = f"Arquivo salvo: {path.name}."
    if saved_rate != requested_rate:
        message += (f" A taxa de amostragem foi de {saved_rate} Hz, a maior aceita pelo formato "
                    f"{file_format.upper()}.")
    manager.announcer.done(message)
    return True


def cancel_confirmation(manager, message: str = CANCELED_MESSAGE) -> None:
    def back() -> None:
        manager.pop()
        manager.speaker.speak(message)
    wx.CallAfter(back)


def open_editor(manager, player, replace: bool = False) -> None:
    def show(confirmation: Confirmation) -> ConfirmScreen:
        player.pause()
        confirm = ConfirmScreen(manager.parent, manager, confirmation)
        manager.push(confirm)
        return confirm

    editor_exit = EditorExit(
        has_changes=lambda: player.has_changes,
        save=lambda: save_audio_file(manager, player),
        show=show,
        back=lambda message: cancel_confirmation(manager, message),
        schedule=wx.CallAfter,
    )

    def back_to_menu() -> None:
        manager.pop_through(screen)

    screen = EditorScreen(manager.parent, manager, build_editor_menu(manager, player), player,
                          on_back=lambda: editor_exit.request(back_to_menu))
    close_guard = editor_exit.request
    manager.set_close_guard(close_guard)

    def on_destroy(event: wx.WindowDestroyEvent) -> None:
        if event.GetEventObject() is screen:
            manager.clear_close_guard(close_guard)
            player.close()
        event.Skip()

    screen.Bind(wx.EVT_WINDOW_DESTROY, on_destroy)
    if replace:
        manager.replace(screen)
    else:
        manager.push(screen)
