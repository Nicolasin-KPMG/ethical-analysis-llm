"""Conexion a PostgreSQL y sesion de SQLAlchemy.

Patron clasico de FastAPI: un engine, un sessionmaker y una dependencia
`get_db` que entrega una sesion por request y la cierra al terminar.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# `future=True` y el dialecto 2.0 ya vienen por defecto en SQLAlchemy 2.x.
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa de la que heredan todos los modelos (en /models).
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesion y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
