"""Recuperacion de fragmentos normativos para el analisis (Fases 2-3).

Punto de entrada de alto nivel del RAG: recibe un texto de consulta, lo convierte
en vector con el proveedor de embeddings y busca los fragmentos mas relevantes,
filtrando por las normas activas del proyecto (multinorma, regla 9) y, opcional,
por jurisdiccion o tema.

El proveedor de embeddings se puede inyectar (parametro `provider`) para poder
probar la recuperacion con un proveedor determinista, sin depender de un modelo real.
"""

from models import ProyectoNormaActiva
from providers.embeddings import get_embedding_provider
from rag.store import buscar_similares


def _normas_activas(db, proyecto_id):
    """IDs de los documentos normativos activos del proyecto.

    Si el proyecto no tiene filas en proyecto_norma_activa, se interpreta como
    'todas activas' (multinorma por defecto) y se devuelve None (sin filtro).
    """
    filas = (
        db.query(ProyectoNormaActiva.documento_id)
        .filter(ProyectoNormaActiva.proyecto_id == proyecto_id)
        .all()
    )
    ids = [f[0] for f in filas]
    return ids or None


def recuperar(
    db,
    texto_consulta,
    proyecto_id=None,
    k=5,
    jurisdicciones=None,
    temas=None,
    provider=None,
):
    """Recupera los k fragmentos normativos mas relevantes para una consulta.

    Devuelve una lista de tuplas (ChunkNormativo, distancia).
    """
    provider = provider or get_embedding_provider()
    query_embedding = provider.embed([texto_consulta])[0]

    documento_ids = _normas_activas(db, proyecto_id) if proyecto_id else None

    return buscar_similares(
        db,
        query_embedding,
        k=k,
        documento_ids=documento_ids,
        jurisdicciones=jurisdicciones,
        temas=temas,
    )
