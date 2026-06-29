"use client";

// Fase 4 — Definición dinámica de dimensiones de priorización.

import { useEffect, useState } from "react";
import {
  Dimension,
  DimensionInput,
  TipoDimension,
  listarDimensiones,
  crearDimension,
  editarDimension,
  eliminarDimension,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import {
  Card,
  CardBody,
  PageHeader,
  Table,
  Badge,
  EmptyState,
  Alert,
  th,
  td,
  btnPrimary,
  btnGhost,
  labelCls,
} from "../../components/ui";

const TIPOS: { value: TipoDimension; label: string; suma: boolean }[] = [
  { value: "beneficio", label: "Beneficio", suma: true },
  { value: "valor_etico", label: "Valor ético", suma: true },
  { value: "costo", label: "Costo", suma: false },
  { value: "riesgo_etico_residual", label: "Riesgo ético residual", suma: false },
];
const suma = (t: string) => TIPOS.find((x) => x.value === t)?.suma ?? true;

const VACIO: DimensionInput = {
  nombre: "",
  tipo: "beneficio",
  descripcion: "",
  peso: 3,
  justificacion_peso: "",
};

export default function Page() {
  const { proyectoId } = useProyecto();
  const [dims, setDims] = useState<Dimension[]>([]);
  const [form, setForm] = useState<DimensionInput>(VACIO);
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) return setDims([]);
    cargar();
  }, [proyectoId]);

  function cargar() {
    listarDimensiones(proyectoId).then(setDims).catch((e) => setError(e.message));
  }
  function reset() {
    setForm(VACIO);
    setEditandoId(null);
  }
  function onEditar(d: Dimension) {
    setEditandoId(d.id);
    setForm({
      nombre: d.nombre,
      tipo: d.tipo,
      descripcion: d.descripcion ?? "",
      peso: d.peso ?? 3,
      justificacion_peso: d.justificacion_peso ?? "",
    });
  }
  async function onGuardar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!proyectoId) return setError("Selecciona o crea un proyecto arriba.");
    try {
      if (editandoId) await editarDimension(editandoId, form);
      else await crearDimension(proyectoId, form);
      reset();
      cargar();
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function onEliminar(id: string) {
    if (!confirm("¿Eliminar esta dimensión? Se borrarán sus evaluaciones.")) return;
    try {
      await eliminarDimension(id);
      cargar();
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Fase 4"
        title="Dimensiones de priorización"
        subtitle="Define los criterios. Beneficio y valor ético suman; costo y riesgo ético residual restan en el ranking."
      />

      {error && <Alert>{error}</Alert>}

      <Card className="mb-6">
        <CardBody>
          <h2 className="mb-4 text-sm font-semibold text-slate-700">
            {editandoId ? "Editar dimensión" : "Nueva dimensión"}
          </h2>
          <form onSubmit={onGuardar} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={labelCls}>Nombre *</label>
              <input
                required
                className="field mt-1"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </div>
            <div>
              <label className={labelCls}>Tipo</label>
              <select
                className="field mt-1"
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value as TipoDimension })}
              >
                {TIPOS.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label} ({t.suma ? "+" : "−"})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>Peso (1 a 5)</label>
              <input
                type="number"
                min={1}
                max={5}
                required
                className="field mt-1"
                value={form.peso}
                onChange={(e) => setForm({ ...form, peso: Number(e.target.value) })}
              />
            </div>
            <div>
              <label className={labelCls}>Descripción</label>
              <input
                className="field mt-1"
                value={form.descripcion}
                onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <label className={labelCls}>Justificación del peso</label>
              <textarea
                className="field mt-1"
                rows={2}
                value={form.justificacion_peso}
                onChange={(e) => setForm({ ...form, justificacion_peso: e.target.value })}
              />
            </div>
            <div className="flex gap-2 sm:col-span-2">
              <button type="submit" className={btnPrimary}>
                {editandoId ? "Guardar cambios" : "Agregar dimensión"}
              </button>
              {editandoId && (
                <button type="button" onClick={reset} className={btnGhost}>
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </CardBody>
      </Card>

      {dims.length === 0 ? (
        <EmptyState>Aún no hay dimensiones. Agrega al menos una para poder evaluar.</EmptyState>
      ) : (
        <Table
          head={
            <tr>
              <th className={th}>Nombre</th>
              <th className={th}>Tipo</th>
              <th className={th}>Peso</th>
              <th className={th}>Justificación</th>
              <th className={th}></th>
            </tr>
          }
        >
          {dims.map((d) => (
            <tr key={d.id} className="hover:bg-slate-50/60">
              <td className={`${td} font-medium text-slate-800`}>{d.nombre}</td>
              <td className={td}>
                <Badge tone={suma(d.tipo) ? "green" : "red"}>
                  {suma(d.tipo) ? "+" : "−"} {d.tipo.replace(/_/g, " ")}
                </Badge>
              </td>
              <td className={`${td} tabular-nums`}>{d.peso ?? "—"}</td>
              <td className={`${td} max-w-xs truncate text-slate-500`}>
                {d.justificacion_peso || "—"}
              </td>
              <td className={`${td} space-x-3 text-right`}>
                <button
                  onClick={() => onEditar(d)}
                  className="text-sm font-medium text-accent-600 hover:text-accent-700"
                >
                  Editar
                </button>
                <button
                  onClick={() => onEliminar(d.id)}
                  className="text-sm font-medium text-red-500 hover:text-red-600"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </Table>
      )}
    </>
  );
}
