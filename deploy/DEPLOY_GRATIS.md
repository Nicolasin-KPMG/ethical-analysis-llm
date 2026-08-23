# Despliegue gratuito (para que el profesor use la app)

Objetivo: dejar la app en una URL publica, **sin coste**, con cuentas propias
para el profesor. Alternativa a `DEPLOY.md` (DigitalOcean, ~12 USD/mes).

| Pieza | Servicio | Plan | Limite relevante |
|---|---|---|---|
| Frontend (Next.js) | **Vercel** | Hobby | gratis para este uso |
| Backend (FastAPI) | **Render** | Free | duerme a los 15 min; 750 h/mes; 5 GB de trafico |
| Base de datos | **Neon** | Free | 0.5 GB, pgvector incluido, no caduca |
| LLM | **Google AI Studio (Gemini)** | Free | 250 K tokens/min |
| Embeddings | **OpenAI** `text-embedding-3-small` | de pago | ~1 centavo todo el corpus |

Solo los embeddings cuestan dinero, y son centavos (ver abajo por que).

## Por que estos y no otros

- **Neon y no el Postgres de Render**: el Postgres gratis de Render **caduca a los
  30 dias**, y este proyecto necesita la extension `pgvector`. Neon la trae y no
  expira. Los 844 fragmentos del corpus ocupan ~3,5 MB de los 500 disponibles.
- **Gemini y no Groq**: Groq tambien es gratis y compatible con OpenAI, pero su
  limite libre es de ~12 K tokens/minuto en llama-3.3-70b. Un analisis de este
  metodo manda hasta 10 fragmentos normativos + el esquema de las tres capas +
  4096 tokens de salida, asi que se pasa del limite. Gemini da 250 K TPM.
- **Embeddings en OpenAI y no en Gemini**: el tier gratis de Gemini permite
  **1000 embeddings al dia** y el corpus son 844 fragmentos. Cabe una sola carga
  y ninguna reindexacion; cualquier reintento agota la cuota del dia (lo
  comprobamos en carne propia). `text-embedding-3-small` cuesta ~1 centavo por
  todo el corpus, no tiene tope diario y acepta `dimensions=1024`.
- **Cada pieza con su credencial**: el LLM usa `OPENAI_API_KEY` (con la clave de
  Gemini) y los embeddings usan `EMBEDDING_OPENAI_API_KEY` (la de OpenAI). Son
  proveedores distintos, asi que no pueden compartir variable.
- **El corpus no se puede mezclar**: los vectores de dos modelos distintos no son
  comparables y la busqueda **no filtra por modelo**, asi que un corpus a medias
  devuelve citas malas sin dar error. Al cambiar de modelo hay que reindexar
  todo con `FORZAR=1`.
- **Se reutiliza el proveedor `openai`**: Gemini expone una capa compatible con
  la API de OpenAI, asi que basta apuntar `OPENAI_BASE_URL` a Google. No hace
  falta un proveedor nuevo en el codigo.
- **1024 dimensiones**: `gemini-embedding-001` acepta el parametro `dimensions`,
  asi que se mantiene `EMBEDDING_DIM=1024` y **no hay que migrar** la columna
  `VECTOR(1024)` ni cambiar la migracion `0001`.

## Dos advertencias antes de empezar

1. **Los resultados no seran identicos a los del Capitulo 7.** Esos se generaron
   con `gpt-4.1`. Gemini 2.5 Flash es otro modelo: los temas eticos y las citas
   pueden variar. Si necesitas que el profe vea exactamente lo documentado,
   siembra los analisis ya generados en vez de recalcularlos en vivo.
2. **En el tier gratis de Gemini, Google usa los prompts y respuestas para
   mejorar sus productos.** Aqui solo se mandan requisitos de ejemplo y normativa
   publica, pero convendria no cargar datos reales de terceros.

---

## Paso 0 — Validar Gemini antes de desplegar

Esto ahorra depurar en produccion. Saca la API key en
<https://aistudio.google.com/apikey>, pegala en el `.env` en la linea
`GEMINI_API_KEY=` y corre:

```bash
bash deploy/probar_gemini.sh
```

Debe imprimir `TODO OK`. Comprueba las dos cosas que suelen romperse al cambiar
de proveedor: que respeta `response_format=json_object` y que devuelve vectores
de exactamente 1024 dimensiones.

El script no toca tu configuracion local: pasa las variables solo a un contenedor
de un solo uso, asi que tu `.env` sigue apuntando a OpenAI/gpt-4.1 para el
desarrollo del dia a dia.

Si falla en **embeddings por dimensiones**, el proveedor ignoro `dimensions`.
Alternativas: usar `text-embedding-3-small` de OpenAI (cuesta ~1 centavo por todo
el corpus), o migrar la columna a las dimensiones que devuelva y re-ingerir.

Si falla en **LLM**, prueba otro modelo sin tocar el `.env`:
`MODELO=gemini-3.6-flash bash deploy/probar_gemini.sh`. Los modelos viejos se
retiran para cuentas nuevas (`gemini-2.5-flash` ya no se sirve), y la lista viva
se consulta con:

