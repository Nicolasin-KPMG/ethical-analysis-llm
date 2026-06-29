"""Proveedor de LLM enchufable.

Interfaz unica `LLMProvider` con dos implementaciones:
- `AnthropicLLM`: SDK de Anthropic (Claude). Proveedor por defecto. Usa "tool use"
  para forzar una salida estructurada que cumpla el esquema (las tres capas).
- `LocalLLM`: endpoint compatible con OpenAI (Ollama / vLLM), para correr offline.
  Pide salida JSON y la parsea.

`analyze` recibe un prompt y un JSON Schema; devuelve un dict que cumple el esquema.
Los clientes se crean de forma perezosa para no exigir credenciales hasta usarlos.
"""

import json
from abc import ABC, abstractmethod

from config import settings


class LLMProvider(ABC):
    """Contrato que toda implementacion de LLM debe cumplir."""

    @abstractmethod
    def analyze(self, prompt: str, schema: dict) -> dict:
        """Recibe un prompt y un JSON Schema de salida; devuelve un dict validado."""
        ...


class AnthropicLLM(LLMProvider):
    """LLM por defecto: Claude via SDK de Anthropic, con salida estructurada."""

    def __init__(self) -> None:
        self.model = settings.anthropic_model
        self.api_key = settings.anthropic_api_key
        self._client = None  # perezoso

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic

            if not self.api_key:
                raise RuntimeError("Falta ANTHROPIC_API_KEY para usar el LLM de Anthropic.")
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def analyze(self, prompt: str, schema: dict) -> dict:
        client = self._get_client()
        # "tool use": definimos una herramienta cuyo input es el esquema deseado y
        # forzamos al modelo a llamarla, asi su salida cumple el esquema.
        herramienta = {
            "name": "registrar_resultado",
            "description": "Registra el resultado estructurado del analisis.",
            "input_schema": schema,
        }
        msg = client.messages.create(
            model=self.model,
            max_tokens=4096,
            tools=[herramienta],
            tool_choice={"type": "tool", "name": "registrar_resultado"},
            messages=[{"role": "user", "content": prompt}],
        )
        for bloque in msg.content:
            if bloque.type == "tool_use":
                return bloque.input
        raise RuntimeError("El modelo no devolvio una llamada a la herramienta.")


class OpenAILLM(LLMProvider):
    """LLM via API de OpenAI (GPT). Pieza independiente de los embeddings:
    se puede combinar con embeddings locales de Ollama sin re-indexar.
    """

    def __init__(self) -> None:
        self.model = settings.openai_model
        self.api_key = settings.openai_api_key
        self._client = None  # perezoso

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            if not self.api_key:
                raise RuntimeError("Falta OPENAI_API_KEY para usar el LLM de OpenAI.")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def analyze(self, prompt: str, schema: dict) -> dict:
        client = self._get_client()
        # Pedimos salida JSON; incluimos el esquema en el prompt como guia y
        # validamos despues con Pydantic en la capa de servicio.
        prompt_json = (
            prompt
            + "\n\nResponde UNICAMENTE con un JSON valido que cumpla este JSON Schema:\n"
            + json.dumps(schema, ensure_ascii=False)
        )
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt_json}],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)


class LocalLLM(LLMProvider):
    """LLM local via endpoint compatible con OpenAI (Ollama / vLLM)."""

    def __init__(self) -> None:
        self.base_url = settings.local_llm_base_url
        self.model = settings.local_llm_model
        self._client = None  # perezoso

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(base_url=self.base_url, api_key="local")
        return self._client

    def analyze(self, prompt: str, schema: dict) -> dict:
        client = self._get_client()
        # Pedimos JSON e incluimos el esquema en el prompt como guia.
        prompt_json = (
            prompt
            + "\n\nResponde UNICAMENTE con un JSON valido que cumpla este JSON Schema:\n"
            + json.dumps(schema, ensure_ascii=False)
        )
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt_json}],
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)


def get_llm_provider() -> LLMProvider:
    """Devuelve la implementacion de LLM segun LLM_PROVIDER."""
    if settings.llm_provider == "openai":
        return OpenAILLM()
    if settings.llm_provider == "local":
        return LocalLLM()
    return AnthropicLLM()
