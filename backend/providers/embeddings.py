"""Proveedor de embeddings enchufable.

Pieza separada del LLM a proposito: Anthropic no genera embeddings, asi que el
proveedor de embeddings se elige y se cambia de forma independiente.

- `HostedEmbeddings`: proveedor hospedado (Voyage por defecto).
- `LocalEmbeddings`: endpoint local compatible con OpenAI (Ollama / vLLM), para offline.

Ambos modelos deben ser multilingues (las normas estan en espanol e ingles).
Cambiar el modelo de embeddings obliga a re-indexar el corpus normativo, porque
los vectores no son compatibles entre modelos: por eso se guarda `modelo_embedding`
junto a cada vector (ver tabla chunk_normativo).

Los clientes se crean de forma perezosa (solo al primer embed) para no exigir
credenciales ni un endpoint vivo mientras no se use el RAG.
"""

from abc import ABC, abstractmethod

import httpx

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
    """Embeddings por defecto: proveedor hospedado (Voyage).

    Voyage no usa el SDK de OpenAI; se llama por HTTP directo. voyage-3 devuelve
    vectores de 1024 dimensiones, que coincide con EMBEDDING_DIM por defecto.
    """

    VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"

    def __init__(self) -> None:
        self._model = settings.embedding_model_hosted

    @property
    def model_name(self) -> str:
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not settings.voyage_api_key:
            raise RuntimeError(
                "Falta VOYAGE_API_KEY para usar embeddings hospedados (Voyage)."
            )
        resp = httpx.post(
            self.VOYAGE_URL,
            headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
            json={"input": texts, "model": self._model},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        # Voyage devuelve los embeddings en el mismo orden de entrada.
        return [item["embedding"] for item in data]


class LocalEmbeddings(EmbeddingProvider):
    """Embeddings locales via endpoint compatible con OpenAI (Ollama / vLLM).

    Usa el cliente de OpenAI apuntando al base_url local; asi corre 100% offline.
    """

    def __init__(self) -> None:
        self._model = settings.embedding_model_local
        self._client = None  # se crea de forma perezosa

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            # api_key es un placeholder: Ollama no la valida.
            self._client = OpenAI(
                base_url=settings.embedding_local_base_url,
                api_key="local",
            )
        return self._client

    def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        resp = client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]


def get_embedding_provider() -> EmbeddingProvider:
    """Devuelve la implementacion de embeddings segun EMBEDDING_PROVIDER."""
    if settings.embedding_provider == "local":
        return LocalEmbeddings()
    return HostedEmbeddings()
