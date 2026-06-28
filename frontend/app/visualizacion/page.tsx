"use client";

// Fase 8 — Visualización del ranking.
// Ranking ordenado y auditable: posición, desglose por categoría, puntaje final
// y una bandera ética por requisito. Permite exportar a CSV.
//
// La bandera es por ahora un placeholder gris ("sin análisis ético aún"): el
// color verde/amarillo/rojo dependerá del análisis ético de las Fases 2-3, que
// todavía no está implementado.

import { useEffect, useState } from "react";
import {
  VisualizacionItem,
  BanderaEtica,
  obtenerVisualizacion,
  urlExportCsv,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";

// Estilo y etiqueta de cada bandera. El gris es el placeholder de M3.
const BANDERAS: Record<BanderaEtica, { color: string; titulo: string }> = {
  verde: { color: "bg-green-500", titulo: "Sin tensiones éticas relevantes" },
  amarilla: { color: "bg-amber-400", titulo: "Tensiones éticas a revisar" },
  roja: { color: "bg-red-500", titulo: "Tensiones éticas graves" },
  sin_analisis: { color: "bg-gray-300", titulo: "Sin análisis ético aún" },
};

export default function Page() {
  const { proyectoId } = useProyecto();
  const [items, setItems] = useState<VisualizacionItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) {
      setItems([]);
      return;
    }
    obtenerVisualizacion(proyectoId)
      .then((d) => setItems(d.items))
      .catch((e) => setError(e.message));
  }, [proyectoId]);

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
          <h1 className="text-2xl font-bold">Fase 8 — Visualización del ranking</h1>
          <p className="text-sm text-gray-600">
            Ranking ordenado y auditable, con el desglose por requisito. La
            bandera ética informa, no bloquea.
          </p>
        </div>
        {items.length > 0 && (
          <a
            href={urlExportCsv(proyectoId)}
            className="shrink-0 rounded bg-gray-800 px-3 py-2 text-sm text-white hover:bg-gray-700"
          >
            Exportar CSV
          </a>
        )}
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Aviso del placeholder de bandera mientras no exista el análisis ético. */}
      <div className="mb-4 rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600">
        <span className="mr-2 inline-block h-3 w-3 rounded-full bg-gray-300 align-middle" />
        La bandera ética está en gris (“sin análisis ético aún”). Se activará al
        implementar las Fases 2-3.
      </div>

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
                <th className="p-3">Ética</th>
                <th className="p-3">Requisito</th>
                <th className="p-3 text-right text-green-700">Beneficio</th>
                <th className="p-3 text-right text-green-700">Valor ético</th>
                <th className="p-3 text-right text-red-700">Costo</th>
                <th className="p-3 text-right text-red-700">Riesgo resid.</th>
                <th className="p-3 text-right">Puntaje final</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => {
                const b = BANDERAS[it.bandera];
                return (
                  <tr key={it.requisito_id} className="border-b last:border-0">
                    <td className="p-3 text-gray-400">{it.posicion}</td>
                    <td className="p-3">
                      <span
                        title={b.titulo}
                        className={
                          "inline-block h-3.5 w-3.5 rounded-full " + b.color
                        }
                      />
                    </td>
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
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
