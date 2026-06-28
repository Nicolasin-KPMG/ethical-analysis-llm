"""Esquemas Pydantic (validacion de entrada/salida de la API).

Fase 1 (proyecto, requisito) y M2 (dimension, evaluacion, ranking).
El esquema de salida del LLM (tres capas) se agrega en M5.
"""

from schemas.proyecto import ProyectoCreate, ProyectoOut
from schemas.requisito import RequisitoCreate, RequisitoUpdate, RequisitoOut
from schemas.dimension import DimensionCreate, DimensionUpdate, DimensionOut
from schemas.evaluacion import EvaluacionUpsert, EvaluacionOut
from schemas.ranking import RankingItem, RankingOut, SnapshotOut, DesgloseRanking
from schemas.visualizacion import VisualizacionItem, VisualizacionOut
from schemas.documento import DocumentoCreate, DocumentoOut, NormasActivasUpdate
from schemas.analisis import (
    AnalisisLLM,
    PrimeraPasada,
    AnalisisOut,
    AnalisisUpdate,
    TemaOut,
    CitaOut,
    TratamientoCreate,
    TratamientoOut,
)
from schemas.relacion import (
    RelacionCreate,
    RelacionUpdate,
    RelacionOut,
    RequisitoMini,
    TrazabilidadItem,
    TrazabilidadOut,
)

__all__ = [
    "ProyectoCreate",
    "ProyectoOut",
    "RequisitoCreate",
    "RequisitoUpdate",
    "RequisitoOut",
    "DimensionCreate",
    "DimensionUpdate",
    "DimensionOut",
    "EvaluacionUpsert",
    "EvaluacionOut",
    "RankingItem",
    "RankingOut",
    "SnapshotOut",
    "DesgloseRanking",
    "VisualizacionItem",
    "VisualizacionOut",
    "DocumentoCreate",
    "DocumentoOut",
    "NormasActivasUpdate",
    "AnalisisLLM",
    "PrimeraPasada",
    "AnalisisOut",
    "AnalisisUpdate",
    "TemaOut",
    "CitaOut",
    "TratamientoCreate",
    "TratamientoOut",
    "RelacionCreate",
    "RelacionUpdate",
    "RelacionOut",
    "RequisitoMini",
    "TrazabilidadItem",
    "TrazabilidadOut",
]
