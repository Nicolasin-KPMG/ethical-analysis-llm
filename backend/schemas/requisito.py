"""Esquemas Pydantic del requisito (Fase 1)."""

import uuid
from typing import Literal

from pydantic import BaseModel

# Tipos permitidos del requisito (seccion 4, Fase 1).
TipoRequisito = Literal["funcional", "no_funcional", "restriccion", "otro"]


class RequisitoCreate(BaseModel):
    """Datos para registrar un requisito. El estado lo fija el backend
    en 'pendiente_de_analisis'; no se acepta desde el cliente en Fase 1.
    """

    codigo: str | None = None
    nombre: str
    descripcion: str | None = None
    tipo: TipoRequisito | None = None
    stakeholder: str | None = None


class RequisitoUpdate(BaseModel):
    """Edicion de un requisito. Todos los campos son opcionales (patch parcial).

    Nota: en Fase 1 solo se editan estos campos descriptivos. El cambio de
    estado, el versionado (reformulacion) y los derivados (mitigacion) son
    parte de la Fase 3 y no se exponen aqui.
    """

    codigo: str | None = None
    nombre: str | None = None
    descripcion: str | None = None
    tipo: TipoRequisito | None = None
    stakeholder: str | None = None


class RequisitoOut(BaseModel):
    id: uuid.UUID
    proyecto_id: uuid.UUID | None = None
    codigo: str | None = None
    nombre: str
    descripcion: str | None = None
    tipo: str | None = None
    stakeholder: str | None = None
    estado: str | None = None
    es_vigente: bool | None = None
    version_anterior_id: uuid.UUID | None = None
    origen_requisito_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}
