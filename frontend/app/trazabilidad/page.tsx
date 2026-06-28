"use client";

// Fase 7 — Gestión de derivados y trazabilidad.
// Muestra las relaciones origen → derivado con su posición/puntaje en el ranking
// y la "regla de arrastre": marca en rojo cuando un derivado OBLIGATORIO queda
// por debajo del requisito que mitiga. Informa, no bloquea.
// Permite alternar "obligatorio", quitar la relación y exportar el proyecto.

import { useEffect, useState } from "react";
import {
  TrazabilidadItem,
  listarTrazabilidad,
  editarRelacion,
  eliminarRelacion,
  urlExportProyecto,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";

function celda(pos?: number | null, pts?: number | null) {
  if (pos == null) return "—";
  return `#${pos} (${pts})`;
}

export default function Page() {
  const { proyectoId } = useProyecto();
  const [items, setItems] = useState<TrazabilidadItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) {
      setItems([]);
      return;
    }
    cargar();
  }, [proyectoId]);

  function cargar() {
    listarTrazabilidad(proyectoId)
      .then((d) => setItems(d.items))
      .catch((e) => setError(e.message));
  }

  async function toggle(rel: TrazabilidadItem) {
    setError(null);
    try {
      await editarRelacion(rel.relacion_id, { obligatorio: !rel.obligatorio });
      cargar();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function quitar(rel: TrazabilidadItem) {
    if (!confirm("¿Quitar esta relación origen-derivado?")) return;
    try {
      await eliminarRelacion(rel.relacion_id);
      cargar();
    } catch (e: any) {
      setError(e.message);
    }
  }

  if (!proyectoId) {
    return (
      <main className="mx-auto max-w-5xl p-6">
        <p className="text-sm text-gray-500">Selecciona o crea un proyecto en la barra superior.</p>
      </main>
    );
  }

  const violadas = items.filter((i) => i.arrastre_violada).length;

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Fase 7 — Derivados y trazabilidad</h1>
          <p className="text-sm text-gray-600">
            Relaciones origen → derivado. Regla de arrastre: un derivado{" "}
            <b>obligatorio</b> no debería quedar por debajo del requisito que mitiga.
          </p>
        </div>
        <a
          href={urlExportProyecto(proyectoId)}
          className="shrink-0 rounded bg-gray-800 px-3 py-2 text-sm text-white hover:bg-gray-700"
        >
          Exportar proyecto (JSON)
        </a>
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {violadas > 0 && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          ⚠ {violadas} relación(es) violan la regla de arrastre: hay derivados obligatorios
          por debajo de su requisito de origen en el ranking.
        </div>
      )}

      {items.length === 0 ? (
        <p className="rounded border bg-white p-4 text-sm text-gray-500">
          No hay relaciones de derivación. Se crean al “mitigar” un requisito en la Fase 3.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-gray-50 text-gray-600">
              <tr>
                <th className="p-3">Origen (posición/puntaje)</th>
                <th className="p-3">Derivado (posición/puntaje)</th>
                <th className="p-3 text-center">Obligatorio</th>
                <th className="p-3 text-center">Arrastre</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr
                  key={it.relacion_id}
                  className={"border-b last:border-0 " + (it.arrastre_violada ? "bg-red-50" : "")}
                >
                  <td className="p-3">
                    <div className="font-medium">{it.origen_nombre}</div>
                    <div className="text-xs text-gray-400">
                      {it.origen_codigo} · {celda(it.origen_posicion, it.origen_puntaje)}
                    </div>
                  </td>
                  <td className="p-3">
                    <div className="font-medium">{it.derivado_nombre}</div>
                    <div className="text-xs text-gray-400">
                      {it.derivado_codigo} · {celda(it.derivado_posicion, it.derivado_puntaje)}
                    </div>
                  </td>
                  <td className="p-3 text-center">
                    <button
                      onClick={() => toggle(it)}
                      className={
                        "rounded px-2 py-0.5 text-xs " +
                        (it.obligatorio ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-600")
                      }
                    >
                      {it.obligatorio ? "obligatorio" : "opcional"}
                    </button>
                  </td>
                  <td className="p-3 text-center">
                    {it.arrastre_violada ? (
                      <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-800">violada</span>
                    ) : (
                      <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-800">ok</span>
                    )}
                  </td>
                  <td className="p-3">
                    <button onClick={() => quitar(it)} className="text-red-600 hover:underline">
                      Quitar
                    </button>
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
