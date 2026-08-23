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

    # --- Autenticacion (login con JWT) ---
    # Secreto para firmar los tokens. CAMBIAR en cualquier despliegue real; el
    # valor por defecto es solo para desarrollo local.
    jwt_secret: str = "dev-secret-cambiar-en-produccion"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 horas

    # --- Proveedor de LLM ---
    llm_provider: str = "anthropic"  # "anthropic" | "openai" | "local"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # Endpoint compatible con OpenAI. Vacio = la API de OpenAI. Se rellena para
    # usar otro proveedor con el mismo cliente (p. ej. Gemini o Groq, que exponen
    # una capa compatible): asi cambiar de LLM no toca codigo, solo el .env.
    openai_base_url: str = ""
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "llama3.1:8b"

    # --- Proveedor de embeddings (pieza aparte: Anthropic no genera embeddings) ---
    embedding_provider: str = "hosted"  # "hosted" | "local" | "openai"
    embedding_model_hosted: str = "voyage-3"
    # Modelo de OpenAI cuando embedding_provider == "openai" (reutiliza OPENAI_API_KEY).
    # text-embedding-3-small acepta `dimensions` y se recorta a EMBEDDING_DIM (1024).
    embedding_model_openai: str = "text-embedding-3-small"
    # Endpoint compatible con OpenAI para embeddings (mismo motivo que arriba).
    # Independiente del LLM: se puede mezclar un LLM y otros embeddings.
    embedding_openai_base_url: str = ""
    # Credencial propia para los embeddings. Si queda vacia se usa
    # OPENAI_API_KEY. Hace falta cuando el LLM y los embeddings son de
    # proveedores distintos (p. ej. LLM en Gemini y embeddings en OpenAI),
    # porque entonces cada uno necesita su propia clave.
    embedding_openai_api_key: str = ""
    # Tope de textos embebidos por minuto. 0 = sin limite. El tier gratis de
    # Gemini permite 100 req/min y su capa compatible cuenta un request por
    # texto, asi que con 844 fragmentos hay que ir a ritmo o revienta con 429.
    embedding_rpm: int = 0
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

    # --- Despliegue ---
    # Origenes permitidos por CORS, separados por coma. "*" abre todo (local).
    cors_origins: str = "*"


# Instancia unica reutilizable en toda la app.
settings = Settings()
