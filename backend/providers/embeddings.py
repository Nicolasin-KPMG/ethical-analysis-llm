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

import time
from abc import ABC, abstractmethod
from collections import deque

import httpx

from config import settings


def _segundos_sugeridos(exc) -> float | None:
    """Saca el `retryDelay` que devuelve el proveedor en el error 429, si viene."""
    try:
        detalles = exc.response.json()["error"].get("details", [])
    except Exception:
        return None
    for d in detalles:
        valor = d.get("retryDelay")
        if isinstance(valor, str) and valor.endswith("s"):
            try:
                return float(valor[:-1]) + 1
            except ValueError:
                return None
    return None


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


class OpenAIEmbeddings(EmbeddingProvider):
    """Embeddings con la API de OpenAI (misma credencial que el LLM).

    Util para desplegar sin Ollama ni una cuenta aparte: reutiliza OPENAI_API_KEY.
    Los modelos text-embedding-3-* aceptan el parametro `dimensions`, asi que se
    recortan a EMBEDDING_DIM (1024) para casar con la columna VECTOR del esquema.
    """

    MAX_REINTENTOS = 6
    URL_OPENAI = "https://api.openai.com/v1"

    def __init__(self) -> None:
        self._model = settings.embedding_model_openai
        self._client = None  # perezoso
        # Marcas de tiempo de los textos ya enviados (ventana de 60 s).
        self._historial: deque[float] = deque()

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            clave = settings.embedding_openai_api_key or settings.openai_api_key
            if not clave:
                raise RuntimeError(
                    "Falta EMBEDDING_OPENAI_API_KEY (u OPENAI_API_KEY) para los embeddings."
                )
            # Siempre explicito: si no se pasa base_url, el SDK toma la variable
            # de entorno OPENAI_BASE_URL, que aqui apunta al LLM (Gemini) y hacia
            # que los embeddings de OpenAI se mandaran a Google con la key
            # equivocada. Vacio en la config = API oficial de OpenAI.
            self._client = OpenAI(
                api_key=clave,
                base_url=settings.embedding_openai_base_url or self.URL_OPENAI,
            )
        return self._client

    def _esperar_turno(self, n: int) -> None:
        """Frena antes de pedir, para no pasarse de EMBEDDING_RPM textos/minuto.

        Ventana deslizante de 60 s: si los `n` textos nuevos no caben, duerme
        hasta que el mas viejo salga de la ventana.
        """
        rpm = settings.embedding_rpm
        if rpm <= 0:
            return

        def _purgar() -> None:
            ahora = time.monotonic()
            while self._historial and ahora - self._historial[0] > 60:
                self._historial.popleft()

        _purgar()
        # Un lote mas grande que el cupo entero no cabe nunca: se espera a que
        # la ventana quede vacia y se manda igual (el reintento cubre el resto).
        while self._historial and len(self._historial) + n > rpm:
            espera = 60 - (time.monotonic() - self._historial[0]) + 0.5
            if espera > 0:
                time.sleep(espera)
            _purgar()

        ahora = time.monotonic()
        self._historial.extend([ahora] * n)

    def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        from openai import RateLimitError

        for intento in range(self.MAX_REINTENTOS):
            self._esperar_turno(len(texts))
            try:
                resp = client.embeddings.create(
                    model=self._model, input=texts, dimensions=settings.embedding_dim
                )
                return [d.embedding for d in resp.data]
            except RateLimitError as exc:
                if intento == self.MAX_REINTENTOS - 1:
                    raise
                # El proveedor suele decir cuanto esperar; si no, se va doblando.
                # Minimo de 20 s: el proveedor a veces sugiere ~0 s y reintentar
                # de inmediato solo quema mas cuota.
                espera = max(_segundos_sugeridos(exc) or 5 * (2**intento), 20)
                print(f"  [embeddings] 429: espero {espera:.0f}s y reintento...", flush=True)
                time.sleep(espera)
                # OJO: no se limpia el historial. El intento fallido igual conto
                # contra la cuota del proveedor, asi que olvidarlo hacia que el
                # siguiente saliera de golpe y volviera a chocar.

        raise RuntimeError("inalcanzable")


def get_embedding_provider() -> EmbeddingProvider:
    """Devuelve la implementacion de embeddings segun EMBEDDING_PROVIDER."""
    if settings.embedding_provider == "local":
        return LocalEmbeddings()
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddings()
    return HostedEmbeddings()
