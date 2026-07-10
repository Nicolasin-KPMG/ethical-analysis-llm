"""Seed del caso "Asegurox" para la actividad de experimentación.

Crea DOS proyectos con los mismos 15 requisitos:

  - "real"     -> solo los 15 requisitos cargados (los participantes lo trabajan).
  - "testing"  -> resuelto: dimensiones, evaluaciones, cribado, análisis de los 4
                  requisitos con riesgo ético y una decisión de tratamiento por
                  cada opción (aceptar / mitigar / reformular / eliminar).

De los 15, exactamente 4 tienen riesgo ético, uno por cada decisión:
  RF-06 Índice de riesgo del empleado        -> ACEPTAR   (riesgo residual bajo, con control humano)
  RF-07 Monitoreo continuo de actividad      -> MITIGAR   (crea controles derivados)
  RF-08 Revocación sin explicación           -> REFORMULAR
  RF-14 Compartir scoring con la aseguradora -> ELIMINAR

Uso (con docker compose levantado):
    API_URL=http://localhost:8001 python3 experimentacion/seed_asegurox.py
    # opcional: solo uno de los dos
    API_URL=http://localhost:8001 python3 experimentacion/seed_asegurox.py --solo testing

Usa solo la librería estándar (urllib) para no requerir dependencias extra.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = os.environ.get("API_URL", "http://localhost:8001")
TIMEOUT = 120  # el análisis (LLM + RAG) puede tardar

DEMO_USER = {
    "nombre": "Demo Asegurox",
    "email": os.environ.get("SEED_EMAIL", "demo@example.com"),
    "password": os.environ.get("SEED_PASSWORD", "demo1234"),
}
_TOKEN = None


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------
def _headers():
    h = {"Content-Type": "application/json"}
    if _TOKEN:
        h["Authorization"] = f"Bearer {_TOKEN}"
    return h


def _req(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, headers=_headers(), method=method)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)


def _post(path, payload):
    return _req("POST", path, payload)


def _put(path, payload):
    return _req("PUT", path, payload)


def _get(path):
    return _req("GET", path)


def _autenticar():
    global _TOKEN
    try:
        data = _post("/auth/register", DEMO_USER)
    except urllib.error.HTTPError as exc:
        if exc.code != 409:
            raise
        data = _post("/auth/login", {"email": DEMO_USER["email"], "password": DEMO_USER["password"]})
    _TOKEN = data["access_token"]
    print(f"Autenticado como {DEMO_USER['email']}.")


# --------------------------------------------------------------------------
# Datos del caso
# --------------------------------------------------------------------------
# (codigo, nombre, tipo, descripcion)
REQUISITOS = [
    ("RF-01", "Catálogo de accesos por usuario", "funcional",
     "Cada jefatura ve en un panel todos los roles y accesos que tiene su equipo, con la fecha de la última certificación."),
    ("RF-02", "Campaña de certificación trimestral", "funcional",
     "Cada trimestre el sistema abre una campaña en la que la jefatura revisa y confirma o revoca los accesos de su equipo."),
    ("RF-03", "Matriz de segregación de funciones", "funcional",
     "Se define un catálogo de funciones incompatibles (por ejemplo, crear un proveedor y aprobar sus pagos) y el sistema detecta y reporta las combinaciones de accesos prohibidas para que la jefatura las corrija."),
    ("RF-04", "Solicitud y aprobación de accesos", "funcional",
     "Un empleado solicita un acceso; su jefatura y el dueño del sistema lo aprueban y queda registrado quién pidió, quién aprobó y cuándo."),
    ("RF-05", "Roles por puesto (plantillas de acceso)", "funcional",
     "Se definen plantillas de acceso estándar por cargo: al asignar un puesto se otorgan los accesos típicos, reduciendo errores de asignación manual."),
    # --- RIESGO ÉTICO: ACEPTAR ---
    ("RF-06", "Índice de riesgo del empleado", "funcional",
     "El sistema calcula un nivel de riesgo por persona combinando cargo, antigüedad, área y cantidad de accesos, SOLO para sugerir a quién auditar primero. La decisión de auditar la toma siempre un responsable humano y no se dispara ninguna acción automática sobre la persona."),
    # --- RIESGO ÉTICO: MITIGAR ---
    ("RF-07", "Monitoreo continuo de actividad", "funcional",
     "Para detectar accesos anómalos, el sistema registra de forma permanente los horarios de conexión, la ubicación y las aplicaciones que usa cada empleado."),
    # --- RIESGO ÉTICO: REFORMULAR ---
    ("RF-08", "Revocación sin explicación", "restriccion",
     "Cuando se le quita un acceso, al empleado se le avisa solo que “fue removido”, sin indicar el motivo ni a quién puede reclamar."),
    ("RF-09", "Accesos temporales con caducidad", "funcional",
     "Los accesos de excepción se otorgan con una fecha de expiración automática y se avisa al solicitante antes de que caduquen."),
    ("RF-10", "Recordatorios de certificación pendiente", "funcional",
     "El sistema notifica a cada jefatura las tareas de certificación por vencer, para que ninguna campaña quede sin cerrar."),
    ("RF-11", "Tablero de cumplimiento", "funcional",
     "Un panel muestra indicadores agregados: porcentaje de accesos certificados, conflictos de segregación abiertos y cuentas sin dueño."),
    ("RF-12", "Registro de auditoría inmutable", "no_funcional",
     "Todos los cambios de acceso (alta, baja, aprobación, revocación) quedan en un registro que no se puede alterar, para trazabilidad ante auditores."),
    ("RF-13", "Integración con el directorio corporativo", "funcional",
     "El alta y la baja de accesos se sincroniza con el directorio corporativo usando solo el estado laboral (activo/inactivo) de la persona."),
    # --- RIESGO ÉTICO: ELIMINAR ---
    ("RF-14", "Compartir el scoring con la aseguradora del grupo", "funcional",
     "Los niveles de riesgo por empleado se comparten con la compañía de seguros del grupo para “afinar” las pólizas de fidelidad y de personas."),
    ("RF-15", "Exportación de evidencia para auditoría externa", "funcional",
     "El sistema genera un paquete de reportes de accesos y certificaciones para entregar a los auditores externos cuando lo soliciten."),
]

# Los 4 con riesgo ético y su decisión objetivo.
RIESGOSOS = {"RF-06", "RF-07", "RF-08", "RF-14"}

# Dimensiones base (aplican a todos). El riesgo ético lo aportan las dimensiones
# que genera el análisis por cada requisito riesgoso.
DIMENSIONES = [
    ("Valor para el negocio", "beneficio", 5,
     "Cuánto aporta a ordenar la gestión de accesos y cerrar los hallazgos de auditoría."),
    ("Urgencia por la auditoría", "beneficio", 4,
     "Qué tan prioritario es por las observaciones de la última auditoría."),
    ("Aporte a control y transparencia", "valor_etico", 4,
     "Cuánto mejora el control interno, la trazabilidad y la rendición de cuentas."),
    ("Costo de implementación", "costo", 3,
     "Esfuerzo técnico y organizacional para construirlo."),
]

# Fuerza (0-5) de cada requisito en las 4 dimensiones base, en el mismo orden que
# DIMENSIONES: (valor_negocio, urgencia, control_transparencia, costo).
FUERZAS_BASE = {
    "RF-01": (4, 4, 4, 2),
    "RF-02": (5, 5, 5, 3),
    "RF-03": (5, 5, 5, 4),
    "RF-04": (4, 4, 4, 3),
    "RF-05": (3, 2, 3, 2),
    "RF-06": (3, 3, 2, 3),
    "RF-07": (3, 3, 2, 4),
    "RF-08": (1, 1, 1, 1),
    "RF-09": (3, 2, 3, 2),
    "RF-10": (2, 3, 2, 1),
    "RF-11": (3, 3, 4, 2),
    "RF-12": (4, 4, 5, 3),
    "RF-13": (3, 3, 2, 3),
    "RF-14": (2, 2, 1, 2),
    "RF-15": (3, 4, 3, 2),
}

# Fuerza para la(s) dimensión(es) ética(s) de riesgo que el análisis crea por cada
# requisito riesgoso. RF-06 (aceptar) lleva un riesgo residual bajo.
FUERZA_RIESGO = {"RF-06": 2, "RF-07": 4, "RF-08": 4, "RF-14": 5}


# --------------------------------------------------------------------------
# Construcción de un proyecto
# --------------------------------------------------------------------------
def crear_requisitos(pid):
    """Crea los 15 requisitos y devuelve {codigo: id}."""
    ids = {}
    for codigo, nombre, tipo, descripcion in REQUISITOS:
        creado = _post(
            f"/proyectos/{pid}/requisitos",
            {"codigo": codigo, "nombre": nombre, "tipo": tipo,
             "descripcion": descripcion, "stakeholder": "Seguridad de la información"},
        )
        ids[codigo] = creado["id"]
    print(f"  {len(ids)} requisitos creados.")
    return ids


def crear_proyecto_real():
    proyecto = _post("/proyectos", {
        "nombre": "Asegurox — Certificación de accesos",
        "descripcion": "Plataforma con IA para certificar accesos y controlar la segregación de funciones (caso de la sesión).",
    })
    pid = proyecto["id"]
    print(f"[REAL] Proyecto creado: {pid}")
    crear_requisitos(pid)
    print("[REAL] Listo (solo requisitos cargados, sin analizar).")
    return pid


def crear_proyecto_testing():
    proyecto = _post("/proyectos", {
        "nombre": "Asegurox — Certificación de accesos (DEMO resuelta)",
        "descripcion": "Copia resuelta para demostración: análisis ético y una decisión de tratamiento por cada opción.",
    })
    pid = proyecto["id"]
    print(f"[TEST] Proyecto creado: {pid}")
    req_ids = crear_requisitos(pid)

    # Dimensiones base.
    dim_ids = []
    for nombre, tipo, peso, desc in DIMENSIONES:
        d = _post(f"/proyectos/{pid}/dimensiones",
                  {"nombre": nombre, "tipo": tipo, "peso": peso, "descripcion": desc})
        dim_ids.append(d["id"])
    print(f"[TEST] {len(dim_ids)} dimensiones base creadas.")

    # Evaluaciones base (matriz requisito × dimensión base).
    n = 0
    for codigo, rid in req_ids.items():
        for dim_id, fuerza in zip(dim_ids, FUERZAS_BASE[codigo]):
            _put(f"/proyectos/{pid}/evaluaciones",
                 {"requisito_id": rid, "dimension_id": dim_id, "fuerza": fuerza,
                  "justificacion": "Evaluación base (seed)."})
            n += 1
    print(f"[TEST] {n} evaluaciones base cargadas.")

    # Cribado (marca los que podrían tener riesgo ético).
    _post(f"/proyectos/{pid}/cribado", {})
    verificar_cribado(pid, req_ids)

    # Análisis detallado de los 4 riesgosos.
    print("[TEST] Analizando los 4 requisitos con riesgo ético (LLM + RAG)...")
    for codigo in ["RF-06", "RF-07", "RF-08", "RF-14"]:
        _post(f"/requisitos/{req_ids[codigo]}/analizar", {})
        print(f"        {codigo} analizado.")

    # Evaluar las dimensiones éticas (de riesgo) que creó el análisis.
    evaluar_dimensiones_eticas(pid, req_ids)

    # Aplicar una decisión de tratamiento por cada opción.
    aplicar_decisiones(pid, req_ids, dim_ids)

    # Snapshot del ranking final.
    _post(f"/proyectos/{pid}/ranking/snapshot", {})
    mostrar_ranking(pid)
    print("[TEST] Listo (resuelto).")
    return pid


def verificar_cribado(pid, req_ids):
    """Comprueba que el cribado marcó exactamente los 4 riesgosos esperados."""
    reqs = _get(f"/proyectos/{pid}/requisitos")
    marcados = {r["codigo"] for r in reqs if r.get("riesgo_preliminar")}
    esperado = RIESGOSOS
    ok = marcados == esperado
    print(f"[TEST] Cribado -> con riesgo: {sorted(marcados)}")
    if not ok:
        faltan = esperado - marcados
        sobran = marcados - esperado
        print(f"        ⚠️  NO coincide con lo esperado {sorted(esperado)}.")
        if faltan:
            print(f"        ⚠️  No se marcaron (falsos negativos): {sorted(faltan)}")
        if sobran:
            print(f"        ⚠️  Se marcaron de más (falsos positivos): {sorted(sobran)}")
    else:
        print("        ✅ Coincide exactamente con los 4 esperados.")
    return ok


def evaluar_dimensiones_eticas(pid, req_ids):
    """Pone fuerza a las dimensiones éticas de riesgo que creó el análisis."""
    id_a_codigo = {v: k for k, v in req_ids.items()}
    dims = _get(f"/proyectos/{pid}/dimensiones")
    n = 0
    for d in dims:
        if d["tipo"] != "riesgo_etico":
            continue
        for rid in d.get("requisitos_aplica", []):
            codigo = id_a_codigo.get(rid)
            if codigo in FUERZA_RIESGO:
                _put(f"/proyectos/{pid}/evaluaciones",
                     {"requisito_id": rid, "dimension_id": d["id"],
                      "fuerza": FUERZA_RIESGO[codigo],
                      "justificacion": "Intensidad del riesgo ético (seed)."})
                n += 1
    print(f"[TEST] {n} evaluaciones de riesgo ético cargadas.")


def aplicar_decisiones(pid, req_ids, dim_ids):
    """Una decisión de tratamiento por cada opción."""
    # ACEPTAR — RF-06 (riesgo residual bajo, con control humano).
    _post(f"/requisitos/{req_ids['RF-06']}/tratamiento", {
        "decision": "aceptar",
        "justificacion": "El índice solo prioriza a quién auditar; la decisión final es humana y no hay acción automática sobre la persona. El riesgo residual es bajo y se acepta con supervisión.",
        "responsable": "Comité de seguridad",
    })

    # MITIGAR — RF-07 (crea controles derivados).
    _post(f"/requisitos/{req_ids['RF-07']}/tratamiento", {
        "decision": "mitigar",
        "justificacion": "El objetivo de detectar accesos anómalos es legítimo, pero el monitoreo es intrusivo. Se conserva con salvaguardas.",
        "responsable": "Oficial de privacidad",
        "derivados": [
            {"nombre": "Minimizar los datos monitoreados",
             "descripcion": "Registrar solo eventos de acceso a sistemas críticos; NO ubicación ni aplicaciones de uso personal.",
             "obligatorio": True},
            {"nombre": "Limitar propósito y retención",
             "descripcion": "Usar los registros solo para seguridad, con retención acotada y borrado automático al vencer el plazo.",
             "obligatorio": True},
            {"nombre": "Aviso y transparencia al empleado",
             "descripcion": "Informar qué se monitorea y por qué, mediante una política de monitoreo comunicada.",
             "obligatorio": False},
        ],
    })

    # REFORMULAR — RF-08.
    nuevo = _post(f"/requisitos/{req_ids['RF-08']}/tratamiento", {
        "decision": "reformular",
        "justificacion": "La revocación sin motivo vulnera la transparencia y el debido proceso. Se reformula para explicar el motivo y ofrecer un canal de reclamo.",
        "responsable": "Dueño del sistema",
        "nuevo_nombre": "Revocación con motivo y canal de reclamo",
        "nueva_descripcion": "Al revocar un acceso se informa el motivo, la fecha y a quién puede reclamar el empleado; la revisión de reclamos la hace una persona responsable.",
    })
    # La nueva versión nace sin evaluar: le damos evaluaciones base (ya sin riesgo).
    nuevo_id = nuevo.get("nuevo_requisito_id")
    if nuevo_id:
        for dim_id, fuerza in zip(dim_ids, (3, 3, 5, 2)):
            _put(f"/proyectos/{pid}/evaluaciones",
                 {"requisito_id": nuevo_id, "dimension_id": dim_id, "fuerza": fuerza,
                  "justificacion": "Versión reformulada (seed)."})

    # ELIMINAR — RF-14.
    _post(f"/requisitos/{req_ids['RF-14']}/tratamiento", {
        "decision": "eliminar",
        "justificacion": "Compartir el scoring con la aseguradora es un uso secundario sin base legal y con riesgo de discriminación en las pólizas. Se elimina.",
        "responsable": "Comité de ética",
    })
    print("[TEST] Decisiones aplicadas: aceptar RF-06, mitigar RF-07, reformular RF-08, eliminar RF-14.")


def mostrar_ranking(pid):
    ranking = _get(f"/proyectos/{pid}/ranking")["items"]
    print("\n=== RANKING (proyecto testing) ===")
    print(f"{'#':>2}  {'Código':7} {'Puntaje':>7}  Nombre")
    for k, it in enumerate(ranking, 1):
        print(f"{k:>2}  {it['codigo'] or '—':7} {it['puntaje_final']:>7}  {it['nombre']}")
        for d in it.get("derivados", []):
            print(f"      ↳ (hijo) {d['nombre']}")
    print()


# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Seed del caso Asegurox.")
    parser.add_argument("--solo", choices=["real", "testing"], help="Crear solo uno de los dos proyectos.")
    args = parser.parse_args()

    print(f"Conectando a {API} ...")
    _autenticar()

    if args.solo != "testing":
        crear_proyecto_real()
    if args.solo != "real":
        crear_proyecto_testing()


if __name__ == "__main__":
    main()
