"""Proveedor de embeddings enchufable.

Pieza separada del LLM a proposito: Anthropic no genera embeddings, asi que el
proveedor de embeddings se elige y se cambia de forma independiente.

- `HostedEmbeddings`: proveedor hospedado (Voyage / OpenAI / Cohere).
- `LocalEmbeddings`: embeddings locales (sentence-transformers / Ollama), para offline.

Ambos modelos deben ser multilingues (las normas estan en espanol e ingles).
Cambiar el modelo de embeddings obliga a re-indexar el corpus normativo, porque
los vectores no son compatibles entre modelos: por eso se guarda `modelo_embedding`
junto a cada vector (ver tabla chunk_normativo).

En M0 `embed` queda como esqueleto; el RAG real se construye en M4.
"""

from abc import ABC, abstractmethod

from config import settings


class EmbeddingProvider(ABC):
    """Contrato que toda implementacion de embeddings debe cumplir."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Convierte una lista de textos en una lista de vectores."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo, para guardarlo junto a cada vector."""
        ...


class HostedEmbeddings(EmbeddingProvider):
    """Embeddings por defecto: proveedor hospedado (Voyage / OpenAI / Cohere)."""

    def __init__(self) -> None:
        self._model = settings.embedding_model_hosted

    @property
    def model_name(self) -> str:
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        # TODO (M4): llamar al proveedor hospedado y devolver los vectores.
        raise NotImplementedError(
            "HostedEmbeddings.embed se implementa en M4 (RAG)."
        )


class LocalEmbeddings(EmbeddingProvider):
    """Embeddings locales (sentence-transformers / Ollama), para correr offline.

    Stub por ahora: interfaz y seleccion listas, calculo real en M4.
    """

    def __init__(self) -> None:
        self._model = settings.embedding_model_local

    @property
    def model_name(self) -> str:
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        # TODO (M4): cargar el modelo local y devolver los vectores.
        raise NotImplementedError(
            "LocalEmbeddings.embed se implementa en M4 (RAG)."
        )


def get_embedding_provider() -> EmbeddingProvider:
    """Devuelve la implementacion de embeddings segun EMBEDDING_PROVIDER."""
    if settings.embedding_provider == "local":
        return LocalEmbeddings()
    return HostedEmbeddings()
