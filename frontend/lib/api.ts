// Cliente minimo del backend. Centraliza la URL base y el manejo de errores.
// La URL se inyecta por variable de entorno (NEXT_PUBLIC_API_URL).

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// --- Tipos que reflejan los esquemas del backend (Fase 1) ---

export type Proyecto = {
  id: string;
  nombre: string;
  descripcion?: string | null;
  fecha_creacion?: string | null;
};

export type Requisito = {
  id: string;
  proyecto_id?: string | null;
  codigo?: string | null;
  nombre: string;
  descripcion?: string | null;
  tipo?: string | null;
  stakeholder?: string | null;
  estado?: string | null;
  es_vigente?: boolean | null;
  version_anterior_id?: string | null;
  origen_requisito_id?: string | null;
};

export type RequisitoInput = {
  codigo?: string;
  nombre: string;
  descripcion?: string;
  tipo?: string;
  stakeholder?: string;
};

// Tipos de dimension (Fase 4). Los dos primeros suman; los dos ultimos restan.
export type TipoDimension =
  | "beneficio"
  | "valor_etico"
  | "costo"
  | "riesgo_etico_residual";

export type Dimension = {
  id: string;
  proyecto_id?: string | null;
  nombre: string;
  tipo: TipoDimension;
  descripcion?: string | null;
  peso?: number | null;
  justificacion_peso?: string | null;
};

export type DimensionInput = {
  nombre: string;
  tipo: TipoDimension;
  descripcion?: string;
  peso: number;
  justificacion_peso?: string;
};

export type Evaluacion = {
  id: string;
  requisito_id: string;
  dimension_id: string;
  fuerza: number;
  justificacion?: string | null;
  responsable?: string | null;
};

export type RankingItem = {
  requisito_id: string;
  codigo?: string | null;
  nombre: string;
  puntaje_final: number;
  desglose: {
    beneficio: number;
    valor_etico: number;
    costo: number;
    riesgo_etico_residual: number;
  };
};

export type RankingOut = {
  proyecto_id: string;
  items: RankingItem[];
};

// Bandera ética (Fase 8). Por ahora siempre "sin_analisis" (placeholder gris)
// hasta implementar el análisis ético de las Fases 2-3.
export type BanderaEtica = "verde" | "amarilla" | "roja" | "sin_analisis";

export type VisualizacionItem = RankingItem & {
  posicion: number;
  bandera: BanderaEtica;
};

export type VisualizacionOut = {
  proyecto_id: string;
  items: VisualizacionItem[];
};

// Helper generico: hace fetch y lanza un error legible si la respuesta falla.
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  if (!res.ok) {
    const detalle = await res.text();
    throw new Error(`Error ${res.status}: ${detalle}`);
  }
  return res.json() as Promise<T>;
}

// --- Proyectos ---

export const listarProyectos = () => request<Proyecto[]>("/proyectos");

export const crearProyecto = (data: { nombre: string; descripcion?: string }) =>
  request<Proyecto>("/proyectos", {
    method: "POST",
    body: JSON.stringify(data),
  });

// --- Requisitos (Fase 1) ---

export const listarRequisitos = (proyectoId: string) =>
  request<Requisito[]>(`/proyectos/${proyectoId}/requisitos`);

