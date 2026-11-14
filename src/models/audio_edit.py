import numpy as np

from src.models.errors import SoundMineError


class EditError(SoundMineError, ValueError):
    pass


INTERNAL_ERROR = ("Não foi possível concluir a edição por um erro interno.", "Tente novamente.")
EMPTY_RESULT = ("A remoção deixaria o áudio vazio.", "Escolha um trecho menor.")
NO_AUDIO = ("O arquivo escolhido não tem áudio.", "Escolha outro arquivo.")
VOLUME_MIN = 0
VOLUME_MAX = 100
AT_START = "start"
AT_CURSOR = "cursor"
AT_END = "end"


def _check_cursor(data: np.ndarray, cursor: int) -> None:
    if not 0 <= cursor <= len(data):
        raise EditError(*INTERNAL_ERROR)


def remove_before(data: np.ndarray, cursor: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, cursor)
    if cursor == 0:
        raise EditError("Não há trecho antes do cursor, porque ele está no início do áudio.",
                        "No player, posicione o cursor depois do trecho que deseja remover.")
    if cursor == len(data):
        raise EditError(*EMPTY_RESULT)
    return data[cursor:], 0


def remove_after(data: np.ndarray, cursor: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, cursor)
    if cursor == len(data):
        raise EditError("Não há trecho depois do cursor, porque ele está no final do áudio.",
                        "No player, posicione o cursor antes do trecho que deseja remover.")
    if cursor == 0:
        raise EditError(*EMPTY_RESULT)
    return data[:cursor], cursor


def remove_between(data: np.ndarray, cursor: int, marked: int | None) -> tuple[np.ndarray, int]:
    _check_cursor(data, cursor)
    if marked is None:
        raise EditError("Não há um ponto memorizado.", "No player, pressione M para memorizar um ponto.")
    _check_cursor(data, marked)
    if marked == cursor:
        raise EditError("O cursor está no ponto memorizado, então não há trecho entre os dois.",
                        "No player, mova o cursor ou memorize outro ponto.")
    start, end = sorted((cursor, marked))
    if start == 0 and end == len(data):
        raise EditError(*EMPTY_RESULT)
    return np.concatenate((data[:start], data[end:])), start


def insert(data: np.ndarray, other: np.ndarray, position: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, position)
    if len(other) == 0:
        raise EditError(*NO_AUDIO)
    return np.concatenate((data[:position], other, data[position:])), position


def overlay(data: np.ndarray, other: np.ndarray, start: int,
            main_volume: int, background_volume: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, start)
    if len(other) == 0:
        raise EditError(*NO_AUDIO)
    if not (VOLUME_MIN <= main_volume <= VOLUME_MAX and VOLUME_MIN <= background_volume <= VOLUME_MAX):
        raise EditError(*INTERNAL_ERROR)
    if start == len(data):
        raise EditError("O cursor está no final do áudio, então não há onde colocar o fundo sonoro.",
                        'Escolha "No início" ou mova o cursor no player.')
    end = min(len(data), start + len(other))
    result = data.copy()
    mixed = data[start:end] * (main_volume / VOLUME_MAX) + other[:end - start] * (background_volume / VOLUME_MAX)
    result[start:end] = np.clip(mixed, -1.0, 1.0)
    return result, start


def background_start(data: np.ndarray, other: np.ndarray, where: str, cursor: int) -> int:
    if where == AT_START:
        return 0
    if where == AT_CURSOR:
        return cursor
    return max(0, len(data) - len(other))


def insert_position(data: np.ndarray, where: str, cursor: int) -> int:
    if where == AT_START:
        return 0
    if where == AT_CURSOR:
        return cursor
    return len(data)
