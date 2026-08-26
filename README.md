# Gestión ética y priorización de requisitos

Herramienta web que sistematiza un **método de seis fases** para detectar las
implicancias éticas de los requisitos de un proyecto de software con IA,
decidir cómo tratarlas y priorizarlos equilibrando valor y riesgo.

Desarrollada como parte de una tesis de magíster. El análisis ético se apoya en
un LLM con **RAG sobre un corpus normativo real** (EU AI Act, GDPR, NIST AI RMF
y las leyes chilenas 19.628 y 20.609), de modo que las citas que devuelve son
artículos existentes y no texto generado.

## El método

El proceso va de una entrada a una salida, y la salida de cada fase es la
entrada de la siguiente:

| Paso | Pantalla | Qué hace |
|---|---|---|
| **Entrada** | `/registro` | Registro de los requisitos del proyecto |
| **Fase 1** | `/analisis` | Identificación de temas éticos (LLM + RAG, tres capas) |
| **Fase 2** | `/analisis` | Tratamiento: reformular, mitigar, eliminar o aceptar |
| **Fase 3** | `/dimensiones` | Definición de dimensiones de priorización y sus pesos |
| **Fase 4** | `/evaluacion` | Matriz de requisitos × dimensiones |
| **Fase 5** | `/ranking` | Cálculo del ranking (determinista, sin IA) |
| **Fase 6** | `/trazabilidad` | Trazabilidad de derivados y regla de arrastre |
| **Salida** | `/visualizacion` | Ranking auditable con desglose y export CSV |

Puntaje = beneficio + valor ético − costo − riesgo ético. Solo entran los
requisitos vigentes y no eliminados.

## Stack

- **Frontend:** Next.js (App Router) + TypeScript + Tailwind
- **Backend:** Python + FastAPI, autenticación con JWT
- **Base de datos:** PostgreSQL + pgvector
- **LLM y embeddings:** proveedores enchufables (OpenAI, Anthropic, o cualquier
  endpoint compatible con OpenAI: Gemini, Groq, Ollama...)
- **Local:** docker-compose

## Correr en local

Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env     # ajusta al menos OPENAI_API_KEY
docker compose up --build
```

El backend espera a PostgreSQL y aplica las migraciones de Alembic solo (crea el
esquema y las extensiones `pgcrypto` y `pgvector`).

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3001 |
| API | http://localhost:8001 |
| Swagger | http://localhost:8001/docs |
| Healthcheck | http://localhost:8001/health |

> Los puertos van remapeados (3001 y 8001) para no chocar con servicios que
> suelen ocupar el 3000 y el 8000.

### Datos de prueba

```bash
API_URL=http://localhost:8001 python3 backend/seed_demo.py
```

Crea el usuario `demo@example.com` / `demo1234` con un proyecto de ejemplo,
sus dimensiones, diez requisitos y la matriz de evaluación completa.

### Corpus normativo

Los documentos en texto están versionados en [backend/datos/](backend/datos/).
Para indexarlos (hace falta un proveedor de embeddings activo):

```bash
docker compose exec backend python -m rag.ingest \
  --archivo /app/datos/GDPR.txt --nombre "GDPR" \
  --jurisdiccion UE --tema "Protección de datos"
```

La ingesta es reanudable: omite los documentos ya cargados, y `--forzar` los
reindexa. Al cambiar de modelo de embeddings hay que reindexar **todo**, porque
los vectores de modelos distintos no son comparables y la búsqueda no filtra por
modelo.

## Despliegue

La app está pensada para correr repartida: frontend en **Vercel**, backend en
**Render** y base de datos en **Neon**. El runbook completo, con las variables
de entorno de cada servicio, está en
[deploy/DEPLOY_GRATIS.md](deploy/DEPLOY_GRATIS.md); [render.yaml](render.yaml)
trae el blueprint del backend.

Existe también un runbook para servidor propio con Docker y HTTPS en
[deploy/DEPLOY.md](deploy/DEPLOY.md).

## Proveedores de IA

Cambiar de proveedor es cambiar variables de entorno, sin tocar código:

| Variable | Para qué |
|---|---|
| `LLM_PROVIDER` | `openai` \| `anthropic` \| `local` |
| `OPENAI_MODEL` | modelo del análisis (la tesis usa `gpt-4.1`) |
| `OPENAI_BASE_URL` | vacío = OpenAI; si se llena, cualquier API compatible |
| `EMBEDDING_MODEL_OPENAI` | modelo de embeddings (`text-embedding-3-small`) |
| `EMBEDDING_OPENAI_API_KEY` | credencial propia si LLM y embeddings son de proveedores distintos |
| `EMBEDDING_DIM` | debe coincidir con la columna `VECTOR` del esquema (1024) |
| `EMBEDDING_RPM` | freno por minuto, para proveedores con cuota (0 = sin límite) |

Para validar un proveedor nuevo antes de desplegar:

```bash
docker compose run --rm --no-deps backend python probar_proveedor.py
```

Comprueba las dos cosas que suelen romperse al cambiar: que el modelo respete
la salida JSON estructurada y que los embeddings tengan las dimensiones
esperadas.

## Estructura

```
/frontend                # Next.js (App Router)
  /app                   # una ruta por paso del método
  /components            # sistema de diseño y layout
  /lib                   # cliente de la API y mapeos de estado
/backend
  /providers             # capa enchufable: llm.py, embeddings.py
  /rag                   # ingest.py, store.py, retrieve.py
  /models                # tablas SQLAlchemy
  /schemas               # Pydantic (incluye las tres capas del análisis)
  /services              # analysis.py, ranking.py, cribado.py, auth.py
  /routers               # un router por grupo de fases
  /alembic               # migraciones
  /datos                 # corpus normativo en texto
/deploy                  # runbooks y scripts de despliegue
```

## Migraciones

```bash
# Tras cambiar los modelos
docker compose exec backend alembic revision --autogenerate -m "mensaje"

# Aplicar
docker compose exec backend alembic upgrade head
```
