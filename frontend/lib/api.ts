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
