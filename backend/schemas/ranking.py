"""Esquemas Pydantic del ranking (Fase 6)."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class DesgloseRanking(BaseModel):
    """Suma por categoria de dimension (Σ peso × fuerza)."""

    beneficio: int
    valor_etico: int
    costo: int
    riesgo_etico_residual: int


class RankingItem(BaseModel):
    requisito_id: str
    codigo: str | None = None
    nombre: str
    puntaje_final: int
    desglose: DesgloseRanking


class RankingOut(BaseModel):
    proyecto_id: uuid.UUID
    items: list[RankingItem]


class SnapshotOut(BaseModel):
    id: uuid.UUID
    proyecto_id: uuid.UUID
    creado_en: datetime | None = None
    datos: dict | None = None

    model_config = {"from_attributes": True}
