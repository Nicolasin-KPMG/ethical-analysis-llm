# Imagen del backend FastAPI.
FROM python:3.12-slim

# Evita .pyc y fuerza logs sin buffer (mejor para ver en docker logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema: libpq para psycopg2 y poppler-utils para pdftotext
# (conversion de los PDF normativos a texto antes de ingerirlos al RAG).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Instala dependencias primero para aprovechar la cache de capas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el codigo.
COPY . .

# Entrypoint: aplica migraciones y luego levanta el servidor con reload.
RUN chmod +x /app/entrypoint.sh
CMD ["/app/entrypoint.sh"]
