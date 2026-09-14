#!/usr/bin/env bash
# ==========================================================================
# Carga inicial de datos, para correr UNA VEZ con `docker compose` ya levantado.
# Sirve igual en local y en un servidor propio (los .txt normativos ya vienen en
# el repo). Para el despliegue Vercel+Render+Neon, usa cargar_datos_remoto.sh.
#
#   1) Ingesta los 5 documentos normativos al RAG (con el proveedor de
#      embeddings que tengas configurado en el .env).
#   2) Crea el usuario demo + proyecto + datos de ejemplo (seed).
#
# Uso:  bash deploy/cargar_datos.sh
# ==========================================================================
set -euo pipefail

echo "==> Esperando a que el backend responda en /health ..."
for i in $(seq 1 30); do
  if docker compose exec -T backend python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:8000/health')" 2>/dev/null; then
    echo "    backend OK"; break
  fi
  echo "    ...todavía no ($i/30)"; sleep 3
done

ingest () {
  local archivo="$1" nombre="$2" jur="$3" tema="$4"
  echo "==> Ingestando: $nombre"
  docker compose exec -T backend python -m rag.ingest \
    --archivo "/app/datos/$archivo" --nombre "$nombre" \
    --jurisdiccion "$jur" --tema "$tema"
}

# archivo                       nombre                                   jurisdicción  tema
ingest "AI_Act.txt"                 "EU AI Act"                          "UE"    "IA de alto riesgo"
ingest "GDPR.txt"                   "GDPR"                               "UE"    "Protección de datos"
ingest "NIST_AI_100-1.txt"          "NIST AI Risk Management Framework"  "EEUU"  "Gestión de riesgos de IA"
ingest "LEY-19628_28-AGO-1999.txt"  "Ley 19.628 (Protección de la vida privada, Chile)" "Chile" "Protección de datos"
ingest "Ley-20609_24-JUL-2012.txt"  "Ley 20.609 (Antidiscriminación, Chile)"           "Chile" "No discriminación"

echo "==> Cargando datos de demo (seed): usuario, proyecto, evaluaciones ..."
docker compose exec -T -e API_URL=http://localhost:8000 backend python seed_demo.py

echo ""
echo "======================================================================"
echo " LISTO. Entra desde el navegador:
   - en local:         http://localhost:3001
   - servidor propio:  http://TU_IP_PUBLICA:3001"
echo " Usuario demo:  demo@example.com   /   demo1234"
echo "======================================================================"
