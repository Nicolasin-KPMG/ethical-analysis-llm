"""Modelos SQLAlchemy. Importa el modulo para que Alembic detecte las tablas."""

from models.models import (
    Proyecto,
    DocumentoNormativo,
    ProyectoNormaActiva,
    Requisito,
    AnalisisEtico,
    TemaEticoDetectado,
    CitaNormativa,
    Tratamiento,
    RelacionRequisito,
    Dimension,
    EvaluacionDimension,
    RankingSnapshot,
    ChunkNormativo,
)

__all__ = [
    "Proyecto",
    "DocumentoNormativo",
    "ProyectoNormaActiva",
    "Requisito",
    "AnalisisEtico",
    "TemaEticoDetectado",
    "CitaNormativa",
    "Tratamiento",
    "RelacionRequisito",
    "Dimension",
    "EvaluacionDimension",
    "RankingSnapshot",
    "ChunkNormativo",
]
