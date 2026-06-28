"""Endpoints del ranking (Fase 6): calculo en vivo y snapshots.

El ranking es determinista y SIN IA (regla 8). Se calcula en vivo desde la matriz
de evaluaciones con la funcion pura services.ranking.calcular_ranking. Opcionalmente
se guarda una "foto" (snapshot) para el experimento de la tesis.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, Dimension, EvaluacionDimension, Requisito, RankingSnapshot
from schemas import RankingOut, SnapshotOut
from services.ranking import calcular_ranking
from services.requisitos_query import requisitos_rankeables

router = APIRouter(prefix="/proyectos/{proyecto_id}/ranking", tags=["ranking"])


def _calcular(proyecto_id: uuid.UUID, db: Session):
    """Reune los datos del proyecto y delega en la funcion pura de ranking."""
    requisitos = requisitos_rankeables(db, proyecto_id)
    dimensiones = (
        db.query(Dimension).filter(Dimension.proyecto_id == proyecto_id).all()
    )
    # Solo las evaluaciones de los requisitos rankeables.
    ids_rankeables = [r.id for r in requisitos]
    evaluaciones = (
        db.query(EvaluacionDimension)
        .filter(EvaluacionDimension.requisito_id.in_(ids_rankeables))
        .all()
        if ids_rankeables
        else []
    )
    return calcular_ranking(requisitos, dimensiones, evaluaciones)


@router.get("", response_model=RankingOut)
def obtener_ranking(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    items = _calcular(proyecto_id, db)
    return {"proyecto_id": proyecto_id, "items": items}


@router.post("/snapshot", response_model=SnapshotOut, status_code=201)
def guardar_snapshot(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    """Guarda una foto del ranking actual (JSONB) para comparar despues."""
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    items = _calcular(proyecto_id, db)
    snapshot = RankingSnapshot(proyecto_id=proyecto_id, datos={"items": items})
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get("/snapshots", response_model=list[SnapshotOut])
def listar_snapshots(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return (
        db.query(RankingSnapshot)
        .filter(RankingSnapshot.proyecto_id == proyecto_id)
        .order_by(RankingSnapshot.creado_en.desc())
        .all()
    )
