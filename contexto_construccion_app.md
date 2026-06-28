# Contexto de construcción: herramienta de gestión ética y priorización de requisitos

Este documento es el contexto para construir la aplicación. Reúne todas las decisiones de diseño tomadas. Léelo completo antes de programar. No introduzcas funcionalidades fuera de lo descrito en "Alcance y lo que NO se construye".

---

## 1. Qué se construye

Una aplicación web que sistematiza un método de 8 fases para gestionar las implicancias éticas de los requisitos de un proyecto de software con IA y priorizarlos. En las Fases 2 y 3 un modelo de lenguaje (LLM) analiza cada requisito y un sistema RAG le aporta el texto normativo para fundamentar. El resto de las fases son gestión de datos y un cálculo de ranking.

Destinatarios: el autor de la tesis y su profesor guía (para sus clases). No es un producto comercial. Se optimiza para terminar y ser defendible, no para escala ni robustez de producción.

Principio rector del método: el LLM identifica, analiza y propone, pero el humano siempre decide. El LLM no es un oráculo.

---

## 2. Stack y arquitectura

- Frontend: Next.js (React) con TypeScript y Tailwind.
- Backend: Python con FastAPI (separado del frontend).
- Base de datos: PostgreSQL con extensión pgvector (relacional y vectorial en una sola base).
- LLM por defecto: Anthropic (Claude Sonnet). Enchufable a una LLM local.
- Embeddings por defecto: proveedor hospedado (Voyage, OpenAI o Cohere). Enchufable a embeddings locales. Anthropic no genera embeddings; por eso es una pieza aparte del LLM.
- Runtime local (para el profe): Ollama, que expone un endpoint compatible con OpenAI.
- RAG: implementado a mano, sin framework (sin LangChain ni LlamaIndex), para que cada paso sea explicable.
- Despliegue: docker-compose en local. La app debe poder correr 100% offline con modelos locales.

Razón de separar backend en Python: el ecosistema de modelos locales vive en Python, y un backend dedicado hace trivial el cambio de proveedor.

Estructura de repositorio sugerida:

```
/frontend            # Next.js
/backend
  /providers         # llm.py, embeddings.py (capa enchufable)
  /rag               # ingest.py, store.py, retrieve.py
  /models            # tablas SQLAlchemy
  /schemas           # Pydantic, incluido el esquema de salida del LLM
  /services          # ranking.py (función pura), analysis.py (orquesta Fase 2-3)
  /routers           # un router por grupo de fases
  main.py
/docker-compose.yml
```

---

## 3. Reglas de negocio clave (respetar al pie de la letra)

Estas reglas no son obvias y son fáciles de equivocar:

1. **Reformulación = nueva versión del requisito.** Cuando un requisito se reformula (lo haga el humano o el LLM), no se sobrescribe: se crea una **fila nueva** de requisito enlazada a la anterior por `version_anterior_id`. La versión anterior se marca `es_vigente = false` y conserva su análisis como historial (para mostrar el antes y después). La versión nueva nace `es_vigente = true` y debe volver a pasar por la Fase 2 (re-análisis) y por la Fase 5 (evaluación), partiendo sin evaluaciones.
2. **Solo la versión vigente se evalúa y entra al ranking.** Las versiones anteriores quedan archivadas como historial de análisis, sin puntaje. Filtrar siempre por `es_vigente = true` en Fases 5 y 6.
3. **Mitigar genera requisitos derivados.** La decisión "mitigar" en la Fase 3 crea requisitos nuevos (derivados) enlazados al padre por `origen_requisito_id` y registrados en `relacion_requisito`. Los derivados se evalúan en la Fase 5 y entran al ranking como cualquier requisito vigente, manteniendo el vínculo con su padre.
4. **version_anterior_id y origen_requisito_id son enlaces distintos** sobre la misma tabla `requisito`. El primero es la cadena de versiones (reformulación); el segundo es la relación padre-hijo (mitigación). No confundirlos.
5. **Eliminar no borra.** La decisión "eliminar" marca `estado = eliminado` y excluye al requisito del ranking, pero la fila se conserva para trazabilidad.
6. **El humano edita libremente lo que propone el LLM** en las Fases 2-3: aceptar, rechazar, editar texto, agregar un tema que el modelo no detectó o quitar uno.
7. **Las reformulaciones que proponga el LLM deben estar diseñadas para resolver o reducir el conflicto ético detectado**, no ser una redacción cualquiera. Esto es una instrucción para el prompt del analizador.
8. **El LLM solo interviene en las Fases 2 y 3.** La Fase 6 (ranking) es determinista y no usa IA, para que la priorización sea auditable.
9. **Multinorma por defecto.** Cada proyecto contrasta contra todas las normas activas, pero existe una configuración (checkbox por proyecto) para acotar el conjunto. La recuperación del RAG filtra por las normas activas del proyecto.
10. **En la Fase 5, fuerza de asociación 0 a 5, donde 0 significa "no aplica".**

