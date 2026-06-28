"use client";

// Fase 4 — Definición dinámica de dimensiones de priorización.
// Cada dimensión tiene un tipo (beneficio/valor_etico suman; costo/riesgo restan)
// y un peso de 1 a 5 con justificación.

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

// Etiqueta legible y signo (+/-) de cada tipo, para que se entienda el efecto.
const TIPOS: { value: TipoDimension; label: string; signo: string }[] = [
  { value: "beneficio", label: "Beneficio", signo: "+" },
  { value: "valor_etico", label: "Valor ético", signo: "+" },
  { value: "costo", label: "Costo", signo: "−" },
  { value: "riesgo_etico_residual", label: "Riesgo ético residual", signo: "−" },
];

const FORM_VACIO: DimensionInput = {
  nombre: "",
  tipo: "beneficio",
  descripcion: "",
  peso: 3,
  justificacion_peso: "",
};

function signoDe(tipo: string) {
  return TIPOS.find((t) => t.value === tipo)?.signo ?? "";
}

export default function Page() {
  const { proyectoId } = useProyecto();
  const [dimensiones, setDimensiones] = useState<Dimension[]>([]);
  const [form, setForm] = useState<DimensionInput>(FORM_VACIO);
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!proyectoId) {
      setDimensiones([]);
      return;
    }
    cargar();
  }, [proyectoId]);

  function cargar() {
    listarDimensiones(proyectoId)
      .then(setDimensiones)
      .catch((e) => setError(e.message));
  }

  function resetForm() {
    setForm(FORM_VACIO);
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
    if (!proyectoId) {
      setError("Selecciona o crea un proyecto en la barra superior.");
      return;
    }
    try {
      if (editandoId) await editarDimension(editandoId, form);
      else await crearDimension(proyectoId, form);
      resetForm();
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
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Fase 4 — Dimensiones de priorización</h1>
        <p className="text-sm text-gray-600">
          Define los criterios. Beneficio y valor ético <b>suman</b>; costo y
          riesgo ético residual <b>restan</b> en el ranking.
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="mb-6 rounded-lg border bg-white p-4">
        <h2 className="mb-3 font-semibold">
          {editandoId ? "Editar dimensión" : "Nueva dimensión"}
        </h2>
        <form onSubmit={onGuardar} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="text-sm">
            Nombre *
            <input
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
            />
          </label>
          <label className="text-sm">
            Tipo
            <select
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.tipo}
              onChange={(e) =>
                setForm({ ...form, tipo: e.target.value as TipoDimension })
              }
            >
              {TIPOS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label} ({t.signo})
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Peso (1 a 5)
            <input
              type="number"
              min={1}
              max={5}
              required
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.peso}
              onChange={(e) =>
                setForm({ ...form, peso: Number(e.target.value) })
              }
            />
          </label>
          <label className="text-sm">
            Descripción
            <input
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
            />
          </label>
          <label className="text-sm sm:col-span-2">
            Justificación del peso
            <textarea
              className="mt-1 w-full rounded border px-3 py-2"
              rows={2}
              value={form.justificacion_peso}
              onChange={(e) =>
                setForm({ ...form, justificacion_peso: e.target.value })
              }
            />
          </label>
          <div className="flex gap-2 sm:col-span-2">
            <button
              type="submit"
              className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-500"
            >
              {editandoId ? "Guardar cambios" : "Agregar dimensión"}
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
          Dimensiones del proyecto ({dimensiones.length})
        </h2>
        {dimensiones.length === 0 ? (
          <p className="text-sm text-gray-500">
            Aún no hay dimensiones. Agrega al menos una para poder evaluar y
            rankear.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-gray-600">
                <tr>
                  <th className="py-2 pr-3">Nombre</th>
                  <th className="py-2 pr-3">Tipo</th>
                  <th className="py-2 pr-3">Peso</th>
                  <th className="py-2 pr-3">Justificación</th>
                  <th className="py-2 pr-3"></th>
                </tr>
              </thead>
              <tbody>
                {dimensiones.map((d) => (
                  <tr key={d.id} className="border-b last:border-0">
                    <td className="py-2 pr-3 font-medium">{d.nombre}</td>
                    <td className="py-2 pr-3">
                      <span
                        className={
                          "rounded px-2 py-0.5 text-xs " +
                          (signoDe(d.tipo) === "+"
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800")
                        }
                      >
                        {signoDe(d.tipo)} {d.tipo}
                      </span>
                    </td>
                    <td className="py-2 pr-3">{d.peso ?? "—"}</td>
                    <td className="py-2 pr-3 text-gray-600">
                      {d.justificacion_peso || "—"}
                    </td>
                    <td className="space-x-3 py-2 pr-3">
                      <button
                        onClick={() => onEditar(d)}
                        className="text-blue-600 hover:underline"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => onEliminar(d.id)}
                        className="text-red-600 hover:underline"
                      >
                        Eliminar
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
