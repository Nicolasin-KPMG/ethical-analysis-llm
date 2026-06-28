"""Helper que reune los datos de un proyecto desde la base y delega en la
funcion pura de ranking. Lo usan la Fase 6 (ranking) y la Fase 8 (visualizacion),
para no duplicar la logica de recoleccion.
"""

from models import Dimension, EvaluacionDimension
from services.ranking import calcular_ranking
from services.requisitos_query import requisitos_rankeables


def ranking_de_proyecto(db, proyecto_id):
    """Devuelve la lista de items del ranking (ya ordenada) para un proyecto."""
    requisitos = requisitos_rankeables(db, proyecto_id)
    dimensiones = (
        db.query(Dimension).filter(Dimension.proyecto_id == proyecto_id).all()
    )
    ids_rankeables = [r.id for r in requisitos]
    evaluaciones = (
        db.query(EvaluacionDimension)
        .filter(EvaluacionDimension.requisito_id.in_(ids_rankeables))
        .all()
        if ids_rankeables
        else []
    )
    return calcular_ranking(requisitos, dimensiones, evaluaciones)
