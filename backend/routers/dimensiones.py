"""Endpoints de dimensiones (Fase 4): CRUD por proyecto.

Cada proyecto define sus propias dimensiones de priorizacion. El tipo determina
si la dimension suma (beneficio, valor_etico) o resta (costo, riesgo_etico_residual)
en el ranking de la Fase 6.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, Dimension
from schemas import DimensionCreate, DimensionUpdate, DimensionOut

router = APIRouter(tags=["dimensiones"])


@router.post(
    "/proyectos/{proyecto_id}/dimensiones",
    response_model=DimensionOut,
    status_code=201,
)
def crear_dimension(
    proyecto_id: uuid.UUID,
    payload: DimensionCreate,
    db: Session = Depends(get_db),
):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    dimension = Dimension(
        proyecto_id=proyecto_id,
        nombre=payload.nombre,
        tipo=payload.tipo,
        descripcion=payload.descripcion,
        peso=payload.peso,
        justificacion_peso=payload.justificacion_peso,
    )
    db.add(dimension)
    db.commit()
    db.refresh(dimension)
    return dimension


@router.get(
    "/proyectos/{proyecto_id}/dimensiones",
    response_model=list[DimensionOut],
)
def listar_dimensiones(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return (
        db.query(Dimension)
        .filter(Dimension.proyecto_id == proyecto_id)
        .order_by(Dimension.tipo, Dimension.nombre)
        .all()
    )


@router.put("/dimensiones/{dimension_id}", response_model=DimensionOut)
def editar_dimension(
    dimension_id: uuid.UUID,
    payload: DimensionUpdate,
    db: Session = Depends(get_db),
):
    dimension = db.get(Dimension, dimension_id)
    if dimension is None:
        raise HTTPException(status_code=404, detail="Dimension no encontrada")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(dimension, campo, valor)

    db.commit()
    db.refresh(dimension)
    return dimension


@router.delete("/dimensiones/{dimension_id}", status_code=204)
def eliminar_dimension(dimension_id: uuid.UUID, db: Session = Depends(get_db)):
    # Borrado real: las evaluaciones asociadas caen por ON DELETE CASCADE.
    dimension = db.get(Dimension, dimension_id)
    if dimension is None:
        raise HTTPException(status_code=404, detail="Dimension no encontrada")
    db.delete(dimension)
    db.commit()
