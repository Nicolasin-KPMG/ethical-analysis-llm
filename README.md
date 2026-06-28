# Gestión ética y priorización de requisitos (Tesis)

Herramienta web que sistematiza un método de 8 fases para gestionar las
implicancias éticas de los requisitos de un proyecto de software con IA y
priorizarlos. Ver [contexto_construccion_app.md](contexto_construccion_app.md).

Estado actual: **M0 (setup), M1 (Fase 1), M2 (Fases 4-6: priorización determinista),
M3 (Fase 8: visualización + CSV), M4 (RAG a mano) y M5 (Fases 2-3: análisis ético
con LLM + RAG, las tres capas, y tratamiento)**. Falta la Fase 7 y el pulido (M6).

Para correr el análisis real de las Fases 2-3 hace falta `ANTHROPIC_API_KEY`
(LLM) y, para las citas normativas, un proveedor de embeddings activo + corpus
ingerido; sin embeddings el análisis corre igual pero sin citas y con confianza
baja. La bandera ética de la Fase 8 sigue como placeholder gris (se conectará al
análisis en una iteración posterior).

El RAG (M4) está completo a nivel de código y verificado offline (chunking por
estructura legal + almacenamiento y búsqueda en pgvector). Para generar vectores
reales necesita un proveedor de embeddings activo (Voyage con API key, u Ollama
local) y los documentos normativos en texto; ver [backend/datos/](backend/datos/).

## Stack

- **Frontend:** Next.js + TypeScript + Tailwind
- **Backend:** Python + FastAPI
- **Base de datos:** PostgreSQL + pgvector
- **Orquestación:** docker-compose

## Estructura

```
/frontend            # Next.js (App Router)
/backend
  /providers         # capa enchufable: llm.py, embeddings.py
  /rag               # ingest.py, store.py, retrieve.py (stubs, M4)
  /models            # tablas SQLAlchemy (modelo de datos completo)
  /schemas           # Pydantic
  /services          # ranking.py, analysis.py (stubs, M2/M5)
  /routers           # un router por grupo de fases
  /alembic           # migraciones
  main.py
/docker-compose.yml
/.env.example
```

## Cómo levantar todo en local

Requisitos: Docker y Docker Compose.

```bash
# 1. Copia las variables de entorno (puedes dejar los valores por defecto).
cp .env.example .env

# 2. Levanta base de datos + backend + frontend.
docker compose up --build
```

Al arrancar, el backend espera a PostgreSQL y aplica las migraciones de Alembic
automáticamente (crea el esquema completo, incluidas las extensiones pgcrypto y
pgvector).

Servicios:

- Frontend: http://localhost:3000
- Backend (API): http://localhost:8000
- Documentación interactiva (Swagger): http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

## Verificar que la Fase 1 funciona

### Opción A — desde la interfaz (http://localhost:3000)

1. En la sección **Proyecto**, escribe un nombre y pulsa **Crear proyecto**.
2. En **Nuevo requisito**, completa al menos *Nombre* (y opcionalmente código,
   descripción, tipo y stakeholder) y pulsa **Registrar requisito**.
3. El requisito aparece en la tabla con estado **pendiente_de_analisis**.
4. Pulsa **Editar** en una fila, cambia algún campo y **Guardar cambios**: la
   tabla se actualiza.

### Verificar M2 (Fases 4, 5 y 6) en la interfaz

1. **Fase 4 · Dimensiones:** agrega al menos una dimensión de tipo *beneficio*
   (suma) y una de tipo *costo* (resta), cada una con peso 1–5.
2. **Fase 5 · Evaluación:** en la matriz, asigna a cada requisito una fuerza
   0–5 por dimensión (se guarda al salir de la celda).
3. **Fase 6 · Ranking:** ve el puntaje final y el desglose, ordenado de mayor a
   menor. Puntaje = beneficio + valor ético − costo − riesgo ético residual.
   Pulsa **Guardar snapshot** para archivar una foto del ranking.

Reglas respetadas: solo los requisitos vigentes y no eliminados se evalúan y
entran al ranking; el ranking es 100% determinista (sin IA).

### Opción B — desde la API (http://localhost:8001/docs o curl)

```bash
# Healthcheck
curl http://localhost:8000/health

# Crear un proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Proyecto demo"}'

# (usa el id devuelto)
PID=<id-del-proyecto>

# Crear un requisito
curl -X POST http://localhost:8000/proyectos/$PID/requisitos \
  -H "Content-Type: application/json" \
  -d '{"codigo":"REQ-001","nombre":"Login con reconocimiento facial","tipo":"funcional","stakeholder":"Usuarios"}'

# Listar requisitos del proyecto
curl http://localhost:8000/proyectos/$PID/requisitos
```

## Capa de proveedores (enchufable)

El cambio de proveedor de LLM o embeddings es sólo cambiar variables en `.env`:

- `LLM_PROVIDER=anthropic|local`
- `EMBEDDING_PROVIDER=hosted|local`

Las implementaciones locales y el análisis con LLM están como *stub* en M0/M1;
se completan en M4 (RAG) y M5 (Fases 2-3).

## Migraciones

```bash
# Generar una nueva migración tras cambiar los modelos
docker compose exec backend alembic revision --autogenerate -m "mensaje"

# Aplicar migraciones manualmente
docker compose exec backend alembic upgrade head
```
