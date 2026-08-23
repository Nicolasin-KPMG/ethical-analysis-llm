#!/usr/bin/env bash
# ==========================================================================
# Paso 0 del despliegue gratis: valida que Gemini sirve, ANTES de desplegar.
#
# Lee GEMINI_API_KEY del .env y corre backend/probar_proveedor.py apuntando
# el cliente de OpenAI a Gemini. No toca la base de datos ni tu configuracion
# local: las variables se pasan solo a este contenedor de un solo uso.
#
# Uso:  bash deploy/probar_gemini.sh
# ==========================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "ERROR: no encuentro .env en $(pwd)" >&2
  exit 1
fi

# Solo la linea de GEMINI_API_KEY, para no arrastrar el resto del .env.
GEMINI_API_KEY="$(grep -E '^GEMINI_API_KEY=' .env | head -1 | cut -d= -f2- | tr -d '"'"'"' \r')"

if [ -z "${GEMINI_API_KEY:-}" ]; then
  cat >&2 <<'MSG'
ERROR: GEMINI_API_KEY esta vacia en el .env.

  1. Saca la key en https://aistudio.google.com/apikey
  2. Pegala en el .env, en la linea:  GEMINI_API_KEY=
  3. Vuelve a correr este script.
MSG
  exit 1
fi

BASE="https://generativelanguage.googleapis.com/v1beta/openai/"

echo "==> Probando Gemini (LLM + embeddings) ..."
docker compose run --rm --no-deps \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY="$GEMINI_API_KEY" \
  -e OPENAI_BASE_URL="$BASE" \
  -e OPENAI_MODEL="${MODELO:-gemini-3.7-flash}" \
  -e EMBEDDING_PROVIDER=openai \
  -e EMBEDDING_OPENAI_BASE_URL="$BASE" \
  -e EMBEDDING_MODEL_OPENAI=gemini-embedding-001 \
  -e EMBEDDING_DIM=1024 \
  backend python probar_proveedor.py
