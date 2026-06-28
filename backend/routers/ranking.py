"""Endpoints del ranking (Fase 6): calculo en vivo y snapshots.

El ranking es determinista y SIN IA (regla 8). Se calcula en vivo desde la matriz
de evaluaciones con la funcion pura services.ranking.calcular_ranking. Opcionalmente
se guarda una "foto" (snapshot) para el experimento de la tesis.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, RankingSnapshot
from schemas import RankingOut, SnapshotOut
from services.ranking_query import ranking_de_proyecto

router = APIRouter(prefix="/proyectos/{proyecto_id}/ranking", tags=["ranking"])


@router.get("", response_model=RankingOut)
def obtener_ranking(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    items = ranking_de_proyecto(db, proyecto_id)
    return {"proyecto_id": proyecto_id, "items": items}


@router.post("/snapshot", response_model=SnapshotOut, status_code=201)
def guardar_snapshot(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    """Guarda una foto del ranking actual (JSONB) para comparar despues."""
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    items = ranking_de_proyecto(db, proyecto_id)
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
