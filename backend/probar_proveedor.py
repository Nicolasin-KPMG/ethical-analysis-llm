"""Smoke-test de los proveedores de LLM y embeddings configurados en el .env.

Sirve para validar un proveedor nuevo (p. ej. Gemini por su capa compatible con
OpenAI) ANTES de desplegar, sin levantar la app entera ni tocar la base de datos.

Comprueba tres cosas que son las que suelen romperse al cambiar de proveedor:
  1. Que el LLM responde y respeta `response_format={"type":"json_object"}`.
  2. Que el LLM cumple un JSON Schema anidado como el de las tres capas.
  3. Que los embeddings devuelven vectores de EMBEDDING_DIM dimensiones
     (si el proveedor ignora el parametro `dimensions`, el vector no cabe en la
     columna VECTOR(1024) y la ingesta fallaria a mitad de camino).

Uso:
    docker compose run --rm --no-deps backend python probar_proveedor.py
"""

import json

from config import settings
from providers.embeddings import get_embedding_provider
from providers.llm import get_llm_provider

ESQUEMA_PRUEBA = {
    "type": "object",
    "properties": {
        "tema": {"type": "string"},
        "riesgos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "gravedad": {"type": "string", "enum": ["baja", "media", "alta"]},
                },
                "required": ["nombre", "gravedad"],
            },
        },
    },
    "required": ["tema", "riesgos"],
}

PROMPT = (
    "Analiza este requisito de software: 'El sistema descarta automaticamente "
    "candidatos mayores de 50 anos'. Devuelve el tema etico principal y dos "
    "riesgos con su gravedad."
)


def probar_llm() -> bool:
    print(f"\n[LLM] proveedor={settings.llm_provider} modelo={settings.openai_model}")
    print(f"      base_url={settings.openai_base_url or '(API de OpenAI)'}")
    try:
        salida = get_llm_provider().analyze(PROMPT, ESQUEMA_PRUEBA)
    except Exception as exc:
        print(f"  FALLO: {type(exc).__name__}: {exc}")
        return False

    print(f"  Respuesta: {json.dumps(salida, ensure_ascii=False)[:300]}")
    if not isinstance(salida, dict) or "tema" not in salida or "riesgos" not in salida:
        print("  FALLO: la salida no cumple el esquema (faltan claves).")
        return False
    print("  OK: JSON estructurado valido.")
    return True


def probar_embeddings() -> bool:
    proveedor = get_embedding_provider()
    print(f"\n[EMBEDDINGS] proveedor={settings.embedding_provider} modelo={proveedor.model_name}")
    print(f"             base_url={settings.embedding_openai_base_url or '(por defecto)'}")
    try:
        vectores = proveedor.embed(["texto de prueba en espanol", "test text in english"])
    except Exception as exc:
        print(f"  FALLO: {type(exc).__name__}: {exc}")
        return False

    dims = len(vectores[0])
    print(f"  Vectores: {len(vectores)}, dimensiones: {dims}")
    if dims != settings.embedding_dim:
        print(
            f"  FALLO: se esperaban {settings.embedding_dim} dimensiones (columna "
            f"VECTOR({settings.embedding_dim})). El proveedor ignoro `dimensions`.\n"
            f"         Opciones: usar un modelo que si lo soporte, o migrar la "
            f"columna a VECTOR({dims}) y re-ingerir el corpus."
        )
        return False
    print("  OK: dimensiones correctas.")
    return True


if __name__ == "__main__":
    ok_llm = probar_llm()
    ok_emb = probar_embeddings()
    print("\n" + "=" * 60)
    if ok_llm and ok_emb:
        print(" TODO OK. El proveedor sirve para desplegar.")
        raise SystemExit(0)
    print(" HAY FALLOS. Revisa el .env antes de desplegar.")
    raise SystemExit(1)
