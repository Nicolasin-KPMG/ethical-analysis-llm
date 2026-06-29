"use client";

// Fase 8 — Visualización del ranking (auditable) + bandera ética + export CSV.

import { useEffect, useState } from "react";
import { VisualizacionItem, BanderaEtica, obtenerVisualizacion, urlExportCsv } from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import { PageHeader, Table, Dot, EmptyState, Alert, Card, th, td, btnDark } from "../../components/ui";

const BANDERAS: Record<BanderaEtica, { tone: "green" | "amber" | "red" | "slate"; titulo: string }> = {
  verde: { tone: "green", titulo: "Sin tensiones éticas relevantes" },
  amarilla: { tone: "amber", titulo: "Tensiones éticas a revisar" },
  roja: { tone: "red", titulo: "Tensiones éticas graves" },
  sin_analisis: { tone: "slate", titulo: "Sin análisis ético aún" },
};

export default function Page() {
  const { proyectoId } = useProyecto();
  const [items, setItems] = useState<VisualizacionItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) return setItems([]);
    obtenerVisualizacion(proyectoId).then((d) => setItems(d.items)).catch((e) => setError(e.message));
  }, [proyectoId]);

  if (!proyectoId) return <EmptyState>Selecciona o crea un proyecto arriba.</EmptyState>;

  return (
    <>
      <PageHeader
        eyebrow="Fase 8"
        title="Visualización del ranking"
        subtitle="Ranking ordenado y auditable, con desglose por requisito. La bandera ética informa, no bloquea."
        actions={
          items.length > 0 && (
            <a href={urlExportCsv(proyectoId)} className={btnDark}>Exportar CSV</a>
          )
        }
      />

      {error && <Alert>{error}</Alert>}

      <Card className="mb-6">
        <div className="flex items-center gap-3 px-5 py-3 text-sm text-slate-600">
          <Dot tone="slate" />
          La bandera ética está en gris (“sin análisis ético aún”). Se activará al conectar las Fases 2-3.
        </div>
      </Card>

      {items.length === 0 ? (
        <EmptyState>No hay requisitos rankeables todavía.</EmptyState>
      ) : (
        <Table
          head={
            <tr>
              <th className={`${th} w-10`}>#</th>
              <th className={`${th} text-center`}>Ética</th>
              <th className={th}>Requisito</th>
              <th className={`${th} text-right`}>Beneficio</th>
              <th className={`${th} text-right`}>Valor ético</th>
              <th className={`${th} text-right`}>Costo</th>
              <th className={`${th} text-right`}>Riesgo res.</th>
              <th className={`${th} text-right`}>Puntaje</th>
            </tr>
          }
        >
          {items.map((it) => {
            const b = BANDERAS[it.bandera];
            return (
              <tr key={it.requisito_id} className="hover:bg-slate-50/60">
                <td className={`${td} text-slate-400`}>{it.posicion}</td>
                <td className={`${td} text-center`}>
                  <span title={b.titulo}><Dot tone={b.tone} /></span>
                </td>
                <td className={td}>
                  <div className="font-medium text-slate-800">{it.nombre}</div>
                  <div className="font-mono text-xs text-slate-400">{it.codigo}</div>
                </td>
                <td className={`${td} text-right tabular-nums text-emerald-600`}>{it.desglose.beneficio}</td>
                <td className={`${td} text-right tabular-nums text-emerald-600`}>{it.desglose.valor_etico}</td>
                <td className={`${td} text-right tabular-nums text-red-500`}>−{it.desglose.costo}</td>
                <td className={`${td} text-right tabular-nums text-red-500`}>−{it.desglose.riesgo_etico_residual}</td>
                <td className={`${td} text-right text-lg font-bold tabular-nums text-slate-900`}>{it.puntaje_final}</td>
              </tr>
            );
          })}
        </Table>
      )}
    </>
  );
}
