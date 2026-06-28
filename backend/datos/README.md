# Corpus normativo (RAG)

Coloca aquí los documentos normativos en **texto plano** (`.txt`/`.md`) para
ingerirlos al RAG. La extracción de PDF a texto se hace por fuera (los PDF reales
son un pendiente del autor; ver sección 13 del contexto).

Ingesta de un documento (con `docker compose` levantado):

```bash
# documento nuevo
docker compose exec backend python -m rag.ingest \
  --archivo /app/datos/ejemplo_norma.txt \
  --nombre "Norma de ejemplo" --jurisdiccion UE --tema "IA"

# documento ya existente (por id)
docker compose exec backend python -m rag.ingest \
  --archivo /app/datos/otra_norma.txt --documento-id <uuid>
```

Requisitos para que la ingesta genere vectores:
- `EMBEDDING_PROVIDER=hosted` con `VOYAGE_API_KEY` configurada, **o**
- `EMBEDDING_PROVIDER=local` con Ollama corriendo y el modelo de embeddings
  disponible en `EMBEDDING_LOCAL_BASE_URL` (100% offline).

El chunking se hace por estructura legal (artículo / considerando / sección),
no por tamaño fijo. `EMBEDDING_DIM` debe coincidir con el modelo elegido (1024
por defecto: voyage-3 y multilingual-e5-large).
