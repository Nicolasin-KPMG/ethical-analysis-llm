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
    "Eres un analista de etica de requisitos de software con IA. Haces un CRIBADO "
    "PRELIMINAR: marcar que requisitos merecen un analisis etico detallado y cuales "
    "son mecanica operativa sin tension etica.\n\n"
    "Marca riesgo_potencial=TRUE solo si el requisito plausiblemente tensiona los "
    "DERECHOS O VALORES de una persona, por ejemplo:\n"
    "- privacidad o uso de datos personales mas alla de lo necesario para su fin;\n"
    "- vigilancia o monitoreo de individuos;\n"
    "- perfilado, puntuacion o clasificacion de personas;\n"
    "- discriminacion o trato desigual (incluidas variables proxy);\n"
    "- decisiones automatizadas que afectan a una persona sin supervision humana;\n"
    "- opacidad: no explicar a la persona una decision que le afecta;\n"
    "- uso secundario o cesion de datos personales a terceros.\n\n"
    "Marca riesgo_potencial=FALSE para mecanismos rutinarios de seguridad, control de "
    "accesos u operacion que, aunque involucren a empleados, NO tensionan esos valores: "
    "inventarios/catalogos de accesos, flujos de solicitud y aprobacion, registros de "
    "auditoria (logs), tableros con metricas agregadas, recordatorios/notificaciones, "
    "plantillas de rol (RBAC), deteccion de conflictos de segregacion de funciones "
    "(combinaciones de accesos incompatibles), accesos temporales con caducidad, "
    "sincronizacion de altas/bajas, o exportacion de evidencia para auditores. Detectar "
    "una violacion de politica o una combinacion de accesos prohibida es un CONTROL, no "
    "un perfilado de personas. Que un requisito trate datos de empleados no lo hace, por "
    "si solo, un riesgo etico.\n\n"
    "Se preciso: distingue los pocos requisitos con tension etica real de la mayoria "
    "operativa. No marques TRUE por las dudas."
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
