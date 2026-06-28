"""Esquemas Pydantic de la visualizacion del ranking (Fase 8)."""

import uuid
from typing import Literal

from pydantic import BaseModel

from schemas.ranking import DesgloseRanking

# Bandera etica por requisito. En el metodo final es verde/amarilla/roja segun el
# analisis etico (Fases 2-3). Como ese analisis aun no existe, en M3 todas las
# banderas son "sin_analisis" (placeholder gris). Se reemplazara en M5.
BanderaEtica = Literal["verde", "amarilla", "roja", "sin_analisis"]


class VisualizacionItem(BaseModel):
    posicion: int
    requisito_id: str
    codigo: str | None = None
    nombre: str
    puntaje_final: int
    desglose: DesgloseRanking
    bandera: BanderaEtica


class VisualizacionOut(BaseModel):
    proyecto_id: uuid.UUID
    items: list[VisualizacionItem]
