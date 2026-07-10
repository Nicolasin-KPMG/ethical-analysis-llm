"""Helper compartido para seleccionar los requisitos que entran a evaluacion
y ranking, segun las reglas de negocio:

  - Regla 2: solo la version VIGENTE se evalua y entra al ranking (es_vigente=true).
  - Regla 5: "eliminar" no borra, marca estado='eliminado' y lo excluye del ranking.
  - Derivados de mitigacion (origen_requisito_id): NO se evaluan ni compiten sueltos
    en el ranking; entran como un bloque bajo su requisito padre (ver ranking_query).

Centralizar esto evita que las Fases 5 y 6 apliquen el filtro de forma distinta.
"""

from models import Requisito


def requisitos_rankeables(db, proyecto_id):
    """Requisitos de un proyecto que pueden evaluarse y rankearse.

    Excluye los derivados de mitigacion: no se puntuan por dimensiones, se muestran
    agrupados bajo su padre en el ranking.
    """
    return (
        db.query(Requisito)
        .filter(
            Requisito.proyecto_id == proyecto_id,
            Requisito.es_vigente.is_(True),
            Requisito.estado != "eliminado",
            Requisito.origen_requisito_id.is_(None),
        )
        .all()
    )
