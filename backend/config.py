"""Configuracion central de la aplicacion.

Toda la configuracion se lee de variables de entorno (ver .env.example).
Cambiar de proveedor de LLM o de embeddings es solo cambiar estas variables;
el resto del codigo nunca habla directo con un SDK concreto.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Lee de un archivo .env si existe; en docker-compose las variables llegan
    # directamente del entorno, lo que tiene prioridad.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Base de datos ---
    database_url: str = "postgresql://postgres:postgres@db:5432/tesis"

    # --- Proveedor de LLM ---
    llm_provider: str = "anthropic"  # "anthropic" | "openai" | "local"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "llama3.1:8b"

    # --- Proveedor de embeddings (pieza aparte: Anthropic no genera embeddings) ---
    embedding_provider: str = "hosted"  # "hosted" | "local"
    embedding_model_hosted: str = "voyage-3"
    embedding_model_local: str = "intfloat/multilingual-e5-large"
    embedding_dim: int = 1024  # debe coincidir con el modelo elegido y con la columna VECTOR
    # Credencial del proveedor hospedado (Voyage por defecto).
    voyage_api_key: str = ""
    # Endpoint local compatible con OpenAI para embeddings (Ollama / vLLM).
    embedding_local_base_url: str = "http://localhost:11434/v1"

    # --- RAG (recuperacion) ---
    # Controlan cuanto contexto normativo se inyecta al analisis (Fases 2-3) y,
    # por tanto, el gasto de tokens del LLM.
    rag_k_por_consulta: int = 4   # fragmentos a recuperar por cada consulta del LLM
    rag_max_fragmentos: int = 10  # tope total de fragmentos enviados al analisis


# Instancia unica reutilizable en toda la app.
settings = Settings()
