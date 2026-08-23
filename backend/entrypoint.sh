#!/usr/bin/env bash
# Arranque del backend en docker-compose.
# 1) Espera a que Postgres acepte conexiones.
# 2) Aplica las migraciones de Alembic (crea el esquema).
# 3) Levanta uvicorn con reload (desarrollo).
set -e

echo "Esperando a PostgreSQL..."
python - <<'PY'
import time
import sqlalchemy
from config import settings

engine = sqlalchemy.create_engine(settings.database_url)
for intento in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        print("PostgreSQL listo.")
        break
    except Exception as exc:
        print(f"  ...todavia no ({intento + 1}/30): {exc}")
        time.sleep(2)
else:
    raise SystemExit("No se pudo conectar a PostgreSQL.")
PY

echo "Aplicando migraciones (alembic upgrade head)..."
alembic upgrade head

# Puerto: en compose es 8000; los PaaS (Render, Koyeb...) inyectan $PORT.
PUERTO="${PORT:-8000}"

# Recarga automatica solo en desarrollo. En el despliegue APP_ENV=prod, donde
# --reload sobra y consume memoria (las instancias gratis son de 512 MB).
if [ "${APP_ENV:-dev}" = "prod" ]; then
  echo "Levantando uvicorn (prod) en :$PUERTO ..."
  exec uvicorn main:app --host 0.0.0.0 --port "$PUERTO"
else
  echo "Levantando uvicorn (dev, reload) en :$PUERTO ..."
  exec uvicorn main:app --host 0.0.0.0 --port "$PUERTO" --reload
fi
