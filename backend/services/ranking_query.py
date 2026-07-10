"""Helper que reune los datos de un proyecto desde la base y delega en la
funcion pura de ranking. Lo usan la Fase 6 (ranking) y la Fase 8 (visualizacion),
para no duplicar la logica de recoleccion.
"""

from models import Dimension, EvaluacionDimension, Requisito
from services.ranking import calcular_ranking
from services.requisitos_query import requisitos_rankeables


def _derivados_por_padre(db, proyecto_id):
    """Mapa padre_id (str) -> lista de sus derivados de mitigacion vigentes.

    Los derivados no se puntuan; se muestran como un bloque colgado de su padre.
    """
    derivados = (
        db.query(Requisito)
        .filter(
            Requisito.proyecto_id == proyecto_id,
            Requisito.origen_requisito_id.isnot(None),
            Requisito.es_vigente.is_(True),
            Requisito.estado != "eliminado",
        )
        .order_by(Requisito.codigo, Requisito.nombre)
        .all()
    )
    por_padre: dict[str, list[dict]] = {}
    for d in derivados:
        por_padre.setdefault(str(d.origen_requisito_id), []).append(
            {"requisito_id": str(d.id), "codigo": d.codigo, "nombre": d.nombre}
        )
    return por_padre


def ranking_de_proyecto(db, proyecto_id):
    """Devuelve la lista de items del ranking (ya ordenada) para un proyecto.

    Cada item incluye ademas ``derivados``: los controles de mitigacion colgados
    de ese requisito, que no puntuan pero se listan como bloque bajo su padre.
    """
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
    items = calcular_ranking(requisitos, dimensiones, evaluaciones)

    # Cuelga cada bloque de derivados bajo su padre, en la posicion del padre.
    por_padre = _derivados_por_padre(db, proyecto_id)
    for it in items:
        it["derivados"] = por_padre.get(it["requisito_id"], [])
    return items
