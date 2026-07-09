"""Carga datos de prueba (seed) para probar las Fases 1, 4, 5 y 6.

Crea un proyecto realista (asistente de IA de contratacion), 6 dimensiones que
cubren los 4 tipos, 10 requisitos y la matriz completa de evaluaciones. Al final
muestra el ranking calculado por el backend y lo re-calcula localmente para
confirmar que coinciden.

Uso (con docker compose levantado):
    API_URL=http://localhost:8001 python3 backend/seed_demo.py

Usa solo la libreria estandar (urllib) para no requerir dependencias extra.
"""

import json
import os
import urllib.error
import urllib.request

API = os.environ.get("API_URL", "http://localhost:8001")

# La API ahora exige login. El seed crea (o reutiliza) un usuario demo y guarda
# su token aqui para adjuntarlo en cada peticion.
DEMO_USER = {
    "nombre": "Demo Seed",
    # Dominio real: email-validator rechaza TLD reservados como .local/.test.
    "email": os.environ.get("SEED_EMAIL", "demo@example.com"),
    "password": os.environ.get("SEED_PASSWORD", "demo1234"),
}
_TOKEN = None


def _headers():
    h = {"Content-Type": "application/json"}
    if _TOKEN:
        h["Authorization"] = f"Bearer {_TOKEN}"
    return h


def _post(path, payload):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload).encode(),
        headers=_headers(),
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def _put(path, payload):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload).encode(),
        headers=_headers(),
        method="PUT",
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def _get(path):
    req = urllib.request.Request(f"{API}{path}", headers=_headers())
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def _autenticar():
    """Registra el usuario demo (o inicia sesion si ya existe) y guarda el token."""
    global _TOKEN
    try:
        data = _post("/auth/register", DEMO_USER)
    except urllib.error.HTTPError as exc:
        if exc.code != 409:  # 409 = ya existe: se hace login normal
            raise
        data = _post(
            "/auth/login",
            {"email": DEMO_USER["email"], "password": DEMO_USER["password"]},
        )
    _TOKEN = data["access_token"]
    print(f"Autenticado como {DEMO_USER['email']}.")


# --- Definicion de los datos de prueba ---

PROYECTO = {
    "nombre": "Proyecto de prueba — Asistente IA de contratación",
    "descripcion": "Datos dummy para probar registro, dimensiones, evaluación y ranking.",
}

# 6 dimensiones que cubren los 4 tipos (2 suman fuerte, 1 valor etico, etc.).
DIMENSIONES = [
    {"nombre": "Valor para el usuario", "tipo": "beneficio", "peso": 5},
    {"nombre": "Viabilidad técnica", "tipo": "beneficio", "peso": 3},
    {"nombre": "Equidad y no discriminación", "tipo": "valor_etico", "peso": 5},
    {"nombre": "Transparencia y explicabilidad", "tipo": "valor_etico", "peso": 4},
    {"nombre": "Costo de desarrollo", "tipo": "costo", "peso": 3},
    {"nombre": "Riesgo de privacidad", "tipo": "riesgo_etico", "peso": 4},
]

# 10 requisitos realistas para el dominio (codigo, nombre, tipo, descripcion).
# Unos estan redactados para tensionar la etica (001, 002, 003, 007) y otros son
# mas benignos (004, 005, 009) o incluso protectores (010).
REQUISITOS = [
    ("REQ-001", "Filtrado automático de CVs", "funcional",
     "El sistema descarta automáticamente los CV que no alcanzan un puntaje mínimo "
     "calculado por IA, sin que un reclutador revise esos descartes."),
    ("REQ-002", "Ranking de candidatos por afinidad", "funcional",
     "Ordena a los postulantes según una puntuación de afinidad al cargo estimada a "
     "partir de su CV y su historial laboral."),
    ("REQ-003", "Análisis de video-entrevistas", "funcional",
     "Analiza las expresiones faciales, el tono de voz y el lenguaje corporal en "
     "video-entrevistas para asignar un puntaje de idoneidad al candidato."),
    ("REQ-004", "Chatbot de atención a postulantes", "funcional",
     "Chatbot que responde dudas frecuentes de los postulantes sobre el estado y los "
     "requisitos de su postulación."),
    ("REQ-005", "Detección de postulaciones duplicadas", "funcional",
     "Detecta y agrupa postulaciones duplicadas de una misma persona para evitar "
     "registros repetidos en el proceso."),
    ("REQ-006", "Sugerencia de banda salarial", "funcional",
     "Sugiere una banda salarial para cada candidato a partir de sus expectativas, su "
     "experiencia y datos de mercado."),
    ("REQ-007", "Verificación de antecedentes", "restriccion",
     "Cruza los datos del postulante con registros externos para verificar "
     "antecedentes penales, comerciales y laborales."),
    ("REQ-008", "Panel de métricas de diversidad", "no_funcional",
     "Muestra a RR.HH. métricas agregadas de diversidad (género, edad, procedencia) "
     "de los postulantes y de las personas contratadas."),
    ("REQ-009", "Exportación de reportes a RR.HH.", "no_funcional",
     "Exporta reportes del proceso de selección en PDF y Excel para el equipo de "
     "Recursos Humanos."),
    ("REQ-010", "Anonimización de datos sensibles", "restriccion",
     "Anonimiza nombre, RUT y datos de contacto durante las etapas de evaluación para "
     "reducir sesgos y proteger la privacidad."),
]


