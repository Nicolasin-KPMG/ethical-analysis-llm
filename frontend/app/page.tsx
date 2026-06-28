"use client";

// Pantalla de la Fase 1: registro de requisitos.
// El proyecto seleccionado viene del contexto compartido (barra superior).
// Aqui: formulario para crear / editar requisitos y tabla del proyecto.

import { useEffect, useState } from "react";
import {
  Requisito,
  RequisitoInput,
  listarRequisitos,
  crearRequisito,
  editarRequisito,
} from "../lib/api";
import { useProyecto } from "../components/ProyectoContext";

const TIPOS = [
  { value: "funcional", label: "Funcional" },
  { value: "no_funcional", label: "No funcional" },
  { value: "restriccion", label: "Restricción" },
  { value: "otro", label: "Otro" },
];

const FORM_VACIO: RequisitoInput = {
  codigo: "",
  nombre: "",
  descripcion: "",
  tipo: "funcional",
  stakeholder: "",
};

export default function Page() {
  const { proyectoId } = useProyecto();

  const [requisitos, setRequisitos] = useState<Requisito[]>([]);
  const [form, setForm] = useState<RequisitoInput>(FORM_VACIO);
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) {
      setRequisitos([]);
      return;
    }
    cargar();
  }, [proyectoId]);

  function cargar() {
    listarRequisitos(proyectoId)
      .then(setRequisitos)
      .catch((e) => setError(e.message));
  }

  function resetForm() {
    setForm(FORM_VACIO);
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
    if (!proyectoId) {
      setError("Selecciona o crea un proyecto en la barra superior.");
      return;
    }
    try {
      if (editandoId) await editarRequisito(editandoId, form);
      else await crearRequisito(proyectoId, form);
      resetForm();
      cargar();
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Fase 1 — Registro de requisitos</h1>
        <p className="text-sm text-gray-600">
          Registra los requisitos del proyecto. Nacen en estado “pendiente de
          análisis”.
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="mb-6 rounded-lg border bg-white p-4">
        <h2 className="mb-3 font-semibold">
          {editandoId ? "Editar requisito" : "Nuevo requisito"}
        </h2>
        <form onSubmit={onGuardar} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="text-sm">
            Código
            <input
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.codigo}
              onChange={(e) => setForm({ ...form, codigo: e.target.value })}
              placeholder="REQ-001"
            />
          </label>
          <label className="text-sm">
            Nombre *
            <input
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
            />
          </label>
          <label className="text-sm sm:col-span-2">
            Descripción
            <textarea
              className="mt-1 w-full rounded border px-3 py-2"
              rows={2}
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
            />
          </label>
          <label className="text-sm">
            Tipo
            <select
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.tipo}
              onChange={(e) => setForm({ ...form, tipo: e.target.value })}
            >
              {TIPOS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Stakeholder
            <input
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.stakeholder}
              onChange={(e) => setForm({ ...form, stakeholder: e.target.value })}
            />
          </label>
          <div className="flex gap-2 sm:col-span-2">
            <button
              type="submit"
              className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500"
            >
              {editandoId ? "Guardar cambios" : "Registrar requisito"}
            </button>
            {editandoId && (
              <button
                type="button"
                onClick={resetForm}
                className="rounded border px-4 py-2 hover:bg-gray-100"
              >
                Cancelar
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="rounded-lg border bg-white p-4">
        <h2 className="mb-3 font-semibold">
          Requisitos registrados ({requisitos.length})
        </h2>
        {requisitos.length === 0 ? (
          <p className="text-sm text-gray-500">
            No hay requisitos en este proyecto todavía.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-gray-600">
                <tr>
                  <th className="py-2 pr-3">Código</th>
                  <th className="py-2 pr-3">Nombre</th>
                  <th className="py-2 pr-3">Tipo</th>
                  <th className="py-2 pr-3">Stakeholder</th>
                  <th className="py-2 pr-3">Estado</th>
                  <th className="py-2 pr-3"></th>
                </tr>
              </thead>
              <tbody>
                {requisitos.map((r) => (
                  <tr key={r.id} className="border-b last:border-0">
                    <td className="py-2 pr-3">{r.codigo || "—"}</td>
                    <td className="py-2 pr-3 font-medium">{r.nombre}</td>
                    <td className="py-2 pr-3">{r.tipo || "—"}</td>
                    <td className="py-2 pr-3">{r.stakeholder || "—"}</td>
                    <td className="py-2 pr-3">
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
                        {r.estado}
                      </span>
                    </td>
                    <td className="py-2 pr-3">
                      <button
                        onClick={() => onEditar(r)}
                        className="text-blue-600 hover:underline"
                      >
                        Editar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
