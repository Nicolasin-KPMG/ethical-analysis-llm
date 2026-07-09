"""Pre-fase de analisis (cribado): clasificacion ligera de todos los requisitos.

Antes del analisis detallado (Fases 2-3, caro: 2 pasadas de LLM + RAG por
requisito), esta pre-fase pasa TODOS los requisitos vigentes por UNA sola llamada
al LLM (por lote) que marca cuales podrian tener implicancias eticas y merecen
entrar al analisis. Los que no, quedan descartados (no se analizan).

Es deliberadamente barata: sin RAG, sin las tres capas, una sola llamada.
"""

import logging

from pydantic import BaseModel, Field

from models import Requisito
from providers.llm import get_llm_provider

logger = logging.getLogger(__name__)


# --- Esquema de salida del LLM (por lote) ---
class _CribadoItem(BaseModel):
    indice: int = Field(description="Indice del requisito, tal como se te entrego en la lista.")
    riesgo_potencial: bool = Field(
        description=(
            "True si el requisito PODRIA tensionar algun valor etico (privacidad, "
            "no discriminacion, transparencia, autonomia, seguridad, proporcionalidad, "
            "etc.) y merece analisis detallado. False si es claramente inocuo/tecnico."
        )
    )
    motivo: str = Field(default="", description="Una frase breve que justifique la decision.")


class _CribadoLLM(BaseModel):
    items: list[_CribadoItem] = []


_SISTEMA = (
    "Eres un analista de etica de requisitos de software con IA. Estas haciendo un "
    "CRIBADO PRELIMINAR: decidir rapidamente que requisitos podrian tener "
    "implicancias eticas y merecen un analisis detallado, y cuales son claramente "
    "inocuos. Ante la duda razonable, marca riesgo_potencial=true; reserva false "
    "para requisitos puramente tecnicos/operativos sin afectacion a personas."
)


def _linea_requisito(indice: int, req: Requisito) -> str:
    return (
        f"[{indice}] {req.codigo or 's/codigo'} — {req.nombre}\n"
        f"     Descripcion: {req.descripcion or '-'}\n"
        f"     Tipo: {req.tipo or '-'} | Stakeholder: {req.stakeholder or '-'}"
    )


def _prompt(requisitos: list[Requisito]) -> str:
    listado = "\n".join(_linea_requisito(i, r) for i, r in enumerate(requisitos))
    return (
        f"{_SISTEMA}\n\n"
        "Clasifica CADA requisito de la lista. Devuelve un item por requisito con su "
        "indice, riesgo_potencial (bool) y un motivo breve.\n\n"
        f"REQUISITOS:\n{listado}"
    )


def cribar_proyecto(db, proyecto_id, llm_provider=None) -> list[Requisito]:
    """Ejecuta el cribado sobre los requisitos vigentes del proyecto y persiste
    el resultado (riesgo_preliminar + motivo_preliminar) en cada uno.

    Devuelve la lista de requisitos vigentes ya actualizados.
    """
    llm = llm_provider or get_llm_provider()

    requisitos = (
        db.query(Requisito)
        .filter(
            Requisito.proyecto_id == proyecto_id,
            Requisito.es_vigente.isnot(False),
            Requisito.estado != "eliminado",
        )
        .order_by(Requisito.codigo)
        .all()
    )
    if not requisitos:
        return []

    salida = _CribadoLLM(**llm.analyze(_prompt(requisitos), _CribadoLLM.model_json_schema()))

    # Punto de partida: todo cribado como "sin riesgo"; luego aplicamos lo que el
    # LLM marco como riesgoso. Asi cada requisito queda con un resultado definido.
    por_indice = {it.indice: it for it in salida.items if 0 <= it.indice < len(requisitos)}
    for i, req in enumerate(requisitos):
        it = por_indice.get(i)
        if it is None:
            # El LLM no lo devolvio: lo dejamos como sin riesgo, sin motivo.
            req.riesgo_preliminar = False
            req.motivo_preliminar = None
        else:
            req.riesgo_preliminar = bool(it.riesgo_potencial)
            req.motivo_preliminar = (it.motivo or "").strip() or None

    db.commit()
    for req in requisitos:
        db.refresh(req)
    return requisitos