---

## 4. El método de 8 fases (especificación funcional)

**Fase 1. Registro de requisitos.** El usuario registra requisitos con: código, nombre, descripción, tipo (funcional, no funcional, restricción, otro), stakeholder y estado (inicia en "pendiente de análisis"). Salida: lista de requisitos.

**Fase 2. Identificación de temas éticos (LLM + RAG).** Para cada requisito vigente, el LLM detecta temas éticos. Por cada tema detectado se registra: tema ético, actor o grupo afectado, tipo de daño, norma tensionada (texto) y evidencia, además del vínculo al fragmento normativo concreto que lo respalda. El LLM produce también las Capas 2 y 3 (ver sección 5). El usuario puede editar todo. Salida: análisis ético del requisito.

**Fase 3. Tratamiento.** Para cada requisito con temas éticos, el usuario decide entre: aceptar, reformular, mitigar, eliminar. El LLM propone la decisión, reformulaciones y derivados, con su justificación. Reformular crea una versión nueva (regla 1). Mitigar crea derivados (regla 3). Eliminar marca el estado (regla 5). Salida: decisión de tratamiento registrada.

**Fase 4. Definición dinámica de dimensiones.** El usuario define las dimensiones de priorización del proyecto. Cada dimensión tiene un tipo: beneficio, valor_etico, costo o riesgo_etico_residual. Beneficio y valor_etico suman; costo y riesgo_etico_residual restan. Cada dimensión tiene un peso (1 a 5) con justificación.

**Fase 5. Relación entre requisitos y dimensiones.** Cada requisito vigente se evalúa frente a cada dimensión con una fuerza de asociación de 0 a 5 (0 = no aplica), con justificación. Salida: matriz de evaluación.

**Fase 6. Cálculo del ranking (automático, sin LLM).** Por requisito:

```
PuntajeFinal =   Σ (peso × fuerza) de dimensiones de tipo beneficio
               + Σ (peso × fuerza) de dimensiones de tipo valor_etico
               − Σ (peso × fuerza) de dimensiones de tipo costo
               − Σ (peso × fuerza) de dimensiones de tipo riesgo_etico_residual
```

Se ordena de mayor a menor. Cálculo en vivo desde la matriz, con opción de guardar una foto del ranking (snapshot) para el experimento.

**Fase 7. Gestión de derivados y trazabilidad.** Se registran las relaciones origen-derivado y las reglas de arrastre (por ejemplo, un derivado obligatorio no debe quedar por debajo del requisito que mitiga).

**Fase 8. Visualización del ranking.** Ranking ordenado y auditable, con el desglose por requisito en beneficio, valor ético, costo y riesgo ético residual, y una bandera ética (verde, amarilla, roja) por requisito. La bandera informa, no bloquea.

---

## 5. Salida del LLM: las tres capas

El analizador devuelve un objeto estructurado (validado con Pydantic) por requisito:

