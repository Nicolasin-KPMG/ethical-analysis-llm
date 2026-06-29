// Mapeos compartidos de estado/tipo de requisito a etiquetas y colores,
// para que el dashboard y las tablas se vean consistentes.

type Tone = "slate" | "blue" | "teal" | "amber" | "red" | "green" | "violet";
type DotTone = "slate" | "amber" | "red" | "green" | "ink";

export function estadoBadge(estado?: string | null): { label: string; tone: Tone } {
  switch (estado) {
    case "aceptado":
      return { label: "Aceptado", tone: "green" };
    case "mitigado":
      return { label: "Mitigado", tone: "amber" };
    case "reformulado":
      return { label: "Reformulado", tone: "violet" };
    case "eliminado":
      return { label: "Eliminado", tone: "slate" };
    default:
      return { label: "Pendiente", tone: "slate" };
  }
}

export function tipoBadge(tipo?: string | null): { label: string; tone: Tone } {
  switch (tipo) {
    case "funcional":
      return { label: "Funcional", tone: "blue" };
    case "no_funcional":
      return { label: "No funcional", tone: "violet" };
    case "restriccion":
      return { label: "Restricción", tone: "amber" };
    default:
      return { label: tipo || "—", tone: "slate" };
  }
}

// "Bandera" del dashboard derivada del estado (la ética fina llega con Fases 2-3).
export function banderaEstado(estado?: string | null): { label: string; tone: DotTone } {
  switch (estado) {
    case "eliminado":
      return { label: "Eliminado", tone: "ink" };
    case "mitigado":
    case "reformulado":
      return { label: "Tratado", tone: "amber" };
    case "aceptado":
      return { label: "Aceptado", tone: "green" };
    default:
      return { label: "Pendiente", tone: "slate" };
  }
}
