"""Esquemas Pydantic de evaluacion_dimension (Fase 5)."""

import uuid

from pydantic import BaseModel, Field


class EvaluacionUpsert(BaseModel):
    """Guarda (crea o actualiza) la evaluacion de un requisito en una dimension.

    Hay una unica fila por (requisito, dimension): si ya existe, se actualiza.
    """

    requisito_id: uuid.UUID
    dimension_id: uuid.UUID
    # Fuerza de asociacion 0 a 5; 0 = "no aplica" (validado tambien por CHECK).
    fuerza: int = Field(ge=0, le=5)
    justificacion: str | None = None
    responsable: str | None = None


class EvaluacionOut(BaseModel):
    id: uuid.UUID
    requisito_id: uuid.UUID
    dimension_id: uuid.UUID
    fuerza: int
    justificacion: str | None = None
    responsable: str | None = None

    model_config = {"from_attributes": True}
