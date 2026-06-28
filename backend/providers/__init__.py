"""Capa de proveedores enchufables.

La app nunca llama directamente a un SDK. Llama a estas interfaces.
`get_llm_provider()` y `get_embedding_provider()` eligen la implementacion
concreta segun las variables de entorno.
"""

from providers.llm import LLMProvider, get_llm_provider
from providers.embeddings import EmbeddingProvider, get_embedding_provider

__all__ = [
    "LLMProvider",
    "EmbeddingProvider",
    "get_llm_provider",
    "get_embedding_provider",
]
