"""Esquemas Pydantic de dimension (Fase 4)."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

# Tipos de dimension (seccion 4). Beneficio y valor_etico suman; costo y
# riesgo_etico_residual restan en el calculo del ranking.
TipoDimension = Literal["beneficio", "valor_etico", "costo", "riesgo_etico_residual"]


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

    model_config = {"from_attributes": True}
