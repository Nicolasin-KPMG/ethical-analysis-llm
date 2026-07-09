"use client";

// Fase 5 — Matriz requisitos × dimensiones. La intensidad se elige de forma
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
      setRequisitos(reqs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado"));
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

  return (
    <>
      <PageHeader
        eyebrow="Fase 5"
        title="Evaluación"
        subtitle="Para cada requisito, indica con qué intensidad expresa cada dimensión: de “No aplica” a “Muy alta”. Las dimensiones éticas solo aplican a su requisito; en los demás la celda queda en “No aplica”. Se guarda al elegir."
      />

      {error && <Alert>{error}</Alert>}

      {requisitos.length === 0 || dimensiones.length === 0 ? (
        <EmptyState>
          Necesitas al menos un requisito (Fase 1) y una dimensión (Fase 4) para construir la matriz.
        </EmptyState>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50/70 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">Requisito</th>
                  {dimensiones.map((d) => (
                    <th key={d.id} className="px-3 py-3 text-center font-semibold">
                      <div className="text-slate-700">{d.nombre}</div>
                      <div className="font-normal normal-case text-slate-400">{d.tipo.replace(/_/g, " ")}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {requisitos.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/60">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-800">{r.nombre}</div>
                      <div className="font-mono text-xs text-slate-400">{r.codigo}</div>
                    </td>
                    {dimensiones.map((d) => {
                      const key = celda(r.id, d.id);
                      // La dimensión no aplica a este requisito: celda fija en "No aplica".
                      const noAplica = d.restringida && !(d.requisitos_aplica ?? []).includes(r.id);
                      if (noAplica) {
                        return (
                          <td key={d.id} className="px-3 py-2 text-center">
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
                        <td key={d.id} className="px-3 py-2 text-center">
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
