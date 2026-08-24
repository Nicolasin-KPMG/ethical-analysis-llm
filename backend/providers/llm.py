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
import time
from abc import ABC, abstractmethod

from config import settings


def _segundos_sugeridos(exc) -> float | None:
    """Lee el `retryDelay` que el proveedor devuelve dentro del error 429."""
    try:
        cuerpo = exc.response.json()
    except Exception:
        return None
    # Gemini devuelve una lista; OpenAI un objeto. Se normaliza.
    if isinstance(cuerpo, list):
        cuerpo = cuerpo[0] if cuerpo else {}
    for d in cuerpo.get("error", {}).get("details", []) or []:
        valor = d.get("retryDelay")
        if isinstance(valor, str) and valor.endswith("s"):
            try:
                return float(valor[:-1]) + 1
            except ValueError:
                return None
    return None


def _con_reintento(llamada, intentos: int = 3):
    """Ejecuta `llamada` reintentando ante 429.

    Los tiers gratis limitan por minuto (Gemini free: 5 peticiones/min), y el
    analisis gasta dos de golpe. Sin esto, encadenar dos requisitos devuelve un
    500 al usuario en vez de tardar unos segundos mas.
    """
    from openai import RateLimitError

    for intento in range(intentos):
        try:
            return llamada()
        except RateLimitError as exc:
            if intento == intentos - 1:
                raise
            espera = min(_segundos_sugeridos(exc) or 10 * (intento + 1), 30)
            print(f"  [llm] 429: espero {espera:.0f}s y reintento...", flush=True)
            time.sleep(espera)
    raise RuntimeError("inalcanzable")


class LLMProvider(ABC):
    """Contrato que toda implementacion de LLM debe cumplir."""

    @abstractmethod
    def analyze(self, prompt: str, schema: dict) -> dict:
        """Recibe un prompt y un JSON Schema de salida; devuelve un dict validado."""
        ...

    @abstractmethod
    def chat(self, system: str, messages: list[dict]) -> str:
        """Conversacion libre (texto). `messages` = [{"role","content"}, ...]."""
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

    def chat(self, system: str, messages: list[dict]) -> str:
        client = self._get_client()
        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return "".join(b.text for b in msg.content if b.type == "text")


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
            # Explicito a proposito: sin base_url el SDK lee OPENAI_BASE_URL del
            # entorno, y basta que otra pieza la use para acabar hablando con el
            # proveedor equivocado. Vacio en la config = API oficial de OpenAI.
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=settings.openai_base_url or "https://api.openai.com/v1",
            )
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
        resp = _con_reintento(
            lambda: client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt_json}],
                response_format={"type": "json_object"},
            )
        )
        return json.loads(resp.choices[0].message.content)

    def chat(self, system: str, messages: list[dict]) -> str:
        client = self._get_client()
        resp = _con_reintento(
            lambda: client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, *messages],
            )
        )
        return resp.choices[0].message.content or ""


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
        resp = _con_reintento(
            lambda: client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt_json}],
                response_format={"type": "json_object"},
            )
        )
        return json.loads(resp.choices[0].message.content)

    def chat(self, system: str, messages: list[dict]) -> str:
        client = self._get_client()
        resp = _con_reintento(
            lambda: client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, *messages],
            )
        )
        return resp.choices[0].message.content or ""


def get_llm_provider() -> LLMProvider:
    """Devuelve la implementacion de LLM segun LLM_PROVIDER."""
    if settings.llm_provider == "openai":
        return OpenAILLM()
    if settings.llm_provider == "local":
        return LocalLLM()
    return AnthropicLLM()
