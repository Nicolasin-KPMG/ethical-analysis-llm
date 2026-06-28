"""Modulo RAG (a mano, sin framework). Se implementa en M4.

- ingest.py: cargar PDF normativos, limpiar, chunquear por estructura legal,
  generar embeddings y guardarlos en pgvector.
- store.py: insertar y consultar vectores en chunk_normativo.
- retrieve.py: recuperacion (similitud + filtro por metadatos/normas activas).
"""
