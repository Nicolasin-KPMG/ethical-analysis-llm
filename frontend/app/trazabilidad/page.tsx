"use client";

// Fase 7 — Derivados y trazabilidad (regla de arrastre).

import { useEffect, useState } from "react";
import {
  TrazabilidadItem,
  listarTrazabilidad,
  editarRelacion,
  eliminarRelacion,
  urlExportProyecto,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import {
  PageHeader,
  Table,
  Badge,
  EmptyState,
  Alert,
  th,
  td,
  btnDark,
} from "../../components/ui";

const cel = (pos?: number | null, pts?: number | null) =>
  pos == null ? "—" : `#${pos} (${pts})`;

export default function Page() {
  const { proyectoId } = useProyecto();
  const [items, setItems] = useState<TrazabilidadItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) return setItems([]);
    cargar();
  }, [proyectoId]);

  function cargar() {
    listarTrazabilidad(proyectoId).then((d) => setItems(d.items)).catch((e) => setError(e.message));
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

  if (!proyectoId) return <EmptyState>Selecciona o crea un proyecto arriba.</EmptyState>;
  const violadas = items.filter((i) => i.arrastre_violada).length;

  return (
    <>
      <PageHeader
        eyebrow="Fase 7"
        title="Derivados y trazabilidad"
        subtitle="Relaciones origen → derivado. Regla de arrastre: un derivado obligatorio no debería quedar por debajo del requisito que mitiga."
        actions={
          <a href={urlExportProyecto(proyectoId)} className={btnDark}>
            Exportar proyecto (JSON)
          </a>
        }
      />

      {error && <Alert>{error}</Alert>}
      {violadas > 0 && (
        <Alert tone="amber">
          ⚠ {violadas} relación(es) violan la regla de arrastre: hay derivados obligatorios por debajo
          de su requisito de origen en el ranking.
        </Alert>
      )}

      {items.length === 0 ? (
        <EmptyState>No hay relaciones de derivación. Se crean al “mitigar” un requisito en la Fase 3.</EmptyState>
      ) : (
        <Table
          head={
            <tr>
              <th className={th}>Origen (posición/puntaje)</th>
              <th className={th}>Derivado (posición/puntaje)</th>
              <th className={`${th} text-center`}>Obligatorio</th>
              <th className={`${th} text-center`}>Arrastre</th>
              <th className={th}></th>
            </tr>
          }
        >
          {items.map((it) => (
            <tr key={it.relacion_id} className={it.arrastre_violada ? "bg-red-50/50" : "hover:bg-slate-50/60"}>
              <td className={td}>
                <div className="font-medium text-slate-800">{it.origen_nombre}</div>
                <div className="text-xs text-slate-400">{it.origen_codigo} · {cel(it.origen_posicion, it.origen_puntaje)}</div>
              </td>
              <td className={td}>
                <div className="font-medium text-slate-800">{it.derivado_nombre}</div>
                <div className="text-xs text-slate-400">{it.derivado_codigo} · {cel(it.derivado_posicion, it.derivado_puntaje)}</div>
              </td>
              <td className={`${td} text-center`}>
                <button onClick={() => toggle(it)}>
                  <Badge tone={it.obligatorio ? "blue" : "slate"}>
                    {it.obligatorio ? "obligatorio" : "opcional"}
                  </Badge>
                </button>
              </td>
              <td className={`${td} text-center`}>
                <Badge tone={it.arrastre_violada ? "red" : "green"}>
                  {it.arrastre_violada ? "violada" : "ok"}
                </Badge>
              </td>
              <td className={`${td} text-right`}>
                <button onClick={() => quitar(it)} className="text-sm font-medium text-red-500 hover:text-red-600">
                  Quitar
                </button>
              </td>
            </tr>
          ))}
        </Table>
      )}
    </>
  );
}
