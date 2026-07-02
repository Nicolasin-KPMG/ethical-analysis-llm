"""Esquemas Pydantic de dimension (Fase 4)."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

# Tipos de dimension (seccion 4). Beneficio y valor_etico suman; costo y
# riesgo_etico restan en el calculo del ranking.
TipoDimension = Literal["beneficio", "valor_etico", "costo", "riesgo_etico"]


class DimensionCreate(BaseModel):
    nombre: str
    tipo: TipoDimension
    descripcion: str | None = None
    # Peso 1 a 5 (validado tambien por CHECK en la base).
    peso: int = Field(ge=1, le=5)
    justificacion_peso: str | None = None


class DimensionUpdate(BaseModel):
    nombre: str | None = None
    tipo: TipoDimension | None = None
    descripcion: str | None = None
    peso: int | None = Field(default=None, ge=1, le=5)
    justificacion_peso: str | None = None


class DimensionOut(BaseModel):
    id: uuid.UUID
    proyecto_id: uuid.UUID | None = None
    nombre: str
    tipo: str
    descripcion: str | None = None
    peso: int | None = None
    justificacion_peso: str | None = None
    # Aplicabilidad: si la dimension es "restringida" (tiene aplicabilidad
    # definida), solo aplica a estos requisitos; para el resto la celda de la
    # matriz de evaluacion queda fija en 0. Vacio + restringida=False => aplica a
    # todos (dimensiones generales: beneficio/costo).
    restringida: bool = False
    requisitos_aplica: list[uuid.UUID] = []

    model_config = {"from_attributes": True}
