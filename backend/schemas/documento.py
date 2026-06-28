"""Esquemas Pydantic de documentos normativos y normas activas por proyecto."""

import uuid

from pydantic import BaseModel


class DocumentoCreate(BaseModel):
    nombre: str
    jurisdiccion: str | None = None
    version: str | None = None
    fuente_url: str | None = None


class DocumentoOut(BaseModel):
    id: uuid.UUID
    nombre: str
    jurisdiccion: str | None = None
    version: str | None = None
    fuente_url: str | None = None

    model_config = {"from_attributes": True}


class NormasActivasUpdate(BaseModel):
    """Lista de documentos activos para un proyecto (multinorma, regla 9)."""

    documento_ids: list[uuid.UUID]