export const crearRequisito = (proyectoId: string, data: RequisitoInput) =>
  request<Requisito>(`/proyectos/${proyectoId}/requisitos`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const editarRequisito = (requisitoId: string, data: RequisitoInput) =>
  request<Requisito>(`/requisitos/${requisitoId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

// --- Dimensiones (Fase 4) ---

export const listarDimensiones = (proyectoId: string) =>
  request<Dimension[]>(`/proyectos/${proyectoId}/dimensiones`);

export const crearDimension = (proyectoId: string, data: DimensionInput) =>
  request<Dimension>(`/proyectos/${proyectoId}/dimensiones`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const editarDimension = (
  dimensionId: string,
  data: Partial<DimensionInput>,
) =>
  request<Dimension>(`/dimensiones/${dimensionId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const eliminarDimension = (dimensionId: string) =>
  fetch(`${API_URL}/dimensiones/${dimensionId}`, { method: "DELETE" }).then(
    (res) => {
      if (!res.ok) throw new Error(`Error ${res.status}`);
    },
  );

// --- Evaluaciones (Fase 5) ---

export const listarEvaluaciones = (proyectoId: string) =>
  request<Evaluacion[]>(`/proyectos/${proyectoId}/evaluaciones`);

export const guardarEvaluacion = (
  proyectoId: string,
  data: {
    requisito_id: string;
    dimension_id: string;
    fuerza: number;
    justificacion?: string;
  },
) =>
  request<Evaluacion>(`/proyectos/${proyectoId}/evaluaciones`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

// --- Ranking (Fase 6) ---

export const obtenerRanking = (proyectoId: string) =>
  request<RankingOut>(`/proyectos/${proyectoId}/ranking`);

export const guardarSnapshot = (proyectoId: string) =>
  request<unknown>(`/proyectos/${proyectoId}/ranking/snapshot`, {
    method: "POST",
  });

// --- Visualización (Fase 8) ---

export const obtenerVisualizacion = (proyectoId: string) =>
  request<VisualizacionOut>(`/proyectos/${proyectoId}/visualizacion`);

// URL directa de descarga del CSV (se usa en un enlace <a>).
export const urlExportCsv = (proyectoId: string) =>
  `${API_URL}/proyectos/${proyectoId}/visualizacion/export.csv`;

// --- Documentos normativos y normas activas (M4/M5) ---

export type Documento = {
  id: string;
  nombre: string;
  jurisdiccion?: string | null;
  version?: string | null;
  fuente_url?: string | null;
};

export const listarDocumentos = () => request<Documento[]>("/documentos");

export const crearDocumento = (data: {
  nombre: string;
  jurisdiccion?: string;
}) =>
  request<Documento>("/documentos", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const listarNormasActivas = (proyectoId: string) =>
  request<Documento[]>(`/proyectos/${proyectoId}/normas-activas`);

export const configurarNormasActivas = (
  proyectoId: string,
  documentoIds: string[],
) =>
  request<Documento[]>(`/proyectos/${proyectoId}/normas-activas`, {
    method: "PUT",
    body: JSON.stringify({ documento_ids: documentoIds }),
  });

// --- Fases 2-3: análisis ético y tratamiento (M5) ---

export type Cita = { chunk_id?: string | null; texto_citado?: string | null };

export type Tema = {
  id?: string;
  tema_etico: string;
  actor_afectado?: string | null;
  tipo_dano?: string | null;
  norma_tensionada_texto?: string | null;
  evidencia?: string | null;
  citas: Cita[];
};

// Capas 2 y 3 se guardan como JSON; las tipamos de forma laxa para mostrarlas.
export type Capas23 = {
  capa_2_analisis?: {
    mapa_stakeholders?: { stakeholder: string; interes?: string; impacto?: string }[];
    tensiones_de_valores?: { valor_a: string; valor_b: string; descripcion?: string }[];
  };
  capa_3_deliberacion?: {
    opciones_tratamiento?: { decision: string; justificacion?: string; pros?: string; contras?: string }[];
    reformulaciones_propuestas?: { texto_propuesto: string; como_reduce_conflicto?: string }[];
    requisitos_derivados_propuestos?: { nombre: string; descripcion?: string; obligatorio?: boolean }[];
    preguntas_deliberativas?: string[];
  };
};

export type Analisis = {
  id: string;
  requisito_id: string;
  generado_por?: string | null;
  modelo_usado?: string | null;
  nivel_confianza?: string | null;
  limitaciones?: string | null;
  capas_2_3?: Capas23 | null;
  creado_en?: string | null;
  temas: Tema[];
};

export type Decision = "aceptar" | "reformular" | "mitigar" | "eliminar";

export const analizarRequisito = (requisitoId: string) =>
  request<Analisis>(`/requisitos/${requisitoId}/analizar`, { method: "POST" });

// GET del análisis: devuelve null si el requisito aún no tiene análisis (404).
export const obtenerAnalisis = async (
  requisitoId: string,
): Promise<Analisis | null> => {
  const res = await fetch(`${API_URL}/requisitos/${requisitoId}/analisis`, {
    cache: "no-store",
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Error ${res.status}: ${await res.text()}`);
  return res.json();
};

export const editarAnalisis = (
  requisitoId: string,
  data: {
    nivel_confianza?: string;
    limitaciones?: string;
    capas_2_3?: Capas23;
    temas?: Tema[];
  },
) =>
  request<Analisis>(`/requisitos/${requisitoId}/analisis`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const crearTratamiento = (
  requisitoId: string,
  data: {
    decision: Decision;
    justificacion?: string;
    responsable?: string;
    nuevo_nombre?: string;
    nueva_descripcion?: string;
    derivados?: { nombre: string; descripcion?: string; obligatorio?: boolean }[];
  },
) =>
  request<{
    id: string;
    decision: string;
    nuevo_requisito_id?: string | null;
    derivados_ids: string[];
  }>(`/requisitos/${requisitoId}/tratamiento`, {
    method: "POST",
    body: JSON.stringify(data),
  });

// --- Fase 7: trazabilidad de derivados (M6) ---

export type TrazabilidadItem = {
  relacion_id: string;
  tipo_relacion?: string | null;
  obligatorio?: boolean | null;
  origen_codigo?: string | null;
  origen_nombre: string;
  origen_puntaje?: number | null;
  origen_posicion?: number | null;
  derivado_codigo?: string | null;
  derivado_nombre: string;
  derivado_puntaje?: number | null;
  derivado_posicion?: number | null;
  arrastre_violada: boolean;
};

export const listarTrazabilidad = (proyectoId: string) =>
  request<{ proyecto_id: string; items: TrazabilidadItem[] }>(
    `/proyectos/${proyectoId}/trazabilidad`,
  );

export const editarRelacion = (
  relacionId: string,
  data: { obligatorio?: boolean; tipo_relacion?: string },
) =>
  request<unknown>(`/relaciones/${relacionId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const eliminarRelacion = (relacionId: string) =>
  fetch(`${API_URL}/relaciones/${relacionId}`, { method: "DELETE" }).then((res) => {
    if (!res.ok) throw new Error(`Error ${res.status}`);
  });

// URL de descarga del export JSON del proyecto completo.
export const urlExportProyecto = (proyectoId: string) =>
  `${API_URL}/proyectos/${proyectoId}/export.json`;
