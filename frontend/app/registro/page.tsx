"use client";

// Fase 1 — Registro de requisitos.

import { useEffect, useState } from "react";
import {
  Requisito,
  RequisitoInput,
  listarRequisitos,
  crearRequisito,
  editarRequisito,
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
import { tipoBadge, estadoBadge } from "../../lib/estado";

const TIPOS = [
  { value: "funcional", label: "Funcional" },
  { value: "no_funcional", label: "No funcional" },
  { value: "restriccion", label: "Restricción" },
  { value: "otro", label: "Otro" },
];

const VACIO: RequisitoInput = {
  codigo: "",
  nombre: "",
  descripcion: "",
  tipo: "funcional",
  stakeholder: "",
};

export default function Page() {
  const { proyectoId } = useProyecto();
  const [requisitos, setRequisitos] = useState<Requisito[]>([]);
  const [form, setForm] = useState<RequisitoInput>(VACIO);
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) return setRequisitos([]);
    cargar();
  }, [proyectoId]);

  function cargar() {
    listarRequisitos(proyectoId).then(setRequisitos).catch((e) => setError(e.message));
  }
  function reset() {
    setForm(VACIO);
    setEditandoId(null);
  }
  function onEditar(r: Requisito) {
    setEditandoId(r.id);
    setForm({
      codigo: r.codigo ?? "",
      nombre: r.nombre ?? "",
      descripcion: r.descripcion ?? "",
      tipo: r.tipo ?? "funcional",
      stakeholder: r.stakeholder ?? "",
    });
  }
  async function onGuardar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!proyectoId) return setError("Selecciona o crea un proyecto arriba.");
    try {
      if (editandoId) await editarRequisito(editandoId, form);
      else await crearRequisito(proyectoId, form);
      reset();
      cargar();
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Fase 1"
        title="Registro de requisitos"
        subtitle="Registra los requisitos del proyecto. Nacen en estado “pendiente de análisis”."
      />

      {error && <Alert>{error}</Alert>}

      <Card className="mb-6">
        <CardBody>
          <h2 className="mb-4 text-sm font-semibold text-slate-700">
            {editandoId ? "Editar requisito" : "Nuevo requisito"}
          </h2>
          <form onSubmit={onGuardar} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={labelCls}>Código</label>
              <input
                className="field mt-1"
                placeholder="REQ-001"
                value={form.codigo}
                onChange={(e) => setForm({ ...form, codigo: e.target.value })}
              />
            </div>
            <div>
              <label className={labelCls}>Nombre *</label>
              <input
                required
                className="field mt-1"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <label className={labelCls}>Descripción</label>
              <textarea
                className="field mt-1"
                rows={2}
                value={form.descripcion}
                onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              />
            </div>
            <div>
              <label className={labelCls}>Tipo</label>
              <select
                className="field mt-1"
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              >
                {TIPOS.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>Stakeholder</label>
              <input
                className="field mt-1"
                value={form.stakeholder}
                onChange={(e) => setForm({ ...form, stakeholder: e.target.value })}
              />
            </div>
            <div className="flex gap-2 sm:col-span-2">
              <button type="submit" className={btnPrimary}>
                {editandoId ? "Guardar cambios" : "Registrar requisito"}
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

      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">
          Requisitos registrados
        </h2>
        <span className="text-sm text-slate-400">{requisitos.length} en total</span>
      </div>

      {requisitos.length === 0 ? (
        <EmptyState>No hay requisitos en este proyecto todavía.</EmptyState>
      ) : (
        <Table
          head={
            <tr>
              <th className={th}>Código</th>
              <th className={th}>Requisito</th>
              <th className={th}>Tipo</th>
              <th className={th}>Stakeholder</th>
              <th className={th}>Estado</th>
              <th className={th}></th>
            </tr>
          }
        >
          {requisitos.map((r) => {
            const tb = tipoBadge(r.tipo);
            const eb = estadoBadge(r.estado);
            return (
              <tr key={r.id} className="hover:bg-slate-50/60">
                <td className={`${td} font-mono text-xs text-slate-500`}>{r.codigo || "—"}</td>
                <td className={`${td} font-medium text-slate-800`}>{r.nombre}</td>
                <td className={td}>
                  <Badge tone={tb.tone}>{tb.label}</Badge>
                </td>
                <td className={`${td} text-slate-600`}>{r.stakeholder || "—"}</td>
                <td className={td}>
                  <Badge tone={eb.tone}>{eb.label}</Badge>
                </td>
                <td className={`${td} text-right`}>
                  <button
                    onClick={() => onEditar(r)}
                    className="text-sm font-medium text-accent-600 hover:text-accent-700"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            );
          })}
        </Table>
      )}
    </>
  );
}
