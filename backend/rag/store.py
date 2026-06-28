"""Almacenamiento y busqueda vectorial sobre chunk_normativo (pgvector).

Estas funciones trabajan con vectores ya calculados (no llaman al modelo de
embeddings), asi que son faciles de probar de forma aislada.
"""

from sqlalchemy import select

from models import ChunkNormativo, DocumentoNormativo


def guardar_chunk(db, documento_id, referencia, texto, metadatos, embedding, modelo_embedding):
    """Inserta un fragmento normativo con su vector. Devuelve el ChunkNormativo."""
    chunk = ChunkNormativo(
        documento_id=documento_id,
        referencia=referencia,
        texto=texto,
        metadatos=metadatos,
        embedding=embedding,
        modelo_embedding=modelo_embedding,
    )
    db.add(chunk)
    return chunk


def buscar_similares(
    db,
    query_embedding,
    k=5,
    documento_ids=None,
    jurisdicciones=None,
    temas=None,
):
    """Busca los k fragmentos mas similares al vector de consulta.

    Combina similitud semantica (distancia coseno en pgvector) con filtros por
    metadatos:
      - documento_ids: restringe a esas normas (p.ej. las activas del proyecto).
      - jurisdicciones: restringe por jurisdiccion del documento (UE, Chile, ...).
      - temas: restringe por el tema guardado en metadatos JSONB.

    Devuelve una lista de tuplas (ChunkNormativo, distancia), de mas a menos
    parecido (distancia ascendente).
    """
    distancia = ChunkNormativo.embedding.cosine_distance(query_embedding)
    stmt = select(ChunkNormativo, distancia.label("distancia"))

    # Filtro por normas (documentos) concretas.
    if documento_ids:
        stmt = stmt.where(ChunkNormativo.documento_id.in_(documento_ids))

    # Filtro por jurisdiccion: se resuelve uniendo con el documento.
    if jurisdicciones:
        stmt = stmt.join(
            DocumentoNormativo,
            ChunkNormativo.documento_id == DocumentoNormativo.id,
        ).where(DocumentoNormativo.jurisdiccion.in_(jurisdicciones))

    # Filtro por tema, guardado dentro del JSONB de metadatos.
    if temas:
        stmt = stmt.where(ChunkNormativo.metadatos["tema"].astext.in_(temas))

    stmt = stmt.order_by(distancia).limit(k)
    return [(row[0], row[1]) for row in db.execute(stmt).all()]
