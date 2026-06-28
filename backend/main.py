"""Punto de entrada de FastAPI.

Monta los routers disponibles y expone un healthcheck. Las tablas se crean con
migraciones de Alembic (no con create_all), para que el esquema sea versionado
y explicable, como pide la tesis.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from config import settings
from routers import (
    proyectos,
    requisitos,
    dimensiones,
    evaluaciones,
    ranking,
    visualizacion,
    documentos,
    fases23,
    relaciones,
    export,
)

app = FastAPI(
    title="Gestion etica y priorizacion de requisitos",
    description="Backend del metodo de 8 fases (tesis). M0+M1: setup y Fase 1.",
    version="0.1.0",
)

# CORS abierto en local para que el frontend (localhost:3000) hable con el backend.
# No es endurecimiento de produccion (fuera de alcance, ver seccion 12).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    """Healthcheck: responde ok y verifica la conexion a la base de datos."""
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "ok",
        "database": "ok" if db_ok else "error",
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }


# Routers de la Fase 1.
app.include_router(proyectos.router)
app.include_router(requisitos.router)

# Routers de M2 (Fases 4, 5 y 6).
app.include_router(dimensiones.router)
app.include_router(evaluaciones.router)
app.include_router(ranking.router)

# Router de M3 (Fase 8, visualizacion).
app.include_router(visualizacion.router)

# Router de M4 (documentos normativos y normas activas, para el RAG).
app.include_router(documentos.router)

# Router de M5 (Fases 2-3: analisis etico y tratamiento).
app.include_router(fases23.router)

# Routers de M6 (Fase 7: relaciones/trazabilidad; y exportacion del proyecto).
app.include_router(relaciones.router)
app.include_router(export.router)
