"""Endpoints de documentos normativos y de normas activas por proyecto.

Soportan la regla 9 (multinorma): por defecto un proyecto contrasta contra todas
las normas; si tiene filas en proyecto_norma_activa, el RAG se limita a esas.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, DocumentoNormativo, ProyectoNormaActiva
from schemas import DocumentoCreate, DocumentoOut, NormasActivasUpdate

router = APIRouter(tags=["documentos"])


@router.post("/documentos", response_model=DocumentoOut, status_code=201)
def crear_documento(payload: DocumentoCreate, db: Session = Depends(get_db)):
    doc = DocumentoNormativo(
        nombre=payload.nombre,
        jurisdiccion=payload.jurisdiccion,
        version=payload.version,
        fuente_url=payload.fuente_url,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/documentos", response_model=list[DocumentoOut])
def listar_documentos(db: Session = Depends(get_db)):
    return db.query(DocumentoNormativo).order_by(DocumentoNormativo.nombre).all()


@router.get(
    "/proyectos/{proyecto_id}/normas-activas",
    response_model=list[DocumentoOut],
)
def listar_normas_activas(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    """Documentos activos del proyecto.

    Lista vacia = multinorma por defecto (todas activas); la recuperacion del RAG
    no aplica filtro de documentos en ese caso.
    """
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return (
        db.query(DocumentoNormativo)
        .join(
            ProyectoNormaActiva,
            ProyectoNormaActiva.documento_id == DocumentoNormativo.id,
        )
        .filter(ProyectoNormaActiva.proyecto_id == proyecto_id)
        .all()
    )


@router.put(
    "/proyectos/{proyecto_id}/normas-activas",
    response_model=list[DocumentoOut],
)
def configurar_normas_activas(
    proyecto_id: uuid.UUID,
    payload: NormasActivasUpdate,
    db: Session = Depends(get_db),
):
    """Reemplaza el conjunto de normas activas del proyecto."""
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Borra la configuracion anterior y guarda la nueva.
    db.query(ProyectoNormaActiva).filter(
        ProyectoNormaActiva.proyecto_id == proyecto_id
    ).delete()

    for documento_id in payload.documento_ids:
        if db.get(DocumentoNormativo, documento_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"Documento {documento_id} no encontrado",
            )
        db.add(
            ProyectoNormaActiva(proyecto_id=proyecto_id, documento_id=documento_id)
        )

    db.commit()
    return listar_normas_activas(proyecto_id, db)