```bash
curl -s -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/openai/models
```

---

## Paso 1 — Base de datos en Neon

Ya esta hecho: proyecto **TesisLLM** (`dark-term-41870672`), **Postgres 16**,
region **us-east-2**, con las migraciones aplicadas. La cadena de conexion quedo
guardada en el `.env` como `NEON_URL` (no pisa el `DATABASE_URL` local, que sigue
apuntando al Postgres de Docker).

Si necesitas recuperarla:

```bash
npx -y neonctl connection-string --project-id dark-term-41870672
```

## Paso 2 — Backend en Render

1. Sube el codigo a GitHub (`git push origin dev`).
2. En <https://render.com>: **New -> Blueprint**, apunta al repo. Detecta el
   `render.yaml` de la raiz.
3. Rellena las variables marcadas como secretas:
   - `DATABASE_URL` -> la `NEON_URL` de tu `.env`
   - `OPENAI_API_KEY` -> la API key de Gemini (para el LLM)
   - `EMBEDDING_OPENAI_API_KEY` -> la API key de OpenAI (para los embeddings)
   - `CORS_ORIGINS` -> dejalo en `*` por ahora; se ajusta en el paso 5
4. Deploy. Tarda unos minutos. Anota la URL: `https://tesis-backend.onrender.com`.
5. Verifica: `curl https://tesis-backend.onrender.com/health` -> `"database": "ok"`.

## Paso 3 — Frontend en Vercel

1. En <https://vercel.com>: **Add New -> Project**, importa el mismo repo.
2. **Root Directory: `frontend`** (importante; si no, no encuentra el proyecto).
   Framework: Next.js, detectado solo.
3. Variable de entorno:
   `NEXT_PUBLIC_API_URL = https://tesis-backend.onrender.com`
4. Deploy. Anota la URL: `https://tu-proyecto.vercel.app`.

> `NEXT_PUBLIC_*` se incrusta **en tiempo de build**. Si cambias esta variable
> despues, hay que redesplegar el frontend, no basta con reiniciarlo.

## Paso 4 — Cargar el corpus y los datos demo

Una sola vez, desde tu maquina (los `.txt` normativos ya estan en el repo):

```bash
API_URL='https://tesis-backend.onrender.com' bash deploy/cargar_datos_remoto.sh
```

`NEON_URL` y `OPENAI_API_KEY` las lee del `.env`. Para reindexar tras cambiar de
modelo de embeddings, antepon `FORZAR=1`. Ingesta los 5 documentos y crea
el usuario demo (las migraciones ya estan aplicadas, el paso es idempotente). La ingesta
tarda varios minutos (844 fragmentos).

## Paso 5 — Cerrar CORS

En Render, cambia `CORS_ORIGINS` de `*` al dominio real de Vercel:

```
CORS_ORIGINS=https://tu-proyecto.vercel.app
```

Guarda (Render redespliega solo). Si usas dominios de preview de Vercel, ponlos
separados por coma.

---

## Como le pasas la app al profesor

Enviale la **URL de Vercel**. Tiene dos caminos:

- **Cuenta propia** (recomendado): el registro esta abierto, se crea su usuario
  desde la pantalla de acceso y trabaja con sus propios proyectos, sin pisar los
  datos de la demo.
- **Cuenta demo**: `demo@example.com` / `demo1234`, que ya trae el proyecto de
  ejemplo con sus requisitos y evaluaciones cargados.

**Avisale del arranque en frio.** La instancia gratis de Render duerme tras 15
minutos sin trafico, asi que la primera pantalla puede tardar ~1 minuto en
cargar. Dos formas de suavizarlo:

- Decirselo en el correo ("si la primera carga tarda, es normal, espera un
  minuto").
- Registrar la URL `/health` en un monitor gratuito (UptimeRobot, cada 5 min)
  para que no se duerma. Consume horas del limite de 750 h/mes: 24/7 son ~730 h,
  asi que entra justo. Si lo activas, hazlo solo los dias de la evaluacion.

## Coste real

0 USD, siempre que no se pasen los limites gratis. Los puntos de riesgo son las
750 h/mes de Render (solo si lo mantienes despierto todo el mes) y los 250 K
tokens/minuto de Gemini (irrelevante con un usuario a la vez).

## Si algo falla

- **El frontend carga pero no trae datos** -> casi siempre `NEXT_PUBLIC_API_URL`
  mal puesto, o `CORS_ORIGINS` no incluye el dominio de Vercel. Mira la consola
  del navegador: un error de CORS se ve explicito.
- **Primera peticion tarda un minuto** -> es el arranque en frio de Render.
- **502 al analizar** -> el analisis son dos pasadas al LLM y puede pasarse del
  timeout de Render. Baja `RAG_MAX_FRAGMENTOS` a 6.
- **Logs del backend** -> pestana "Logs" en el panel de Render.
- **Se acabo el espacio en Neon** -> `0.5 GB`; el corpus son ~3,5 MB, asi que si
  pasa es que se ingerio el mismo documento varias veces.
