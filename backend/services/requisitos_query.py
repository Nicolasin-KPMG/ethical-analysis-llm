"""Helper compartido para seleccionar los requisitos que entran a evaluacion
y ranking, segun las reglas de negocio:

  - Regla 2: solo la version VIGENTE se evalua y entra al ranking (es_vigente=true).
  - Regla 5: "eliminar" no borra, marca estado='eliminado' y lo excluye del ranking.

Centralizar esto evita que las Fases 5 y 6 apliquen el filtro de forma distinta.
"""

from models import Requisito


def requisitos_rankeables(db, proyecto_id):
    """Requisitos de un proyecto que pueden evaluarse y rankearse."""
    return (
        db.query(Requisito)
        .filter(
            Requisito.proyecto_id == proyecto_id,
            Requisito.es_vigente.is_(True),
            Requisito.estado != "eliminado",
        )
        .all()
    )
