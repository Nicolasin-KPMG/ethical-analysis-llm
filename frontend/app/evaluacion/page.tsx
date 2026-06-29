"use client";

// Fase 5 — Matriz requisitos × dimensiones (fuerza 0–5, 0 = no aplica).

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
        subtitle="Asigna a cada requisito una fuerza de 0 a 5 (0 = no aplica) frente a cada dimensión. Se guarda al salir de la celda."
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
                      return (
                        <td key={d.id} className="px-3 py-2 text-center">
                          <input
                            type="number"
                            min={0}
                            max={5}
                            className="field-sm w-16 text-center"
                            value={valores[key] ?? ""}
                            onChange={(e) => setValores({ ...valores, [key]: e.target.value })}
                            onBlur={(e) => onGuardarCelda(r.id, d.id, e.target.value)}
                          />
                          {guardando === key && <div className="text-xs text-slate-400">…</div>}
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
