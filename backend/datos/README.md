# Corpus normativo (RAG)

Aquí van los documentos normativos en **texto plano** (`.txt`/`.md`), que son los
que ingesta el RAG. Los cinco del proyecto (EU AI Act, GDPR, NIST AI RMF y las
leyes chilenas 19.628 y 20.609) ya están versionados.

Los PDF originales **no** se versionan (pesan demasiado); la conversión a texto
se hace por fuera con [`../convertir_pdf.sh`](../convertir_pdf.sh).

Para cargar los cinco documentos de una vez, usa
[`deploy/cargar_datos.sh`](../../deploy/cargar_datos.sh). Para uno suelto, con
`docker compose` levantado:

```bash
# documento nuevo
docker compose exec backend python -m rag.ingest \
  --archivo /app/datos/ejemplo_norma.txt \
  --nombre "Norma de ejemplo" --jurisdiccion UE --tema "IA"

# documento ya existente (por id)
docker compose exec backend python -m rag.ingest \
  --archivo /app/datos/otra_norma.txt --documento-id <uuid>
```

Requisitos para que la ingesta genere vectores — uno de estos tres:

- `EMBEDDING_PROVIDER=openai` con `OPENAI_API_KEY` (lo que usa el proyecto:
  `text-embedding-3-small`, ~1 centavo por todo el corpus);
- `EMBEDDING_PROVIDER=local` con Ollama corriendo y el modelo disponible en
  `EMBEDDING_LOCAL_BASE_URL` (100% offline, gratis);
- `EMBEDDING_PROVIDER=hosted` con `VOYAGE_API_KEY`.

El chunking se hace por estructura legal (artículo / considerando / sección), no
por tamaño fijo. `EMBEDDING_DIM` debe coincidir con el modelo elegido y con la
columna `VECTOR` del esquema (1024 por defecto).
