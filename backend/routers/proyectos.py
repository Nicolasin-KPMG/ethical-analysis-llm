"""Endpoints de proyectos: crear y listar.

(Configurar normas activas se agrega cuando se construya el RAG / multinorma.)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto
from schemas import ProyectoCreate, ProyectoOut

router = APIRouter(prefix="/proyectos", tags=["proyectos"])


@router.post("", response_model=ProyectoOut, status_code=201)
def crear_proyecto(payload: ProyectoCreate, db: Session = Depends(get_db)):
    proyecto = Proyecto(nombre=payload.nombre, descripcion=payload.descripcion)
    db.add(proyecto)
    db.commit()
    db.refresh(proyecto)
    return proyecto


@router.get("", response_model=list[ProyectoOut])
def listar_proyectos(db: Session = Depends(get_db)):
    return db.query(Proyecto).order_by(Proyecto.fecha_creacion.desc()).all()


@router.get("/{proyecto_id}", response_model=ProyectoOut)
def obtener_proyecto(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto
