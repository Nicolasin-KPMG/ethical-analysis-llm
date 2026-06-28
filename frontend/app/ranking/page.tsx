"use client";

// Fase 6 — Ranking (cálculo en vivo, determinista, sin IA).
// Muestra el puntaje final de cada requisito vigente y su desglose por
// categoría. Permite guardar una foto (snapshot) del ranking.

import { useEffect, useState } from "react";
import {
  RankingItem,
  obtenerRanking,
  guardarSnapshot,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";

export default function Page() {
  const { proyectoId } = useProyecto();
  const [items, setItems] = useState<RankingItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) {
      setItems([]);
      return;
    }
    cargar();
  }, [proyectoId]);

  function cargar() {
    setMensaje(null);
    obtenerRanking(proyectoId)
      .then((r) => setItems(r.items))
      .catch((e) => setError(e.message));
  }

  async function onSnapshot() {
    setError(null);
    try {
      await guardarSnapshot(proyectoId);
      setMensaje("Snapshot del ranking guardado.");
    } catch (e: any) {
      setError(e.message);
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
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Fase 6 — Ranking</h1>
          <p className="text-sm text-gray-600">
            Puntaje = beneficio + valor ético − costo − riesgo ético residual.
            Cálculo en vivo desde la matriz de la Fase 5.
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            onClick={cargar}
            className="rounded border px-3 py-2 text-sm hover:bg-gray-100"
          >
            Recalcular
          </button>
          <button
            onClick={onSnapshot}
            className="rounded bg-gray-800 px-3 py-2 text-sm text-white hover:bg-gray-700"
          >
            Guardar snapshot
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {mensaje && (
        <div className="mb-4 rounded border border-green-300 bg-green-50 p-3 text-sm text-green-700">
          {mensaje}
        </div>
      )}

      {items.length === 0 ? (
        <p className="rounded border bg-white p-4 text-sm text-gray-500">
          No hay requisitos rankeables todavía (necesitas requisitos, dimensiones
          y evaluaciones).
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-gray-50 text-gray-600">
              <tr>
                <th className="p-3">#</th>
                <th className="p-3">Requisito</th>
                <th className="p-3 text-right text-green-700">Beneficio</th>
                <th className="p-3 text-right text-green-700">Valor ético</th>
                <th className="p-3 text-right text-red-700">Costo</th>
                <th className="p-3 text-right text-red-700">Riesgo resid.</th>
                <th className="p-3 text-right">Puntaje final</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => (
                <tr key={it.requisito_id} className="border-b last:border-0">
                  <td className="p-3 text-gray-400">{i + 1}</td>
                  <td className="p-3">
                    <div className="font-medium">{it.nombre}</div>
                    <div className="text-xs text-gray-400">{it.codigo}</div>
                  </td>
                  <td className="p-3 text-right">{it.desglose.beneficio}</td>
                  <td className="p-3 text-right">{it.desglose.valor_etico}</td>
                  <td className="p-3 text-right">−{it.desglose.costo}</td>
                  <td className="p-3 text-right">
                    −{it.desglose.riesgo_etico_residual}
                  </td>
                  <td className="p-3 text-right text-lg font-bold">
                    {it.puntaje_final}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