```json
{
  "capa_1_identificacion": [
    {
      "tema_etico": "string",
      "actor_afectado": "string",
      "tipo_dano": "string",
      "norma_tensionada_texto": "string",
      "evidencia": "string",
      "citas": [{ "chunk_id": "uuid", "texto_citado": "string" }]
    }
  ],
  "capa_2_analisis": {
    "mapa_stakeholders": [],
    "tensiones_de_valores": [],
    "argumentos_marcos_eticos": []
  },
  "capa_3_deliberacion": {
    "opciones_tratamiento": [],
    "reformulaciones_propuestas": [],
    "requisitos_derivados_propuestos": [],
    "preguntas_deliberativas": []
  },
  "nivel_confianza": "alta | media | baja",
  "limitaciones": "string"
}
```

Persistencia: la Capa 1 se guarda en columnas relacionales (tabla `tema_etico_detectado`) con sus citas. Las Capas 2 y 3, junto con confianza y limitaciones, se guardan como JSON en la tabla `analisis_etico`.

---

## 6. Capa de proveedores (LLM y embeddings enchufables)

La aplicación nunca llama directamente al SDK de Anthropic ni a un modelo local. Llama a interfaces. Cambiar de proveedor es cambiar variables de entorno.

```python
# providers/llm.py
class LLMProvider:
    def analyze(self, prompt: str, schema: dict) -> dict: ...

class AnthropicLLM(LLMProvider): ...   # SDK de Anthropic (Claude)
class LocalLLM(LLMProvider): ...       # endpoint compatible con OpenAI (Ollama / vLLM)

# providers/embeddings.py
class EmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]: ...

class HostedEmbeddings(EmbeddingProvider): ...   # Voyage / OpenAI / Cohere
class LocalEmbeddings(EmbeddingProvider): ...     # sentence-transformers / Ollama
```

Configuración:

```bash
# .env
LLM_PROVIDER=anthropic            # o: local
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-sonnet-4-6
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.1:8b

EMBEDDING_PROVIDER=hosted         # o: local
EMBEDDING_MODEL_HOSTED=voyage-3
EMBEDDING_MODEL_LOCAL=intfloat/multilingual-e5-large
EMBEDDING_DIM=1024                # debe coincidir con el modelo elegido
```

Advertencias:
- Cambiar el LLM es inmediato. Cambiar el modelo de embeddings obliga a re-indexar todo el corpus normativo, porque los vectores no son compatibles entre modelos. Guardar `modelo_embedding` junto a cada vector para detectar incompatibilidades.
- Los modelos de embeddings deben ser multilingües (las normas están en español e inglés).

---

## 7. Módulo RAG (solo Fases 2-3, a mano)

**Ingesta (offline, una vez por documento).** Cargar los PDF normativos, limpiar el texto (encabezados, pies de página, numeración), chunquear por estructura legal (artículo, considerando, sección), no por tamaño fijo. Guardar metadatos (norma, referencia, jurisdicción, tema). Generar embeddings y almacenar en pgvector.

**Recuperación (durante el análisis de un requisito), en `services/analysis.py`:**
1. El LLM hace un primer pase y propone temas y familias de normas candidatas para el requisito.
2. Se recuperan los fragmentos relevantes de la base vectorial, filtrando por esos temas, por la jurisdicción y por las normas activas del proyecto, combinando similitud semántica con filtro por metadatos.
3. El LLM produce el análisis final (las tres capas) usando esos fragmentos como contexto, citando el fragmento recuperado como evidencia.
4. La salida se valida contra el esquema y se registran los fragmentos citados. Si una afirmación no se apoya en ningún fragmento recuperado, se marca como baja confianza.

---

## 8. Modelo de datos (PostgreSQL)

