"""Esquemas Pydantic de relaciones entre requisitos y trazabilidad (Fase 7)."""

import uuid
from typing import Optional

from pydantic import BaseModel


class RequisitoMini(BaseModel):
    id: uuid.UUID
    codigo: Optional[str] = None
    nombre: str
    estado: Optional[str] = None
    es_vigente: Optional[bool] = None

    model_config = {"from_attributes": True}


class RelacionCreate(BaseModel):
    origen_id: uuid.UUID
    derivado_id: uuid.UUID
    tipo_relacion: str = "mitigacion"
    obligatorio: bool = True


class RelacionUpdate(BaseModel):
    tipo_relacion: Optional[str] = None
    obligatorio: Optional[bool] = None


class RelacionOut(BaseModel):
    id: uuid.UUID
    tipo_relacion: Optional[str] = None
    obligatorio: Optional[bool] = None
    origen: RequisitoMini
    derivado: RequisitoMini


class TrazabilidadItem(BaseModel):
    """Una relacion origen-derivado con su posicion/puntaje en el ranking.

    `arrastre_violada` marca la regla del contexto: un derivado OBLIGATORIO no
    deberia quedar por debajo (peor puntaje) del requisito que mitiga. Informa,
    no bloquea.
    """

    relacion_id: uuid.UUID
    tipo_relacion: Optional[str] = None
    obligatorio: Optional[bool] = None

    origen_codigo: Optional[str] = None
    origen_nombre: str
    origen_puntaje: Optional[int] = None
    origen_posicion: Optional[int] = None

    derivado_codigo: Optional[str] = None
    derivado_nombre: str
    derivado_puntaje: Optional[int] = None
    derivado_posicion: Optional[int] = None

    arrastre_violada: bool = False


class TrazabilidadOut(BaseModel):
    proyecto_id: uuid.UUID
    items: list[TrazabilidadItem]