# Matriz de fuerzas (0-5) hecha a mano: una fila por requisito (mismo orden que
# REQUISITOS) y una columna por dimension (mismo orden que DIMENSIONES):
#   col 0: Valor para el usuario   (beneficio)
#   col 1: Viabilidad técnica      (beneficio)
#   col 2: Equidad/no discrimin.   (valor_etico)
#   col 3: Transparencia/explic.   (valor_etico)
#   col 4: Costo de desarrollo     (costo)
#   col 5: Riesgo de privacidad    (riesgo_etico)
# Cada fila es un perfil plausible; hay algunos 0 ("no aplica") a proposito.
MATRIZ = [
    [5, 4, 2, 2, 4, 5],  # REQ-001 Filtrado de CVs: útil pero éticamente riesgoso
    [5, 3, 1, 2, 3, 5],  # REQ-002 Ranking de candidatos: alto valor, riesgo de sesgo
    [3, 2, 1, 1, 4, 5],  # REQ-003 Video-entrevistas: caro y riesgoso, bajo valor ético
    [4, 5, 4, 4, 2, 1],  # REQ-004 Chatbot: equilibrado y barato
    [4, 5, 3, 3, 1, 1],  # REQ-005 Deduplicación: mucho beneficio, poco costo/riesgo
    [4, 3, 2, 3, 2, 3],  # REQ-006 Banda salarial: intermedio
    [3, 3, 2, 2, 3, 5],  # REQ-007 Verificación de antecedentes: riesgo alto
    [3, 4, 5, 5, 2, 1],  # REQ-008 Métricas de diversidad: alto valor ético
    [2, 5, 3, 4, 1, 2],  # REQ-009 Exportación de reportes: barato, valor moderado
    [2, 3, 5, 4, 3, 0],  # REQ-010 Anonimización: refuerza ética, baja el riesgo (0)
]


def fuerza_para(i, j):
    """Fuerza 0-5 del requisito i en la dimension j (desde la matriz de prueba)."""
    return MATRIZ[i][j]


def main():
    print(f"Conectando a {API} ...")
    _autenticar()
    proyecto = _post("/proyectos", PROYECTO)
    pid = proyecto["id"]
    print(f"Proyecto creado: {pid}")

    # Dimensiones.
    dims = []
    for d in DIMENSIONES:
        creada = _post(f"/proyectos/{pid}/dimensiones", d)
        dims.append(creada)
    print(f"{len(dims)} dimensiones creadas.")

    # Requisitos.
    reqs = []
    for codigo, nombre, tipo, descripcion in REQUISITOS:
        creado = _post(
            f"/proyectos/{pid}/requisitos",
            {
                "codigo": codigo,
                "nombre": nombre,
                "tipo": tipo,
                "descripcion": descripcion,
                "stakeholder": "RR.HH.",
            },
        )
        reqs.append(creado)
    print(f"{len(reqs)} requisitos creados.")

    # Matriz de evaluaciones (requisito x dimension).
    n = 0
    for i, r in enumerate(reqs):
        for j, d in enumerate(dims):
            _put(
                f"/proyectos/{pid}/evaluaciones",
                {
                    "requisito_id": r["id"],
                    "dimension_id": d["id"],
                    "fuerza": fuerza_para(i, j),
                    "justificacion": "Evaluación de prueba (seed).",
                },
            )
            n += 1
    print(f"{n} evaluaciones cargadas.")

    # Snapshot de ejemplo.
    _post(f"/proyectos/{pid}/ranking/snapshot", {})
    print("Snapshot del ranking guardado.")

    # --- Mostrar ranking del backend y verificarlo localmente ---
    ranking = _get(f"/proyectos/{pid}/ranking")["items"]

    print("\n=== RANKING (calculado por el backend) ===")
    print(f"{'#':>2}  {'Código':8} {'Puntaje':>7}  {'(ben)':>5} {'(val)':>5} {'(cos)':>5} {'(rie)':>5}  Nombre")
    for k, it in enumerate(ranking, 1):
        dg = it["desglose"]
        print(
            f"{k:>2}  {it['codigo']:8} {it['puntaje_final']:>7}  "
            f"{dg['beneficio']:>5} {dg['valor_etico']:>5} {dg['costo']:>5} {dg['riesgo_etico']:>5}  "
            f"{it['nombre']}"
        )

    # Re-calculo local independiente para confirmar la formula.
    peso_de = {d["id"]: (d["tipo"], d["peso"]) for d in dims}
    ok = True
    for i, r in enumerate(reqs):
        acc = {"beneficio": 0, "valor_etico": 0, "costo": 0, "riesgo_etico": 0}
        for j, d in enumerate(dims):
            tipo, peso = peso_de[d["id"]]
            acc[tipo] += peso * fuerza_para(i, j)
        esperado = acc["beneficio"] + acc["valor_etico"] - acc["costo"] - acc["riesgo_etico"]
        real = next(x for x in ranking if x["requisito_id"] == r["id"])["puntaje_final"]
        if esperado != real:
            ok = False
            print(f"  ¡DISCREPANCIA en {r['codigo']}: esperado {esperado}, backend {real}!")
    print("\nVerificación local de la fórmula:", "OK ✅" if ok else "FALLÓ ❌")
    print(f"\nAbre la interfaz en http://localhost:3001 y elige el proyecto:\n  '{PROYECTO['nombre']}'")


if __name__ == "__main__":
    main()
