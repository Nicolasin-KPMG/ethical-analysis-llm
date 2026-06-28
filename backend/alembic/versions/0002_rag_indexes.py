"""Indices para el RAG sobre chunk_normativo.

- Indice HNSW sobre el embedding con operador de distancia coseno: acelera la
  busqueda por similitud (se puede crear sobre la tabla vacia).
- Indice btree sobre documento_id: acelera el filtro por normas activas.

Revision ID: 0002_rag_indexes
Revises: 0001_initial
Create Date: 2026-06-28
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_rag_indexes"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunk_embedding_hnsw "
        "ON chunk_normativo USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chunk_documento_id "
        "ON chunk_normativo (documento_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunk_documento_id")
    op.execute("DROP INDEX IF EXISTS ix_chunk_embedding_hnsw")
