"""Endpoints de requisitos (Fase 1): crear, listar y editar.

El estado inicial siempre es 'pendiente_de_analisis' y un requisito nace vigente.
El versionado (reformulacion) y los derivados (mitigacion) pertenecen a la Fase 3
y no se implementan aqui.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, Requisito
from schemas import RequisitoCreate, RequisitoUpdate, RequisitoOut

router = APIRouter(tags=["requisitos"])


@router.post(
    "/proyectos/{proyecto_id}/requisitos",
    response_model=RequisitoOut,
    status_code=201,
)
def crear_requisito(
    proyecto_id: uuid.UUID,
    payload: RequisitoCreate,
    db: Session = Depends(get_db),
):
    # Validar que el proyecto exista antes de colgarle un requisito.
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    requisito = Requisito(
        proyecto_id=proyecto_id,
        codigo=payload.codigo,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        tipo=payload.tipo,
        stakeholder=payload.stakeholder,
        # estado y es_vigente toman sus valores por defecto en la base:
        # 'pendiente_de_analisis' y true.
    )
    db.add(requisito)
    db.commit()
    db.refresh(requisito)
    return requisito


@router.get(
    "/proyectos/{proyecto_id}/requisitos",
    response_model=list[RequisitoOut],
)
def listar_requisitos(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return (
        db.query(Requisito)
        .filter(Requisito.proyecto_id == proyecto_id)
        .order_by(Requisito.codigo)
        .all()
    )


@router.get("/requisitos/{requisito_id}", response_model=RequisitoOut)
def obtener_requisito(requisito_id: uuid.UUID, db: Session = Depends(get_db)):
    requisito = db.get(Requisito, requisito_id)
    if requisito is None:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")
    return requisito


@router.put("/requisitos/{requisito_id}", response_model=RequisitoOut)
def editar_requisito(
    requisito_id: uuid.UUID,
    payload: RequisitoUpdate,
    db: Session = Depends(get_db),
):
    requisito = db.get(Requisito, requisito_id)
    if requisito is None:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")

    # Patch parcial: solo se actualizan los campos enviados.
    datos = payload.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(requisito, campo, valor)

    db.commit()
    db.refresh(requisito)
    return requisito
