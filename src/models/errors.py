OPEN_FILE = "abrir arquivo"
REMOVE = "remover trecho"
ADD_AUDIO = "adicionar áudio"
ADD_BACKGROUND = "adicionar fundo sonoro"
UNDO = "desfazer"
SAVE = "salvar"
PLAY = "tocar arquivo"
RUN_OPTION = "executar a opção"
START_SPEECH = "iniciar a fala"
LOAD_SETTINGS = "carregar as configurações"
SAVE_SETTINGS = "salvar as configurações"


class SoundMineError(Exception):
    def __init__(self, reason: str, hint: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.hint = hint


MEMORY_HINT = "Aumente o valor de Memória em megabytes, em Configurações, guia Desempenho."


def user_message(error: BaseException) -> str:
    if isinstance(error, SoundMineError):
        return f"{error.reason} {error.hint}" if error.hint else error.reason
    return str(error)


def unexpected_option_message(label: str) -> str:
    return f"Ocorreu um erro inesperado na opção {label}. Tente novamente."


def error_title(operation: str | None = None) -> str:
    if operation is None or not operation.strip():
        return "Erro"
    return f"Erro ao {operation.strip()}"