```sql
CREATE TABLE proyecto (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre        TEXT NOT NULL,
  descripcion   TEXT,
  fecha_creacion TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE documento_normativo (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre       TEXT NOT NULL,         -- EU AI Act, GDPR, Boletín 16821-19, etc.
  jurisdiccion TEXT,                  -- UE, EEUU, Chile
  version      TEXT,
  fuente_url   TEXT
);

CREATE TABLE proyecto_norma_activa (   -- multinorma con checkbox; por defecto todas activas
  proyecto_id  UUID REFERENCES proyecto(id) ON DELETE CASCADE,
  documento_id UUID REFERENCES documento_normativo(id),
  PRIMARY KEY (proyecto_id, documento_id)
);

CREATE TABLE requisito (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proyecto_id         UUID REFERENCES proyecto(id) ON DELETE CASCADE,
  codigo              TEXT,
  nombre              TEXT NOT NULL,
  descripcion         TEXT,
  tipo                TEXT,            -- funcional, no funcional, restriccion, otro
  stakeholder         TEXT,
  estado              TEXT DEFAULT 'pendiente_de_analisis', -- ..., aceptado, reformulado, mitigado, eliminado
  es_vigente          BOOLEAN DEFAULT true,
  version_anterior_id UUID REFERENCES requisito(id),  -- cadena de versiones (reformulacion)
  origen_requisito_id UUID REFERENCES requisito(id)   -- padre (mitigacion / derivado)
);

CREATE TABLE analisis_etico (          -- Fase 2-3, capas 2 y 3 + metadatos del analisis
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requisito_id  UUID REFERENCES requisito(id) ON DELETE CASCADE,
  generado_por  TEXT,                  -- llm | humano
  modelo_usado  TEXT,
  nivel_confianza TEXT,                -- alta | media | baja
  limitaciones  TEXT,
  capas_2_3     JSONB,                 -- mapa stakeholders, tensiones, opciones, preguntas, etc.
  creado_en     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE tema_etico_detectado (    -- Fase 2, capa 1 relacional
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analisis_id   UUID REFERENCES analisis_etico(id) ON DELETE CASCADE,
  tema_etico    TEXT,
  actor_afectado TEXT,
  tipo_dano     TEXT,
  norma_tensionada_texto TEXT,
  evidencia     TEXT
);

CREATE TABLE cita_normativa (          -- trazabilidad: tema -> fragmento concreto
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tema_id       UUID REFERENCES tema_etico_detectado(id) ON DELETE CASCADE,
  chunk_id      UUID REFERENCES chunk_normativo(id),
  texto_citado  TEXT
);

CREATE TABLE tratamiento (             -- Fase 3
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requisito_id  UUID REFERENCES requisito(id) ON DELETE CASCADE,
  decision      TEXT,                  -- aceptar | reformular | mitigar | eliminar
  justificacion TEXT,
  responsable   TEXT,
  creado_en     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE relacion_requisito (      -- Fase 7
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  origen_id     UUID REFERENCES requisito(id) ON DELETE CASCADE,
  derivado_id   UUID REFERENCES requisito(id) ON DELETE CASCADE,
  tipo_relacion TEXT,
  obligatorio   BOOLEAN DEFAULT true
);

CREATE TABLE dimension (               -- Fase 4
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proyecto_id   UUID REFERENCES proyecto(id) ON DELETE CASCADE,
  nombre        TEXT NOT NULL,
  tipo          TEXT NOT NULL,         -- beneficio | valor_etico | costo | riesgo_etico_residual
  descripcion   TEXT,
  peso          INT CHECK (peso BETWEEN 1 AND 5),
  justificacion_peso TEXT
);

CREATE TABLE evaluacion_dimension (    -- Fase 5 (solo requisitos vigentes)
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requisito_id  UUID REFERENCES requisito(id) ON DELETE CASCADE,
  dimension_id  UUID REFERENCES dimension(id) ON DELETE CASCADE,
  fuerza        INT CHECK (fuerza BETWEEN 0 AND 5),
  justificacion TEXT,
  responsable   TEXT,
  UNIQUE (requisito_id, dimension_id)
);

CREATE TABLE ranking_snapshot (        -- Fase 6/8, foto opcional para el experimento
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  proyecto_id   UUID REFERENCES proyecto(id) ON DELETE CASCADE,
  creado_en     TIMESTAMPTZ DEFAULT now(),
  datos         JSONB
);

CREATE TABLE chunk_normativo (         -- RAG (pgvector)
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  documento_id    UUID REFERENCES documento_normativo(id) ON DELETE CASCADE,
  referencia      TEXT,                -- articulo / seccion
  texto           TEXT,
  metadatos       JSONB,               -- norma, jurisdiccion, tema
  embedding       VECTOR(1024),        -- ajustar dimension al modelo de embeddings
  modelo_embedding TEXT
);
```

