"""Endpoints de la Fase 7: gestion de derivados y trazabilidad.

- CRUD de relacion_requisito (origen -> derivado).
- Trazabilidad con la "regla de arrastre": un derivado OBLIGATORIO no deberia
  quedar por debajo (peor puntaje) del requisito que mitiga. Es informativa
  (una bandera), no bloquea, en linea con el principio del metodo.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, Requisito, RelacionRequisito
from schemas import RelacionCreate, RelacionUpdate, RelacionOut, TrazabilidadOut
from services.ranking_query import ranking_de_proyecto

router = APIRouter(tags=["relaciones"])


def _relacion_out(db: Session, rel: RelacionRequisito) -> dict:
    origen = db.get(Requisito, rel.origen_id)
    derivado = db.get(Requisito, rel.derivado_id)
    return {
        "id": rel.id,
        "tipo_relacion": rel.tipo_relacion,
        "obligatorio": rel.obligatorio,
        "origen": origen,
        "derivado": derivado,
    }


@router.get("/proyectos/{proyecto_id}/relaciones", response_model=list[RelacionOut])
def listar_relaciones(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    # Relaciones cuyo origen pertenece al proyecto.
    rels = (
        db.query(RelacionRequisito)
        .join(Requisito, RelacionRequisito.origen_id == Requisito.id)
        .filter(Requisito.proyecto_id == proyecto_id)
        .all()
    )
    return [_relacion_out(db, r) for r in rels]


@router.post("/relaciones", response_model=RelacionOut, status_code=201)
def crear_relacion(payload: RelacionCreate, db: Session = Depends(get_db)):
    origen = db.get(Requisito, payload.origen_id)
    derivado = db.get(Requisito, payload.derivado_id)
    if origen is None or derivado is None:
        raise HTTPException(status_code=404, detail="Origen o derivado no encontrado")
    if origen.proyecto_id != derivado.proyecto_id:
        raise HTTPException(status_code=400, detail="Origen y derivado de proyectos distintos")

    rel = RelacionRequisito(
        origen_id=payload.origen_id,
        derivado_id=payload.derivado_id,
        tipo_relacion=payload.tipo_relacion,
        obligatorio=payload.obligatorio,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return _relacion_out(db, rel)


@router.put("/relaciones/{relacion_id}", response_model=RelacionOut)
def editar_relacion(
    relacion_id: uuid.UUID, payload: RelacionUpdate, db: Session = Depends(get_db)
):
    rel = db.get(RelacionRequisito, relacion_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relacion no encontrada")
    if payload.tipo_relacion is not None:
        rel.tipo_relacion = payload.tipo_relacion
    if payload.obligatorio is not None:
        rel.obligatorio = payload.obligatorio
    db.commit()
    db.refresh(rel)
    return _relacion_out(db, rel)


@router.delete("/relaciones/{relacion_id}", status_code=204)
def eliminar_relacion(relacion_id: uuid.UUID, db: Session = Depends(get_db)):
    rel = db.get(RelacionRequisito, relacion_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relacion no encontrada")
    db.delete(rel)
    db.commit()


@router.get("/proyectos/{proyecto_id}/trazabilidad", response_model=TrazabilidadOut)
def trazabilidad(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Posicion y puntaje de cada requisito en el ranking vigente.
    ranking = ranking_de_proyecto(db, proyecto_id)
    info = {
        it["requisito_id"]: {"posicion": i, "puntaje": it["puntaje_final"]}
        for i, it in enumerate(ranking, start=1)
    }

    rels = (
        db.query(RelacionRequisito)
        .join(Requisito, RelacionRequisito.origen_id == Requisito.id)
        .filter(Requisito.proyecto_id == proyecto_id)
        .all()
    )

    items = []
    for rel in rels:
        origen = db.get(Requisito, rel.origen_id)
        derivado = db.get(Requisito, rel.derivado_id)
        o = info.get(str(rel.origen_id), {})
        d = info.get(str(rel.derivado_id), {})

        # Regla de arrastre: derivado obligatorio por debajo del padre.
        violada = (
            bool(rel.obligatorio)
            and o.get("puntaje") is not None
            and d.get("puntaje") is not None
            and d["puntaje"] < o["puntaje"]
        )

        items.append(
            {
                "relacion_id": rel.id,
                "tipo_relacion": rel.tipo_relacion,
                "obligatorio": rel.obligatorio,
                "origen_codigo": origen.codigo if origen else None,
                "origen_nombre": origen.nombre if origen else "(?)",
                "origen_puntaje": o.get("puntaje"),
                "origen_posicion": o.get("posicion"),
                "derivado_codigo": derivado.codigo if derivado else None,
                "derivado_nombre": derivado.nombre if derivado else "(?)",
                "derivado_puntaje": d.get("puntaje"),
                "derivado_posicion": d.get("posicion"),
                "arrastre_violada": violada,
            }
        )

    return {"proyecto_id": proyecto_id, "items": items}
