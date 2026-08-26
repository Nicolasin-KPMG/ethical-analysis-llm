"use client";

// Fase 4 — Matriz requisitos × dimensiones. La intensidad se elige de forma
// CUALITATIVA (palabras), pero se guarda como número 0–5 (0 = no aplica) para
// que la fórmula del ranking no cambie.

import { useEffect, useState } from "react";
import {
  Requisito,
  Dimension,
  Evaluacion,
  listarRequisitos,
  listarDimensiones,
  listarEvaluaciones,
  guardarEvaluacion,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import { Card, PageHeader, EmptyState, Alert } from "../../components/ui";

const celda = (rid: string, did: string) => `${rid}::${did}`;

// Orden y estilo de los grupos de columnas por tipo de dimensión.
const TIPO_META: Record<string, { label: string; orden: number; head: string }> = {
  beneficio: { label: "Beneficio", orden: 0, head: "bg-emerald-50 text-emerald-700" },
  costo: { label: "Costo", orden: 1, head: "bg-rose-50 text-rose-700" },
  valor_etico: { label: "Valor ético", orden: 2, head: "bg-teal-50 text-teal-700" },
  riesgo_etico: { label: "Riesgo ético", orden: 3, head: "bg-red-50 text-red-700" },
};
const tipoOrden = (t: string) => TIPO_META[t]?.orden ?? 99;

// Escala cualitativa de la fuerza (0–5). El usuario elige con palabras.
const ESCALA_FUERZA: { valor: number; label: string }[] = [
  { valor: 0, label: "No aplica" },
  { valor: 1, label: "Muy baja" },
  { valor: 2, label: "Baja" },
  { valor: 3, label: "Media" },
  { valor: 4, label: "Alta" },
  { valor: 5, label: "Muy alta" },
];

export default function Page() {
  const { proyectoId } = useProyecto();
  const [requisitos, setRequisitos] = useState<Requisito[]>([]);
  const [dimensiones, setDimensiones] = useState<Dimension[]>([]);
  const [valores, setValores] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) return;
    cargar();
  }, [proyectoId]);

  async function cargar() {
    try {
      const [reqs, dims, evals] = await Promise.all([
        listarRequisitos(proyectoId),
        listarDimensiones(proyectoId),
        listarEvaluaciones(proyectoId),
      ]);
      // Los derivados de mitigación (origen_requisito_id) no se evalúan: entran
      // al ranking como bloque bajo su padre.
      setRequisitos(
        reqs.filter(
          (r) => r.es_vigente !== false && r.estado !== "eliminado" && !r.origen_requisito_id,
        ),
      );
      setDimensiones(dims);
      const mapa: Record<string, string> = {};
      evals.forEach((e: Evaluacion) => (mapa[celda(e.requisito_id, e.dimension_id)] = String(e.fuerza)));
      setValores(mapa);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function onGuardarCelda(rid: string, did: string, valor: string) {
    const fuerza = Number(valor);
    if (valor === "" || Number.isNaN(fuerza) || fuerza < 0 || fuerza > 5) {
      setError("La fuerza debe estar entre 0 y 5.");
      return;
    }
    setError(null);
    setGuardando(celda(rid, did));
    try {
      await guardarEvaluacion(proyectoId, { requisito_id: rid, dimension_id: did, fuerza });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGuardando(null);
    }
  }

  if (!proyectoId)
    return <EmptyState>Selecciona o crea un proyecto arriba.</EmptyState>;

  // Columnas ordenadas por tipo (beneficio, costo, valor ético, riesgo ético) y
  // agrupadas en bloques consecutivos para el encabezado de grupo.
  const dimsOrdenadas = [...dimensiones].sort(
    (a, b) => tipoOrden(a.tipo) - tipoOrden(b.tipo) || a.nombre.localeCompare(b.nombre),
  );
  const grupos: { tipo: string; dims: Dimension[] }[] = [];
  for (const d of dimsOrdenadas) {
    const ult = grupos[grupos.length - 1];
    if (ult && ult.tipo === d.tipo) ult.dims.push(d);
    else grupos.push({ tipo: d.tipo, dims: [d] });
  }
  const inicioGrupo = new Set(grupos.map((g) => g.dims[0].id));

  return (
    <>
      <PageHeader
        eyebrow="Fase 4"
        title="Evaluación"
        subtitle="Para cada requisito, indica con qué intensidad expresa cada dimensión: de “No aplica” a “Muy alta”. Las dimensiones éticas solo aplican a su requisito; en los demás la celda queda en “No aplica”. Se guarda al elegir."
      />

      {error && <Alert>{error}</Alert>}

      {requisitos.length === 0 || dimensiones.length === 0 ? (
        <EmptyState>
          Necesitas al menos un requisito (Entrada) y una dimensión (Fase 3) para construir la matriz.
        </EmptyState>
      ) : (
        <Card className="overflow-hidden">
          <p className="border-b border-slate-100 px-4 py-2 text-xs text-slate-400">
            Las columnas están agrupadas por tipo. Desliza horizontalmente para ver todas; la columna de requisitos queda fija.
          </p>
          <div className="overflow-x-auto">
            <table className="border-separate border-spacing-0 text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-500">
                {/* Fila de grupos por tipo. */}
                <tr>
                  <th
                    rowSpan={2}
                    className="sticky left-0 z-20 border-b border-slate-200 bg-slate-50 px-4 py-3 text-left font-semibold"
                  >
                    Requisito
                  </th>
                  {grupos.map((g) => (
                    <th
                      key={g.tipo}
                      colSpan={g.dims.length}
                      className={`border-b border-l border-slate-200 px-3 py-2 text-center font-semibold ${TIPO_META[g.tipo]?.head ?? "bg-slate-50 text-slate-600"}`}
                    >
                      {TIPO_META[g.tipo]?.label ?? g.tipo.replace(/_/g, " ")}
                    </th>
                  ))}
                </tr>
                {/* Fila de nombres de dimensión. */}
                <tr>
                  {dimsOrdenadas.map((d) => (
                    <th
                      key={d.id}
                      className={`min-w-[8rem] border-b border-slate-200 bg-slate-50/70 px-3 py-3 text-center font-semibold normal-case text-slate-700 ${inicioGrupo.has(d.id) ? "border-l border-slate-200" : ""}`}
                    >
                      {d.nombre}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {requisitos.map((r) => (
                  <tr key={r.id} className="group hover:bg-slate-50/60">
                    <td className="sticky left-0 z-10 border-b border-slate-100 bg-white px-4 py-3 group-hover:bg-slate-50">
                      <div className="font-medium text-slate-800">{r.nombre}</div>
                      <div className="font-mono text-xs text-slate-400">{r.codigo}</div>
                    </td>
                    {dimsOrdenadas.map((d) => {
                      const key = celda(r.id, d.id);
                      const bordeGrupo = inicioGrupo.has(d.id) ? "border-l border-slate-200" : "";
                      // La dimensión no aplica a este requisito: celda fija en "No aplica".
                      const noAplica = d.restringida && !(d.requisitos_aplica ?? []).includes(r.id);
                      if (noAplica) {
                        return (
                          <td key={d.id} className={`border-b border-slate-100 px-3 py-2 text-center ${bordeGrupo}`}>
                            <span
                              title="Esta dimensión no aplica a este requisito"
                              className="inline-block rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-400"
                            >
                              No aplica
                            </span>
                          </td>
                        );
                      }
                      return (
                        <td key={d.id} className={`border-b border-slate-100 px-3 py-2 text-center ${bordeGrupo}`}>
                          <select
                            className="field-sm w-28 text-center"
                            value={valores[key] ?? ""}
                            onChange={(e) => {
                              const v = e.target.value;
                              setValores({ ...valores, [key]: v });
                              if (v !== "") onGuardarCelda(r.id, d.id, v);
                            }}
                          >
                            <option value="" disabled>
                              Elegir…
                            </option>
                            {ESCALA_FUERZA.map((o) => (
                              <option key={o.valor} value={String(o.valor)}>
                                {o.label}
                              </option>
                            ))}
                          </select>
                          {guardando === key && <span className="ml-1 text-xs text-slate-400">…</span>}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  );
}
