"""Seed del ESTADO ALCANZADO EN LA SESIÓN real de experimentación (para screenshots).

A diferencia de seed_asegurox.py (que resuelve las 4 decisiones), este reproduce lo
que efectivamente hizo el grupo:

  - Los 15 requisitos cargados.
  - Las 4 dimensiones exigidas por el área de Seguridad de la Información / Auditoría
    (2 de beneficio y 2 de costo), más las de riesgo ético que crea el análisis.
  - Pre-análisis (cribado) corrido.
  - Análisis detallado de DOS requisitos: RF-06 y RF-07.
  - RF-06 (índice de riesgo del empleado)  -> REFORMULAR (transparencia e impugnación).
  - RF-07 (monitoreo continuo de actividad) -> MITIGAR (controles derivados).
  - Matriz de evaluación completada.

Uso (apuntando al backend desplegado):
    API_URL=http://localhost:8001 python3 experimentacion/seed_sesion.py
    # o contra el droplet, según cómo esté expuesto el backend:
    API_URL=http://159.223.124.246:8001 python3 experimentacion/seed_sesion.py

Reutiliza los helpers y los 15 requisitos de seed_asegurox.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_asegurox as S  # noqa: E402

# Las 4 dimensiones que pide el área de seguridad en la guía Asegurox.
DIMS_SESION = [
    ("Cierre de hallazgos de auditoría", "beneficio", 5,
     "Cuánto ayuda el requisito a cerrar las observaciones de la auditoría."),
    ("Reducción del riesgo de accesos indebidos / fraude", "beneficio", 4,
     "Cuánto baja la exposición a permisos incompatibles y cuentas indebidas."),
    ("Costo de implementación", "costo", 3,
     "Esfuerzo técnico y de tiempo para construirlo."),
    ("Fricción operativa", "costo", 2,
     "Carga que agrega a jefaturas y usuarios (revisiones, aprobaciones)."),
]

# Fuerza de asociación (0-5) por requisito, en el orden de DIMS_SESION:
# (Cierre hallazgos, Reducción riesgo, Costo implementación, Fricción operativa)
FUERZAS = {
    "RF-01": (4, 4, 2, 2), "RF-02": (5, 4, 3, 4), "RF-03": (5, 5, 4, 3),
    "RF-04": (3, 4, 3, 3), "RF-05": (3, 3, 3, 2), "RF-06": (3, 4, 3, 3),
    "RF-07": (2, 3, 3, 4), "RF-08": (2, 3, 1, 2), "RF-09": (3, 4, 2, 2),
    "RF-10": (3, 2, 1, 1), "RF-11": (4, 2, 3, 1), "RF-12": (5, 3, 3, 1),
    "RF-13": (3, 3, 3, 2), "RF-14": (1, 1, 2, 2), "RF-15": (4, 2, 2, 2),
}
DEFAULT_FUERZA = (3, 3, 2, 2)
# Intensidad del riesgo ético que crea el análisis, para los dos analizados.
FUERZA_RIESGO = {"RF-06": 4, "RF-07": 4}


def _evaluar_base_vigentes(pid, dim_ids):
    """PUT idempotente de las 4 dimensiones base para todos los requisitos vigentes
    (cubre los 15 originales, la nueva versión reformulada y los derivados)."""
    n = 0
    for r in S._get(f"/proyectos/{pid}/requisitos"):
        if r.get("es_vigente") is False:
            continue
        if r.get("origen_requisito_id"):
            continue  # los derivados de mitigación no se evalúan (van como bloque bajo su padre)
        fuerzas = FUERZAS.get(r.get("codigo"), DEFAULT_FUERZA)
        for dim_id, fuerza in zip(dim_ids, fuerzas):
            S._put(f"/proyectos/{pid}/evaluaciones",
                   {"requisito_id": r["id"], "dimension_id": dim_id, "fuerza": fuerza,
                    "justificacion": "Evaluación cargada en la sesión."})
            n += 1
    print(f"  {n} evaluaciones base (dimensiones de la sesión) cargadas.")


def _evaluar_riesgo_etico(pid, req_ids):
    id2cod = {v: k for k, v in req_ids.items()}
    n = 0
    for d in S._get(f"/proyectos/{pid}/dimensiones"):
        if d["tipo"] != "riesgo_etico":
            continue
        for rid in d.get("requisitos_aplica", []):
            cod = id2cod.get(rid)
            if cod in FUERZA_RIESGO:
                S._put(f"/proyectos/{pid}/evaluaciones",
                       {"requisito_id": rid, "dimension_id": d["id"],
                        "fuerza": FUERZA_RIESGO[cod],
                        "justificacion": "Intensidad del riesgo ético (sesión)."})
                n += 1
    print(f"  {n} evaluaciones de riesgo ético cargadas.")


def main():
    print(f"Conectando a {S.API} ...")
    S._autenticar()

    proyecto = S._post("/proyectos", {
        "nombre": "Asegurox — Sesión (estado final)",
        "descripcion": ("Reconstrucción del estado alcanzado en la sesión: pre-análisis corrido, "
                        "RF-06 reformulado, RF-07 mitigado, dimensiones del área de seguridad y "
                        "evaluación completada."),
    })
    pid = proyecto["id"]
    print(f"Proyecto de la sesión creado: {pid}")

    req_ids = S.crear_requisitos(pid)

    # Dimensiones del área de seguridad (2 beneficio, 2 costo).
    dim_ids = []
    for nombre, tipo, peso, desc in DIMS_SESION:
        d = S._post(f"/proyectos/{pid}/dimensiones",
                    {"nombre": nombre, "tipo": tipo, "peso": peso, "descripcion": desc})
        dim_ids.append(d["id"])
    print(f"  {len(dim_ids)} dimensiones del área de seguridad creadas.")

    # Evaluación base de los 15 antes del cribado.
    _evaluar_base_vigentes(pid, dim_ids)

    # Pre-análisis (cribado).
    S._post(f"/proyectos/{pid}/cribado", {})
    S.verificar_cribado(pid, req_ids)

    # Análisis detallado SOLO de los dos que trabajó el grupo.
    print("Analizando RF-06 y RF-07 (LLM + RAG)...")
    for cod in ["RF-06", "RF-07"]:
        S._post(f"/requisitos/{req_ids[cod]}/analizar", {})
        print(f"  {cod} analizado.")

    # Intensidad de las dimensiones de riesgo ético creadas por el análisis.
    _evaluar_riesgo_etico(pid, req_ids)

    # RF-06 -> REFORMULAR (índice de riesgo con transparencia e impugnación).
    S._post(f"/requisitos/{req_ids['RF-06']}/tratamiento", {
        "decision": "reformular",
        "justificacion": ("El índice combina datos personales y laborales y puede derivar en perfilado "
                          "y decisiones sesgadas contra ciertos grupos (antigüedad, cargo), aun sin usar "
                          "categorías especiales. Se reformula para dar transparencia y explicabilidad de "
                          "los criterios, identificar al responsable humano y habilitar la impugnación del "
                          "indicador. El análisis se apoya en fragmentos normativos y no en evidencia "
                          "estadística, por lo que se recomienda una evaluación de impacto en privacidad "
                          "(PIA) antes de implementar."),
        "responsable": "Comité de ética y seguridad",
        "nuevo_nombre": "Índice de riesgo del empleado con transparencia e impugnación",
        "nueva_descripcion": ("El sistema calcula un nivel de riesgo por persona solo para sugerir a quién "
                              "auditar primero. Se informan al empleado los criterios y la lógica de "
                              "cálculo, se identifica al responsable humano de la decisión y se habilita un "
                              "canal para impugnar el indicador asignado. La decisión de auditar la toma "
                              "siempre una persona responsable, que registra sus razones. No se dispara "
                              "ninguna acción automática sobre la persona."),
    })
    print("  RF-06 reformulado.")

    # RF-07 -> MITIGAR (controles derivados).
    S._post(f"/requisitos/{req_ids['RF-07']}/tratamiento", {
        "decision": "mitigar",
        "justificacion": ("Detectar accesos anómalos es un objetivo legítimo, pero el monitoreo continuo "
                          "de horarios, ubicación y aplicaciones es intrusivo. Se conserva el requisito con "
                          "salvaguardas que minimizan los datos, limitan el propósito y la retención, e "
                          "informan al empleado."),
        "responsable": "Oficial de privacidad",
        "derivados": [
            {"nombre": "Minimizar los datos monitoreados",
             "descripcion": "Registrar solo eventos de acceso a sistemas críticos; no ubicación ni aplicaciones de uso personal.",
             "obligatorio": True},
            {"nombre": "Limitar propósito y retención",
             "descripcion": "Usar los registros solo para seguridad, con retención acotada y borrado automático al vencer el plazo.",
             "obligatorio": True},
            {"nombre": "Aviso y transparencia al empleado",
             "descripcion": "Informar qué se monitorea y por qué mediante una política de monitoreo comunicada.",
             "obligatorio": False},
        ],
    })
    print("  RF-07 mitigado (3 derivados).")

    # Evaluación final: cubre la nueva versión reformulada y los derivados.
    _evaluar_base_vigentes(pid, dim_ids)

    # Snapshot del ranking y muestra por consola.
    S._post(f"/proyectos/{pid}/ranking/snapshot", {})
    S.mostrar_ranking(pid)
    print(f"\nLISTO. Proyecto de la sesión sembrado (id {pid}). Abre la app y toma las capturas.")
    return pid


if __name__ == "__main__":
    main()
