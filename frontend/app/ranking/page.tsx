"use client";

// Fase 6 — Ranking (cálculo en vivo, determinista, sin IA).

import { useEffect, useState } from "react";
import { RankingItem, obtenerRanking, guardarSnapshot } from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import {
  PageHeader,
  Table,
  EmptyState,
  Alert,
  th,
  td,
  btnGhost,
  btnDark,
} from "../../components/ui";

export default function Page() {
  const { proyectoId } = useProyecto();
  const [items, setItems] = useState<RankingItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) return setItems([]);
    cargar();
  }, [proyectoId]);

  function cargar() {
    setMensaje(null);
    obtenerRanking(proyectoId).then((r) => setItems(r.items)).catch((e) => setError(e.message));
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

  if (!proyectoId) return <EmptyState>Selecciona o crea un proyecto arriba.</EmptyState>;

  const maxAbs = Math.max(1, ...items.map((i) => Math.abs(i.puntaje_final)));

  return (
    <>
      <PageHeader
        eyebrow="Fase 6"
        title="Ranking"
        subtitle="Puntaje = beneficio + valor ético − costo − riesgo ético residual. Cálculo en vivo, determinista, sin IA."
        actions={
          <>
            <button onClick={cargar} className={btnGhost}>Recalcular</button>
            <button onClick={onSnapshot} className={btnDark}>Guardar snapshot</button>
          </>
        }
      />

      {error && <Alert>{error}</Alert>}
      {mensaje && <Alert tone="green">{mensaje}</Alert>}

      {items.length === 0 ? (
        <EmptyState>No hay requisitos rankeables (necesitas requisitos, dimensiones y evaluaciones).</EmptyState>
      ) : (
        <Table
          head={
            <tr>
              <th className={`${th} w-10`}>#</th>
              <th className={th}>Requisito</th>
              <th className={`${th} text-right`}>Beneficio</th>
              <th className={`${th} text-right`}>Valor ético</th>
              <th className={`${th} text-right`}>Costo</th>
              <th className={`${th} text-right`}>Riesgo res.</th>
              <th className={`${th} text-right`}>Puntaje</th>
            </tr>
          }
        >
          {items.map((it, i) => (
            <tr key={it.requisito_id} className="hover:bg-slate-50/60">
              <td className={`${td} text-slate-400`}>{i + 1}</td>
              <td className={td}>
                <div className="font-medium text-slate-800">{it.nombre}</div>
                <div className="font-mono text-xs text-slate-400">{it.codigo}</div>
              </td>
              <td className={`${td} text-right tabular-nums text-emerald-600`}>{it.desglose.beneficio}</td>
              <td className={`${td} text-right tabular-nums text-emerald-600`}>{it.desglose.valor_etico}</td>
              <td className={`${td} text-right tabular-nums text-red-500`}>−{it.desglose.costo}</td>
              <td className={`${td} text-right tabular-nums text-red-500`}>−{it.desglose.riesgo_etico_residual}</td>
              <td className={`${td} text-right`}>
                <div className="flex items-center justify-end gap-2">
                  <div className="hidden h-1.5 w-24 overflow-hidden rounded-full bg-slate-100 sm:block">
                    <div
                      className={"h-full rounded-full " + (it.puntaje_final >= 0 ? "bg-accent-500" : "bg-red-400")}
                      style={{ width: `${(Math.abs(it.puntaje_final) / maxAbs) * 100}%` }}
                    />
                  </div>
                  <span className="w-10 text-lg font-bold tabular-nums text-slate-900">
                    {it.puntaje_final}
                  </span>
                </div>
              </td>
            </tr>
          ))}
        </Table>
      )}
    </>
  );
}
