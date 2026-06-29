"""Endpoints de visualizacion del ranking (Fase 8).

- GET /proyectos/{id}/visualizacion: ranking ordenado y auditable, con desglose
  por categoria y una bandera etica por requisito.
- GET /proyectos/{id}/visualizacion/export.csv: exportacion del mismo contenido
  como CSV (abrible en Excel/Sheets), util para el experimento de la tesis.

Nota sobre la bandera: en el metodo final es verde/amarilla/roja segun el
analisis etico (Fases 2-3). Como ese analisis todavia no existe, en M3 todas las
banderas valen "sin_analisis" (placeholder gris). Se reemplazara en M5.
"""

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Proyecto, Requisito
from schemas import VisualizacionOut
from services.ranking_query import ranking_de_proyecto
from services.bandera import bandera_de

router = APIRouter(prefix="/proyectos/{proyecto_id}/visualizacion", tags=["visualizacion"])


def _items_visualizacion(proyecto_id: uuid.UUID, db: Session):
    """Toma el ranking y lo enriquece con posicion y la bandera etica real."""
    ranking = ranking_de_proyecto(db, proyecto_id)
    items = []
    for posicion, it in enumerate(ranking, start=1):
        requisito = db.get(Requisito, uuid.UUID(it["requisito_id"]))
        items.append(
            {
                "posicion": posicion,
                "requisito_id": it["requisito_id"],
                "codigo": it["codigo"],
                "nombre": it["nombre"],
                "puntaje_final": it["puntaje_final"],
                "desglose": it["desglose"],
                "bandera": bandera_de(db, requisito) if requisito else "sin_analisis",
            }
        )
    return items


@router.get("", response_model=VisualizacionOut)
def obtener_visualizacion(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"proyecto_id": proyecto_id, "items": _items_visualizacion(proyecto_id, db)}


@router.get("/export.csv")
def exportar_csv(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    items = _items_visualizacion(proyecto_id, db)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "posicion",
            "codigo",
            "nombre",
            "beneficio",
            "valor_etico",
            "costo",
            "riesgo_etico_residual",
            "puntaje_final",
            "bandera_etica",
        ]
    )
    for it in items:
        d = it["desglose"]
        writer.writerow(
            [
                it["posicion"],
                it["codigo"] or "",
                it["nombre"],
                d["beneficio"],
                d["valor_etico"],
                d["costo"],
                d["riesgo_etico_residual"],
                it["puntaje_final"],
                it["bandera"],
            ]
        )
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=ranking_{proyecto_id}.csv"
        },
    )