Nota: `cita_normativa` referencia `chunk_normativo`; crear las tablas en el orden correcto o diferir la FK.

---

## 9. API (endpoints por fase)

- Proyectos: crear, listar, configurar normas activas.
- Fase 1: `POST /proyectos/{id}/requisitos`, `GET`, `PUT`, manejo de versiones y derivados.
- Fases 2-3: `POST /requisitos/{id}/analizar` (LLM + RAG), `PUT /requisitos/{id}/analisis` (edición humana), `POST /requisitos/{id}/tratamiento`. Reformular y mitigar crean filas nuevas de requisito según las reglas.
- Fase 4: CRUD de `dimension`.
- Fase 5: guardar y listar `evaluacion_dimension`.
- Fase 6: `GET /proyectos/{id}/ranking` (cálculo en vivo), `POST /proyectos/{id}/ranking/snapshot`.
- Fase 7: CRUD de `relacion_requisito`.
- Fase 8: `GET /proyectos/{id}/visualizacion`, exportación.

---

## 10. Frontend (pantallas)

Una pestaña por fase, navegables como el flujo de 8 pasos. Las de CRUD son formularios y tablas. La pantalla de Fases 2-3 es la rica: muestra el análisis del LLM en las tres capas, permite editar todo, y soporta el ciclo de reformulación con vista de antes y después (el re-análisis es una acción explícita del usuario, nunca automática, para evitar bucles).

---

## 11. Orden de construcción (hitos)

- M0. Setup: repos, PostgreSQL + pgvector, esqueleto FastAPI y Next.js, capa de proveedores (la local puede ser stub al inicio).
- M1. Modelo de datos + Fase 1.
- M2. Fases 4, 5 y 6 (motor de priorización funcionando, ética manual).
- M3. Fase 8 (visualización).
- M4. RAG: ingesta y base vectorial de los documentos normativos.
- M5. Fases 2-3 (análisis con LLM + RAG, las tres capas). La parte más difícil.
- M6. Fase 7, exportación y pulido.

Al terminar M3 la herramienta ya prioriza requisitos sin IA. Esa versión manual es la línea base del experimento de la tesis; la versión con LLM (M5) es el tratamiento.

---

## 12. Alcance y lo que NO se construye

No construir: autenticación, usuarios ni multiusuario; multitenancy; endurecimiento de producción; entrenamiento o ajuste fino de modelos; ontologías o grafos formales; framework de RAG (se hace a mano); campos de severidad e incertidumbre en la Fase 2 (se eliminaron del método); un campo separado de riesgo residual 0-3 (el riesgo ético residual es ahora un tipo de dimensión).

---

## 13. Pendientes por resolver con el autor

- Conseguir y limpiar los PDF normativos (EU AI Act, NIST, Boletín 16821-19, GDPR, Ley 19.628, Ley 20.609).
- Elegir el modelo de embeddings hospedado y su equivalente local (ambos multilingües) y fijar `EMBEDDING_DIM`.
- Decidir si las normas más usadas y estables van fijas en el prompt y el RAG se reserva para el resto, o si todo pasa por RAG.
- Definir la granularidad del chunking para artículos legales muy largos.
- Redactar el prompt operativo del analizador (debe producir las tres capas y reformulaciones que resuelvan el conflicto detectado).
