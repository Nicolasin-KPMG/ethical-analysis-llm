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
# Requiere estas variables de entorno:
#   NEON_URL   cadena de conexion de Neon, terminada en ?sslmode=require
#   GEMINI_KEY API key de Google AI Studio
#   API_URL    URL publica del backend en Render (https://....onrender.com)
#
# Uso:
#   NEON_URL='postgresql://...' GEMINI_KEY='...' API_URL='https://...' \
#     bash deploy/cargar_datos_remoto.sh
# ==========================================================================
set -euo pipefail

: "${NEON_URL:?Falta NEON_URL}"
: "${GEMINI_KEY:?Falta GEMINI_KEY}"
: "${API_URL:?Falta API_URL}"

GEMINI_BASE="https://generativelanguage.googleapis.com/v1beta/openai/"

# `run --rm --no-deps` usa la imagen del backend sin levantar el Postgres local.
en_backend () {
  docker compose run --rm --no-deps \
    -e DATABASE_URL="$NEON_URL" \
    -e OPENAI_API_KEY="$GEMINI_KEY" \
    -e EMBEDDING_PROVIDER=openai \
    -e EMBEDDING_OPENAI_BASE_URL="$GEMINI_BASE" \
    -e EMBEDDING_MODEL_OPENAI=gemini-embedding-001 \
    -e EMBEDDING_DIM=1024 \
    backend "$@"
}

echo "==> 0/3  Aplicando migraciones en Neon (crea el esquema y pgvector)..."
en_backend alembic upgrade head

ingest () {
  local archivo="$1" nombre="$2" jur="$3" tema="$4"
  echo "==> Ingestando: $nombre"
  en_backend python -m rag.ingest \
    --archivo "/app/datos/$archivo" --nombre "$nombre" \
    --jurisdiccion "$jur" --tema "$tema"
}

echo "==> 1/3  Ingestando el corpus normativo (embeddings con Gemini)..."
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
