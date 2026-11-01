import logging

logger = logging.getLogger(__name__)


class Speaker:
    def __init__(self) -> None:
        self._output = None
        try:
            from accessible_output2.outputs.auto import Auto
            self._output = Auto()
        except Exception:
            logger.exception("Não foi possível iniciar a fala pelo leitor de tela.")

    @property
    def available(self) -> bool:
        return self._output is not None

    def speak(self, text: str, interrupt: bool = True) -> None:
        if self._output is None or not text:
            return
        try:
            self._output.speak(text, interrupt=interrupt)
        except Exception:
            logger.exception("Falha ao falar %r", text)
