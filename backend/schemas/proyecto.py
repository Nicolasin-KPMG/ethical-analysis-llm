"""Esquemas Pydantic del proyecto."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: str | None = None


class ProyectoOut(BaseModel):
    id: uuid.UUID
    nombre: str
    descripcion: str | None = None
    fecha_creacion: datetime | None = None

    # Permite construir el esquema directamente desde el modelo SQLAlchemy.
    model_config = {"from_attributes": True}
