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
]
