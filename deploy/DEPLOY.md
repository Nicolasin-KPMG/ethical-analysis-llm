# Despliegue de la demo en DigitalOcean

Objetivo: que tu jefe pruebe la app **una vez** desde su navegador.
Coste real: **~0 USD** si usas el crédito de bienvenida; si no, ~1 USD por unos días
(borra el droplet al terminar).

La app corre con el mismo `docker compose` que usas en local. Lo único que cambia
respecto a local: **embeddings van por Voyage** (no Ollama) y el frontend apunta a
la **IP pública** del servidor.

---

## 0. Antes de empezar (en tu máquina)
Ten a mano tu clave (la misma sirve para el LLM y para los embeddings):
- `OPENAI_API_KEY`
- (opcional) `ANTHROPIC_API_KEY`

---

## 1. Crear el droplet
1. Entra a <https://cloud.digitalocean.com> → **Create → Droplets**.
2. **Marketplace → "Docker on Ubuntu"** (trae Docker + Compose ya instalados).
3. Plan **Basic → Regular → 2 GB RAM / 1 vCPU** (~12 USD/mes, prorrateado por hora).
   - Con 1 GB puede ir justo al construir imágenes; 2 GB va sobrado para la demo.
4. Región: **New York / San Francisco** (más cerca de Chile que Europa).
5. Autenticación: **SSH key** (recomendado) o password.
6. Crea el droplet y anota su **IP pública** (ej. `164.92.x.x`).

## 2. Abrir puertos
La app expone **3001** (frontend) y **8001** (backend). En el droplet:
```bash
ufw allow 22 && ufw allow 3001 && ufw allow 8001 && ufw --force enable
```

## 3. Subir el código
El corpus normativo (`backend/datos/*.txt`) **ya viene en el repo**, así que basta
clonar. Desde el droplet (o por ssh):
```bash
git clone <URL_DE_TU_REPO> tesis && cd tesis && git checkout dev
```
> Si tu repo es privado y no tienes deploy key, alternativa simple desde tu máquina:
> `rsync -av --exclude node_modules --exclude .next --exclude .git ./ root@IP:~/tesis/`

## 4. Configurar el `.env` del servidor
En el droplet:
```bash
cd ~/tesis
cp deploy/env.deploy.example .env
nano .env
```
Rellena todo lo marcado `<<< ... >>>`:
- `POSTGRES_PASSWORD` y la misma en `DATABASE_URL`
- `JWT_SECRET`  → genera con `openssl rand -hex 32`
- `OPENAI_API_KEY` y `VOYAGE_API_KEY`
- **`NEXT_PUBLIC_API_URL=http://IP:8001`**  ← pon la IP real

## 5. Levantar la app
```bash
cd ~/tesis
docker compose up -d --build      # tarda unos minutos la primera vez
docker compose ps                 # los 3 servicios en "Up"
```

## 6. Cargar los datos (una vez)
```bash
bash deploy/cargar_datos.sh
```
Esto ingesta los 5 documentos al RAG (con Voyage) y crea el usuario/proyecto demo.

## 7. Probar
Abre **`http://IP:3001`** en el navegador y entra con:
- **Usuario:** `demo@example.com`
- **Clave:** `demo1234`

Pásale a tu jefe esa URL y esas credenciales.

---

## Al terminar (para no seguir pagando)
En DigitalOcean: **Destroy** el droplet. Con eso deja de facturar todo.

## Si algo falla
- Logs: `docker compose logs -f backend` (o `frontend`, `db`).
- Salud del backend: `curl http://localhost:8001/health` en el droplet.
- El frontend carga pero no trae datos → casi siempre `NEXT_PUBLIC_API_URL`
  mal puesto. Corrígelo en `.env` y `docker compose up -d --build frontend`.
- Error de embeddings al ingestar → revisa `OPENAI_API_KEY` y que
  `EMBEDDING_PROVIDER=openai` en el `.env`.
