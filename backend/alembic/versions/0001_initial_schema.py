"""Esquema inicial completo (seccion 8 del contexto).

Crea las extensiones necesarias (pgcrypto para gen_random_uuid y vector para
pgvector) y todas las tablas del modelo de datos, en orden de dependencias de FK.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Dimension del vector de embeddings. Debe coincidir con EMBEDDING_DIM y con la
# columna del modelo. Si se cambia el modelo de embeddings, hay que re-indexar.
EMBEDDING_DIM = 1024


def _uuid_pk():
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def upgrade() -> None:
    # Extensiones: gen_random_uuid() (pgcrypto) y el tipo VECTOR (pgvector).
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "proyecto",
        _uuid_pk(),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "documento_normativo",
        _uuid_pk(),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("jurisdiccion", sa.Text()),
        sa.Column("version", sa.Text()),
        sa.Column("fuente_url", sa.Text()),
    )

    op.create_table(
        "proyecto_norma_activa",
        sa.Column(
            "proyecto_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("proyecto.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "documento_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documento_normativo.id"),
            primary_key=True,
        ),
    )

    op.create_table(
        "requisito",
        _uuid_pk(),
        sa.Column(
            "proyecto_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("proyecto.id", ondelete="CASCADE"),
        ),
        sa.Column("codigo", sa.Text()),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("tipo", sa.Text()),
        sa.Column("stakeholder", sa.Text()),
        sa.Column("estado", sa.Text(), server_default=sa.text("'pendiente_de_analisis'")),
        sa.Column("es_vigente", sa.Boolean(), server_default=sa.text("true")),
        # Dos self-refs distintos sobre la misma tabla:
        sa.Column(
            "version_anterior_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requisito.id"),
        ),
        sa.Column(
            "origen_requisito_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requisito.id"),
        ),
    )

    op.create_table(
        "analisis_etico",
        _uuid_pk(),
        sa.Column(
            "requisito_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requisito.id", ondelete="CASCADE"),
        ),
        sa.Column("generado_por", sa.Text()),
        sa.Column("modelo_usado", sa.Text()),
        sa.Column("nivel_confianza", sa.Text()),
        sa.Column("limitaciones", sa.Text()),
        sa.Column("capas_2_3", postgresql.JSONB()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tema_etico_detectado",
        _uuid_pk(),
        sa.Column(
            "analisis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analisis_etico.id", ondelete="CASCADE"),
        ),
        sa.Column("tema_etico", sa.Text()),
        sa.Column("actor_afectado", sa.Text()),
        sa.Column("tipo_dano", sa.Text()),
        sa.Column("norma_tensionada_texto", sa.Text()),
        sa.Column("evidencia", sa.Text()),
    )

    # chunk_normativo antes de cita_normativa por la FK.
    op.create_table(
        "chunk_normativo",
        _uuid_pk(),
        sa.Column(
            "documento_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documento_normativo.id", ondelete="CASCADE"),
        ),
        sa.Column("referencia", sa.Text()),
        sa.Column("texto", sa.Text()),
        sa.Column("metadatos", postgresql.JSONB()),
        sa.Column("embedding", Vector(EMBEDDING_DIM)),
        sa.Column("modelo_embedding", sa.Text()),
    )

    op.create_table(
        "cita_normativa",
        _uuid_pk(),
        sa.Column(
            "tema_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tema_etico_detectado.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chunk_normativo.id"),
        ),
        sa.Column("texto_citado", sa.Text()),
    )

    op.create_table(
        "tratamiento",
        _uuid_pk(),
        sa.Column(
            "requisito_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requisito.id", ondelete="CASCADE"),
        ),
        sa.Column("decision", sa.Text()),
        sa.Column("justificacion", sa.Text()),
        sa.Column("responsable", sa.Text()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "relacion_requisito",
        _uuid_pk(),
        sa.Column(
            "origen_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requisito.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "derivado_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requisito.id", ondelete="CASCADE"),
        ),
        sa.Column("tipo_relacion", sa.Text()),
        sa.Column("obligatorio", sa.Boolean(), server_default=sa.text("true")),
    )

    op.create_table(
        "dimension",
        _uuid_pk(),
        sa.Column(
            "proyecto_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("proyecto.id", ondelete="CASCADE"),
        ),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("peso", sa.Integer()),
        sa.Column("justificacion_peso", sa.Text()),
        sa.CheckConstraint("peso BETWEEN 1 AND 5", name="ck_dimension_peso"),
    )

    op.create_table(
        "evaluacion_dimension",
        _uuid_pk(),
        sa.Column(
            "requisito_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requisito.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "dimension_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dimension.id", ondelete="CASCADE"),
        ),
        sa.Column("fuerza", sa.Integer()),
        sa.Column("justificacion", sa.Text()),
        sa.Column("responsable", sa.Text()),
        sa.CheckConstraint("fuerza BETWEEN 0 AND 5", name="ck_evaluacion_fuerza"),
        sa.UniqueConstraint("requisito_id", "dimension_id", name="uq_evaluacion_req_dim"),
    )

    op.create_table(
        "ranking_snapshot",
        _uuid_pk(),
        sa.Column(
            "proyecto_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("proyecto.id", ondelete="CASCADE"),
        ),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("datos", postgresql.JSONB()),
    )


def downgrade() -> None:
    # Orden inverso a la creacion.
    op.drop_table("ranking_snapshot")
    op.drop_table("evaluacion_dimension")
    op.drop_table("dimension")
    op.drop_table("relacion_requisito")
    op.drop_table("tratamiento")
    op.drop_table("cita_normativa")
    op.drop_table("chunk_normativo")
    op.drop_table("tema_etico_detectado")
    op.drop_table("analisis_etico")
    op.drop_table("requisito")
    op.drop_table("proyecto_norma_activa")
    op.drop_table("documento_normativo")
    op.drop_table("proyecto")
