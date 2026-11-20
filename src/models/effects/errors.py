from src.models.errors import SoundMineError

INTERNAL_ERROR = ("Não foi possível concluir o efeito por um erro interno.", "Tente novamente.")


class EffectError(SoundMineError):
    pass
