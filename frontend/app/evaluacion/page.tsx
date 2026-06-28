"use client";

// Fase 5 — Relación entre requisitos y dimensiones (matriz de evaluación).
// Filas: requisitos vigentes (no eliminados). Columnas: dimensiones.
// Cada celda es una fuerza de 0 a 5 (0 = no aplica) que se guarda al salir
// del campo (onBlur).

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

// Clave de una celda de la matriz.
const celda = (rid: string, did: string) => `${rid}::${did}`;

export default function Page() {
  const { proyectoId } = useProyecto();
  const [requisitos, setRequisitos] = useState<Requisito[]>([]);
  const [dimensiones, setDimensiones] = useState<Dimension[]>([]);
  // Mapa celda -> fuerza (como string para el input controlado).
  const [valores, setValores] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) {
      setRequisitos([]);
      setDimensiones([]);
      setValores({});
      return;
    }
    cargar();
  }, [proyectoId]);

  async function cargar() {
    try {
      const [reqs, dims, evals] = await Promise.all([
        listarRequisitos(proyectoId),
        listarDimensiones(proyectoId),
        listarEvaluaciones(proyectoId),
      ]);
      // Solo requisitos vigentes y no eliminados entran a la matriz (reglas 2 y 5).
      setRequisitos(
        reqs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado"),
      );
      setDimensiones(dims);
      const mapa: Record<string, string> = {};
      evals.forEach((e: Evaluacion) => {
        mapa[celda(e.requisito_id, e.dimension_id)] = String(e.fuerza);
      });
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
      await guardarEvaluacion(proyectoId, {
        requisito_id: rid,
        dimension_id: did,
        fuerza,
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGuardando(null);
    }
  }

  if (!proyectoId) {
    return (
      <main className="mx-auto max-w-5xl p-6">
        <p className="text-sm text-gray-500">
          Selecciona o crea un proyecto en la barra superior.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Fase 5 — Evaluación</h1>
        <p className="text-sm text-gray-600">
          Asigna a cada requisito una fuerza de asociación de 0 a 5 (0 = no
          aplica) frente a cada dimensión. Se guarda automáticamente al salir de
          la celda.
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {requisitos.length === 0 || dimensiones.length === 0 ? (
        <p className="rounded border bg-white p-4 text-sm text-gray-500">
          Necesitas al menos un requisito (Fase 1) y una dimensión (Fase 4) para
          construir la matriz.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-gray-50 text-gray-600">
              <tr>
                <th className="p-3">Requisito</th>
                {dimensiones.map((d) => (
                  <th key={d.id} className="p-3 text-center">
                    {d.nombre}
                    <div className="text-xs font-normal text-gray-400">
                      {d.tipo}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {requisitos.map((r) => (
                <tr key={r.id} className="border-b last:border-0">
                  <td className="p-3">
                    <div className="font-medium">{r.nombre}</div>
                    <div className="text-xs text-gray-400">{r.codigo}</div>
                  </td>
                  {dimensiones.map((d) => {
                    const key = celda(r.id, d.id);
                    return (
                      <td key={d.id} className="p-2 text-center">
                        <input
                          type="number"
                          min={0}
                          max={5}
                          className="w-16 rounded border px-2 py-1 text-center"
                          value={valores[key] ?? ""}
                          onChange={(e) =>
                            setValores({ ...valores, [key]: e.target.value })
                          }
                          onBlur={(e) =>
                            onGuardarCelda(r.id, d.id, e.target.value)
                          }
                        />
                        {guardando === key && (
                          <div className="text-xs text-gray-400">…</div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
