OPEN_FILE = "abrir arquivo"
REMOVE = "remover trecho"
ADD_AUDIO = "adicionar áudio"
ADD_BACKGROUND = "adicionar fundo sonoro"
UNDO = "desfazer"
SAVE = "salvar"
RUN_OPTION = "executar a opção"
START_SPEECH = "iniciar a fala"


class SoundMineError(Exception):
    def __init__(self, reason: str, hint: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.hint = hint


def error_title(operation: str | None = None) -> str:
    if operation is None or not operation.strip():
        return "Erro"
    return f"Erro ao {operation.strip()}"
