"""Proveedor de LLM enchufable.

Interfaz unica `LLMProvider` con dos implementaciones:
- `AnthropicLLM`: usa el SDK de Anthropic (Claude). Es el proveedor por defecto.
- `LocalLLM`: usa un endpoint compatible con OpenAI (Ollama / vLLM) para correr offline.

Importante: en M0 el metodo `analyze` queda como esqueleto. El analisis real
(Fases 2-3, con RAG y validacion del esquema de tres capas) se construye en M5.
Aqui solo dejamos lista la interfaz y la seleccion por variables de entorno.
"""

from abc import ABC, abstractmethod

from config import settings


class LLMProvider(ABC):
    """Contrato que toda implementacion de LLM debe cumplir."""

    @abstractmethod
    def analyze(self, prompt: str, schema: dict) -> dict:
        """Recibe un prompt y un JSON Schema de salida; devuelve un dict validado.

        En las Fases 2-3 esto producira el objeto de tres capas del contexto.
        """
        ...


class AnthropicLLM(LLMProvider):
    """LLM por defecto: Claude via SDK de Anthropic."""

    def __init__(self) -> None:
        self.model = settings.anthropic_model
        self.api_key = settings.anthropic_api_key
        # El cliente se crea de forma perezosa en analyze() para no exigir
        # la API key mientras solo estemos en M0/M1.

    def analyze(self, prompt: str, schema: dict) -> dict:
        # TODO (M5): instanciar anthropic.Anthropic(api_key=...), llamar a
        # messages.create forzando salida estructurada contra `schema`,
        # y devolver el dict validado.
        raise NotImplementedError(
            "AnthropicLLM.analyze se implementa en M5 (Fases 2-3)."
        )


class LocalLLM(LLMProvider):
    """LLM local via endpoint compatible con OpenAI (Ollama / vLLM).

    Stub por ahora: la interfaz y la seleccion estan listas, pero la llamada
    real se implementa en M5 junto con el analizador.
    """

    def __init__(self) -> None:
        self.base_url = settings.local_llm_base_url
        self.model = settings.local_llm_model

    def analyze(self, prompt: str, schema: dict) -> dict:
        # TODO (M5): usar el cliente OpenAI apuntando a base_url (Ollama/vLLM).
        raise NotImplementedError(
            "LocalLLM.analyze se implementa en M5 (Fases 2-3)."
        )


def get_llm_provider() -> LLMProvider:
    """Devuelve la implementacion de LLM segun LLM_PROVIDER."""
    if settings.llm_provider == "local":
        return LocalLLM()
    return AnthropicLLM()
