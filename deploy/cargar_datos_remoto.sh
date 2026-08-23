#!/usr/bin/env bash
# ==========================================================================
# Carga inicial de datos contra el despliegue GRATIS (Neon + Render + Vercel).
# Se corre UNA VEZ desde tu maquina, no desde el servidor.
#
#   1) Ingesta los 5 documentos normativos al RAG en la base de Neon.
#      (Usa la imagen local del backend, pero apuntando DATABASE_URL a Neon;
#       asi no hay que instalar Python ni las dependencias fuera de Docker.)
#   2) Crea el usuario/proyecto demo llamando a la API publica de Render.
#
# NEON_URL y GEMINI_KEY se leen del .env (donde ya estan guardadas).
# API_URL hay que pasarla: es la URL publica del backend en Render.
#
# Uso:
#   API_URL='https://tesis-backend.onrender.com' bash deploy/cargar_datos_remoto.sh
# ==========================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

# Lee una variable del .env sin arrastrar el resto del archivo.
del_env () { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' \r'; }

NEON_URL="${NEON_URL:-$(del_env NEON_URL)}"
# Embeddings por OpenAI y no por Gemini: el tier gratis de Gemini topa en 1000
# embeddings AL DIA y el corpus son 844, asi que una sola reindexacion agota la
# cuota. text-embedding-3-small cuesta ~1 centavo por todo el corpus y no tiene
# tope diario. El LLM sigue siendo Gemini (gratis): son piezas independientes.
OPENAI_KEY="${OPENAI_KEY:-$(del_env OPENAI_API_KEY)}"

: "${NEON_URL:?Falta NEON_URL (ponla en el .env)}"
: "${OPENAI_KEY:?Falta OPENAI_API_KEY en el .env (embeddings)}"
: "${API_URL:?Falta API_URL (la URL del backend en Render)}"

# `run --rm --no-deps` usa la imagen del backend sin levantar el Postgres local.
en_backend () {
  docker compose run --rm --no-deps \
    -e DATABASE_URL="$NEON_URL" \
    -e EMBEDDING_PROVIDER=openai \
    -e EMBEDDING_OPENAI_API_KEY="$OPENAI_KEY" \
    -e EMBEDDING_OPENAI_BASE_URL= \
    -e EMBEDDING_MODEL_OPENAI=text-embedding-3-small \
    -e EMBEDDING_DIM=1024 \
    -e EMBEDDING_RPM="${EMBEDDING_RPM:-0}" \
    backend "$@"
}

echo "==> 0/3  Aplicando migraciones en Neon (crea el esquema y pgvector)..."
en_backend alembic upgrade head

# FORZAR=1 re-ingesta documentos ya cargados. Obligatorio al cambiar de modelo
# de embeddings: los vectores de modelos distintos no son comparables y la
# busqueda no filtra por modelo, asi que un corpus mezclado da citas malas.
ingest () {
  local archivo="$1" nombre="$2" jur="$3" tema="$4"
  echo "==> Ingestando: $nombre"
  en_backend python -m rag.ingest \
    --archivo "/app/datos/$archivo" --nombre "$nombre" \
    --jurisdiccion "$jur" --tema "$tema" ${FORZAR:+--forzar}
}

echo "==> 1/3  Ingestando el corpus normativo (embeddings con OpenAI)..."
# archivo                       nombre                                   jurisdiccion  tema
ingest "AI_Act.txt"                 "EU AI Act"                          "UE"    "IA de alto riesgo"
ingest "GDPR.txt"                   "GDPR"                               "UE"    "Proteccion de datos"
ingest "NIST_AI_100-1.txt"          "NIST AI Risk Management Framework"  "EEUU"  "Gestion de riesgos de IA"
ingest "LEY-19628_28-AGO-1999.txt"  "Ley 19.628 (Proteccion de la vida privada, Chile)" "Chile" "Proteccion de datos"
ingest "Ley-20609_24-JUL-2012.txt"  "Ley 20.609 (Antidiscriminacion, Chile)"           "Chile" "No discriminacion"

echo "==> 2/3  Despertando el backend de Render (la instancia free duerme)..."
curl -fsS --max-time 180 "$API_URL/health" && echo

echo "==> 3/3  Sembrando usuario y proyecto demo via API..."
API_URL="$API_URL" python3 backend/seed_demo.py

echo ""
echo "======================================================================"
echo " LISTO."
echo " App:      (la URL de Vercel)"
echo " Usuario:  demo@example.com  /  demo1234"
echo " El profe puede crear su propia cuenta desde la pantalla de registro."
echo "======================================================================"
