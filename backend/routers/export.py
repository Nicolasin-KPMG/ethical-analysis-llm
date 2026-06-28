"""Exportacion del proyecto completo (Fase 8 / M6).

GET /proyectos/{id}/export.json devuelve una foto completa y auditable del
proyecto (requisitos, dimensiones, evaluaciones, relaciones, analisis y ranking)
como archivo JSON descargable. Util para el experimento de la tesis.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Proyecto,
    Requisito,
    Dimension,
    EvaluacionDimension,
    RelacionRequisito,
    AnalisisEtico,
    TemaEticoDetectado,
)
from services.ranking_query import ranking_de_proyecto

router = APIRouter(tags=["export"])


def _fila(obj, campos):
    """Convierte un modelo en dict tomando solo los campos indicados."""
    return {c: getattr(obj, c) for c in campos}


@router.get("/proyectos/{proyecto_id}/export.json")
def exportar_proyecto(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    requisitos = db.query(Requisito).filter(Requisito.proyecto_id == proyecto_id).all()
    req_ids = [r.id for r in requisitos]

    dimensiones = db.query(Dimension).filter(Dimension.proyecto_id == proyecto_id).all()
    evaluaciones = (
        db.query(EvaluacionDimension)
        .filter(EvaluacionDimension.requisito_id.in_(req_ids))
        .all()
        if req_ids
        else []
    )
    relaciones = (
        db.query(RelacionRequisito)
        .filter(RelacionRequisito.origen_id.in_(req_ids))
        .all()
        if req_ids
        else []
    )

    # Ultimo analisis por requisito, con sus temas (Capa 1).
    analisis_export = []
    for rid in req_ids:
        a = (
            db.query(AnalisisEtico)
            .filter(AnalisisEtico.requisito_id == rid)
            .order_by(AnalisisEtico.creado_en.desc())
            .first()
        )
        if a is None:
            continue
        temas = db.query(TemaEticoDetectado).filter(TemaEticoDetectado.analisis_id == a.id).all()
        analisis_export.append(
            {
                **_fila(a, ["id", "requisito_id", "generado_por", "modelo_usado",
                            "nivel_confianza", "limitaciones", "capas_2_3", "creado_en"]),
                "temas": [
                    _fila(t, ["id", "tema_etico", "actor_afectado", "tipo_dano",
                              "norma_tensionada_texto", "evidencia"])
                    for t in temas
                ],
            }
        )

    datos = {
        "proyecto": _fila(proyecto, ["id", "nombre", "descripcion", "fecha_creacion"]),
        "requisitos": [
            _fila(r, ["id", "codigo", "nombre", "descripcion", "tipo", "stakeholder",
                      "estado", "es_vigente", "version_anterior_id", "origen_requisito_id"])
            for r in requisitos
        ],
        "dimensiones": [
            _fila(d, ["id", "nombre", "tipo", "descripcion", "peso", "justificacion_peso"])
            for d in dimensiones
        ],
        "evaluaciones": [
            _fila(e, ["id", "requisito_id", "dimension_id", "fuerza", "justificacion", "responsable"])
            for e in evaluaciones
        ],
        "relaciones": [
            _fila(rel, ["id", "origen_id", "derivado_id", "tipo_relacion", "obligatorio"])
            for rel in relaciones
        ],
        "analisis": analisis_export,
        "ranking": ranking_de_proyecto(db, proyecto_id),
    }

    return JSONResponse(
        content=jsonable_encoder(datos),
        headers={"Content-Disposition": f"attachment; filename=proyecto_{proyecto_id}.json"},
    )
