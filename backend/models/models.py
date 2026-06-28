"""Modelo de datos completo (PostgreSQL), reflejando seccion 8 del contexto.

Notas de diseno importantes:
- Se crean TODAS las tablas del contexto, no solo las de la Fase 1, para tener
  el esquema completo desde M1 (las fases posteriores solo agregaran logica).
- `requisito` tiene DOS enlaces self-referenciales distintos:
    * version_anterior_id -> cadena de versiones (reformulacion)
    * origen_requisito_id -> relacion padre-hijo (mitigacion / derivado)
  No deben confundirse.
- `es_vigente` distingue la version vigente (la unica que se evalua y rankea)
  de las versiones archivadas como historial.
- Los UUID se generan en la base con gen_random_uuid() (extension pgcrypto,
  disponible en la imagen de Postgres).
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector

from config import settings
from database import Base


def _pk():
    """Columna de clave primaria UUID generada por la base de datos."""
    return Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class Proyecto(Base):
    __tablename__ = "proyecto"

    id = _pk()
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())


class DocumentoNormativo(Base):
    __tablename__ = "documento_normativo"

    id = _pk()
    nombre = Column(Text, nullable=False)  # EU AI Act, GDPR, Boletin 16821-19, etc.
    jurisdiccion = Column(Text)            # UE, EEUU, Chile
    version = Column(Text)
    fuente_url = Column(Text)


class ProyectoNormaActiva(Base):
    """Multinorma con checkbox; por defecto todas activas (clave compuesta)."""

    __tablename__ = "proyecto_norma_activa"

    proyecto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyecto.id", ondelete="CASCADE"),
        primary_key=True,
    )
    documento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documento_normativo.id"),
        primary_key=True,
    )


class Requisito(Base):
    __tablename__ = "requisito"

    id = _pk()
    proyecto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyecto.id", ondelete="CASCADE"),
    )
    codigo = Column(Text)
    nombre = Column(Text, nullable=False)
    descripcion = Column(Text)
    tipo = Column(Text)            # funcional, no funcional, restriccion, otro
    stakeholder = Column(Text)
    # El estado inicial de un requisito es "pendiente de analisis".
    estado = Column(Text, server_default=text("'pendiente_de_analisis'"))
    es_vigente = Column(Boolean, server_default=text("true"))

    # Dos self-refs DISTINTOS sobre la misma tabla:
    version_anterior_id = Column(UUID(as_uuid=True), ForeignKey("requisito.id"))
    origen_requisito_id = Column(UUID(as_uuid=True), ForeignKey("requisito.id"))


class AnalisisEtico(Base):
    """Fase 2-3: capas 2 y 3 + metadatos del analisis."""

    __tablename__ = "analisis_etico"

    id = _pk()
    requisito_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requisito.id", ondelete="CASCADE"),
    )
    generado_por = Column(Text)       # llm | humano
    modelo_usado = Column(Text)
    nivel_confianza = Column(Text)    # alta | media | baja
    limitaciones = Column(Text)
    capas_2_3 = Column(JSONB)         # mapa stakeholders, tensiones, opciones, preguntas, etc.
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class TemaEticoDetectado(Base):
    """Fase 2, capa 1 en columnas relacionales."""

    __tablename__ = "tema_etico_detectado"

    id = _pk()
    analisis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analisis_etico.id", ondelete="CASCADE"),
    )
    tema_etico = Column(Text)
    actor_afectado = Column(Text)
    tipo_dano = Column(Text)
    norma_tensionada_texto = Column(Text)
    evidencia = Column(Text)


class ChunkNormativo(Base):
    """RAG (pgvector). Definido antes de cita_normativa por la FK.

    `embedding` usa la dimension configurada (debe coincidir con el modelo).
    `modelo_embedding` se guarda junto al vector para detectar incompatibilidades
    al cambiar de modelo.
    """

    __tablename__ = "chunk_normativo"

    id = _pk()
    documento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documento_normativo.id", ondelete="CASCADE"),
    )
    referencia = Column(Text)            # articulo / seccion
    texto = Column(Text)
    metadatos = Column(JSONB)            # norma, jurisdiccion, tema
    embedding = Column(Vector(settings.embedding_dim))
    modelo_embedding = Column(Text)


class CitaNormativa(Base):
    """Trazabilidad: tema detectado -> fragmento normativo concreto."""

    __tablename__ = "cita_normativa"

    id = _pk()
    tema_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tema_etico_detectado.id", ondelete="CASCADE"),
    )
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunk_normativo.id"))
    texto_citado = Column(Text)


class Tratamiento(Base):
    """Fase 3."""

    __tablename__ = "tratamiento"

    id = _pk()
    requisito_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requisito.id", ondelete="CASCADE"),
    )
    decision = Column(Text)        # aceptar | reformular | mitigar | eliminar
    justificacion = Column(Text)
    responsable = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class RelacionRequisito(Base):
    """Fase 7: relaciones origen-derivado."""

    __tablename__ = "relacion_requisito"

    id = _pk()
    origen_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requisito.id", ondelete="CASCADE"),
    )
    derivado_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requisito.id", ondelete="CASCADE"),
    )
    tipo_relacion = Column(Text)
    obligatorio = Column(Boolean, server_default=text("true"))


class Dimension(Base):
    """Fase 4: dimensiones de priorizacion del proyecto."""

    __tablename__ = "dimension"

    id = _pk()
    proyecto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyecto.id", ondelete="CASCADE"),
    )
    nombre = Column(Text, nullable=False)
    # beneficio | valor_etico | costo | riesgo_etico_residual
    tipo = Column(Text, nullable=False)
    descripcion = Column(Text)
    peso = Column(Integer)
    justificacion_peso = Column(Text)

    __table_args__ = (
        CheckConstraint("peso BETWEEN 1 AND 5", name="ck_dimension_peso"),
    )


class EvaluacionDimension(Base):
    """Fase 5: matriz requisito x dimension (solo requisitos vigentes)."""

    __tablename__ = "evaluacion_dimension"

    id = _pk()
    requisito_id = Column(
        UUID(as_uuid=True),
        ForeignKey("requisito.id", ondelete="CASCADE"),
    )
    dimension_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dimension.id", ondelete="CASCADE"),
    )
    fuerza = Column(Integer)       # 0 a 5; 0 = no aplica
    justificacion = Column(Text)
    responsable = Column(Text)

    __table_args__ = (
        CheckConstraint("fuerza BETWEEN 0 AND 5", name="ck_evaluacion_fuerza"),
        UniqueConstraint("requisito_id", "dimension_id", name="uq_evaluacion_req_dim"),
    )


class RankingSnapshot(Base):
    """Fase 6/8: foto opcional del ranking para el experimento."""

    __tablename__ = "ranking_snapshot"

    id = _pk()
    proyecto_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proyecto.id", ondelete="CASCADE"),
    )
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    datos = Column(JSONB)
