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

Necesitas **Docker con Docker Compose** y una **API key de OpenAI** (la misma
clave cubre el LLM y los embeddings; indexar todo el corpus cuesta ~1 centavo y
una sesión de análisis ~0,26 USD). Si prefieres no gastar nada, más abajo está
la alternativa 100% local con Ollama.

**1. Configura el entorno.** Copia el ejemplo y rellena `OPENAI_API_KEY`; el
resto de valores ya vienen puestos:

```bash
cp .env.example .env
```

**2. Levanta los tres servicios** (base de datos, backend y frontend):

```bash
docker compose up --build
```

El backend espera a PostgreSQL y aplica las migraciones de Alembic solo (crea el
esquema y las extensiones `pgcrypto` y `pgvector`). La primera vez tarda unos
minutos construyendo las imágenes.

**3. Carga el corpus normativo y los datos de ejemplo**, en otra terminal y con
lo anterior corriendo:

```bash
bash deploy/cargar_datos.sh
```

Esto indexa los cinco documentos normativos en el RAG (más de 800 fragmentos;
tarda varios minutos) y crea el usuario demo. **El paso no es opcional:** sin
corpus indexado, el análisis de la Fase 1 no tiene normativa que citar.

**4. Entra** a <http://localhost:3001> con `demo@example.com` / `demo1234`, o
crea tu propia cuenta con "Crear cuenta" en la pantalla de acceso.

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3001 |
| API | http://localhost:8001 |
| Swagger | http://localhost:8001/docs |
| Healthcheck | http://localhost:8001/health |

> Los puertos van remapeados (3001, 8001 y 5433 para Postgres) para no chocar
> con servicios que suelen ocupar el 3000, el 8000 y el 5432.

### Sobre los datos de ejemplo

El seed crea el usuario `demo@example.com` / `demo1234` con un proyecto de
ejemplo, sus dimensiones, diez requisitos y la matriz de evaluación completa.
`cargar_datos.sh` ya lo ejecuta; para volver a correrlo solo:

```bash
API_URL=http://localhost:8001 python3 backend/seed_demo.py
```

### Sobre el corpus normativo

Los documentos en texto están versionados en [backend/datos/](backend/datos/) —
los PDF originales no, por peso. Para indexar uno suelto:

```bash
docker compose exec backend python -m rag.ingest \
  --archivo /app/datos/GDPR.txt --nombre "GDPR" \
  --jurisdiccion UE --tema "Protección de datos"
```

La ingesta es reanudable: omite los documentos ya cargados, y `--forzar` los
reindexa. Al cambiar de modelo de embeddings hay que reindexar **todo**, porque
los vectores de modelos distintos no son comparables y la búsqueda no filtra por
modelo.

### Sin gastar en APIs

Se puede correr entero en local con [Ollama](https://ollama.com) en el host:

```bash
ollama pull llama3.1:8b && ollama pull bge-m3
```

y en el `.env`: `LLM_PROVIDER=local` y `EMBEDDING_PROVIDER=local`. Funciona, pero
la calidad del análisis ético baja bastante respecto a `gpt-4.1`, que es el
modelo con el que se generaron los resultados de la tesis.

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
/experimentacion         # material de la sesión de validación con usuarios
```

## Migraciones

```bash
# Tras cambiar los modelos
docker compose exec backend alembic revision --autogenerate -m "mensaje"

# Aplicar
docker compose exec backend alembic upgrade head
```

## Si algo falla

- **El análisis devuelve un error del proveedor (502)** → casi siempre la API key:
  revisa `OPENAI_API_KEY` y que `OPENAI_BASE_URL` esté **vacía** si usas OpenAI.
  Dejarla apuntando a otro proveedor manda tu clave ahí y devuelve
  "Please pass a valid API key".
- **El análisis no cita ninguna norma** → falta indexar el corpus:
  `bash deploy/cargar_datos.sh`.
- **La ingesta falla por dimensiones** → `EMBEDDING_DIM` tiene que coincidir con
  el modelo de embeddings y con la columna `VECTOR(1024)` del esquema.
- **El frontend carga pero no trae datos** → `NEXT_PUBLIC_API_URL` mal puesta, o
  `CORS_ORIGINS` no incluye el dominio del frontend. En la consola del navegador
  el error de CORS sale explícito. Ojo: `NEXT_PUBLIC_*` se incrusta en tiempo de
  build, así que al cambiarla hay que reconstruir el frontend.
- **Los puertos están ocupados** → se remapean en [docker-compose.yml](docker-compose.yml).
- **Empezar de cero** → `docker compose down -v` borra el volumen de la base, y
  hay que volver a correr el paso 3.
- **Ver los logs** → `docker compose logs -f backend`.
