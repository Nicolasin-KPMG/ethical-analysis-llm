"""Endpoints de evaluaciones (Fase 5): guardar y listar la matriz requisito×dimension.

Cada requisito vigente se evalua frente a cada dimension con una fuerza de 0 a 5
(0 = no aplica). Hay una unica fila por (requisito, dimension): si ya existe, se
actualiza (upsert).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, Requisito, Dimension, EvaluacionDimension
from schemas import EvaluacionUpsert, EvaluacionOut

router = APIRouter(tags=["evaluaciones"])


@router.put(
    "/proyectos/{proyecto_id}/evaluaciones",
    response_model=EvaluacionOut,
)
def guardar_evaluacion(
    proyecto_id: uuid.UUID,
    payload: EvaluacionUpsert,
    db: Session = Depends(get_db),
):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # El requisito debe existir, pertenecer al proyecto, estar vigente y no
    # eliminado (reglas 2 y 5): solo esos se evaluan.
    requisito = db.get(Requisito, payload.requisito_id)
    if requisito is None or requisito.proyecto_id != proyecto_id:
        raise HTTPException(status_code=404, detail="Requisito no encontrado en el proyecto")
    if not requisito.es_vigente or requisito.estado == "eliminado":
        raise HTTPException(
            status_code=400,
            detail="Solo se evaluan requisitos vigentes y no eliminados",
        )

    # La dimension debe existir y pertenecer al proyecto.
    dimension = db.get(Dimension, payload.dimension_id)
    if dimension is None or dimension.proyecto_id != proyecto_id:
        raise HTTPException(status_code=404, detail="Dimension no encontrada en el proyecto")

    # Upsert: busca la fila existente por la clave (requisito, dimension).
    evaluacion = (
        db.query(EvaluacionDimension)
        .filter(
            EvaluacionDimension.requisito_id == payload.requisito_id,
            EvaluacionDimension.dimension_id == payload.dimension_id,
        )
        .one_or_none()
    )
    if evaluacion is None:
        evaluacion = EvaluacionDimension(
            requisito_id=payload.requisito_id,
            dimension_id=payload.dimension_id,
        )
        db.add(evaluacion)

    evaluacion.fuerza = payload.fuerza
    evaluacion.justificacion = payload.justificacion
    evaluacion.responsable = payload.responsable

    db.commit()
    db.refresh(evaluacion)
    return evaluacion


@router.get(
    "/proyectos/{proyecto_id}/evaluaciones",
    response_model=list[EvaluacionOut],
)
def listar_evaluaciones(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    """Lista todas las evaluaciones del proyecto (la matriz completa)."""
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Join con requisito para acotar al proyecto.
    return (
        db.query(EvaluacionDimension)
        .join(Requisito, EvaluacionDimension.requisito_id == Requisito.id)
        .filter(Requisito.proyecto_id == proyecto_id)
        .all()
    )
