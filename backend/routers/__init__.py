"""Routers de la API, un grupo por fase.

Fase 1: proyectos, requisitos.
M2: dimensiones (Fase 4), evaluaciones (Fase 5), ranking (Fase 6).
M3: visualizacion (Fase 8).
Los routers de las demas fases se agregan en sus hitos correspondientes.
"""

from routers import (
    proyectos,
    requisitos,
    dimensiones,
    evaluaciones,
    ranking,
    visualizacion,
)

__all__ = [
    "proyectos",
    "requisitos",
    "dimensiones",
    "evaluaciones",
    "ranking",
    "visualizacion",
]
