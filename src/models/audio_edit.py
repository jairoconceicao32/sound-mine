import numpy as np


class EditError(ValueError):
    pass


EMPTY_RESULT = "a operação deixaria o áudio vazio."
VOLUME_MIN = 0
VOLUME_MAX = 100
AT_START = "start"
AT_CURSOR = "cursor"
AT_END = "end"


def _check_cursor(data: np.ndarray, cursor: int) -> None:
    if not 0 <= cursor <= len(data):
        raise EditError("o cursor não está em uma posição válida.")


def remove_before(data: np.ndarray, cursor: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, cursor)
    if cursor == 0:
        raise EditError("o cursor está no início do áudio.")
    if cursor == len(data):
        raise EditError(EMPTY_RESULT)
    return data[cursor:], 0


def remove_after(data: np.ndarray, cursor: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, cursor)
    if cursor == len(data):
        raise EditError("o cursor está no final do áudio.")
    if cursor == 0:
        raise EditError(EMPTY_RESULT)
    return data[:cursor], cursor


def remove_between(data: np.ndarray, cursor: int, marked: int | None) -> tuple[np.ndarray, int]:
    _check_cursor(data, cursor)
    if marked is None:
        raise EditError("não existe um ponto memorizado.")
    _check_cursor(data, marked)
    if marked == cursor:
        raise EditError("o cursor está no ponto memorizado.")
    start, end = sorted((cursor, marked))
    if start == 0 and end == len(data):
        raise EditError(EMPTY_RESULT)
    return np.concatenate((data[:start], data[end:])), start


def insert(data: np.ndarray, other: np.ndarray, position: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, position)
    if len(other) == 0:
        raise EditError("o arquivo escolhido não tem áudio.")
    return np.concatenate((data[:position], other, data[position:])), position


def overlay(data: np.ndarray, other: np.ndarray, start: int,
            main_volume: int, background_volume: int) -> tuple[np.ndarray, int]:
    _check_cursor(data, start)
    if len(other) == 0:
        raise EditError("o arquivo escolhido não tem áudio.")
    if not (VOLUME_MIN <= main_volume <= VOLUME_MAX and VOLUME_MIN <= background_volume <= VOLUME_MAX):
        raise EditError("os volumes definidos são inválidos.")
    if start == len(data):
        raise EditError("não há áudio depois da posição escolhida para o fundo sonoro.")
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
