"use client";

// Barra superior del contenido: contexto del proyecto (selector tipo encabezado)
// con creación rápida inline. Sticky, fondo claro.

import { useState } from "react";
import { useProyecto } from "./ProyectoContext";

export default function Topbar() {
  const { proyectos, proyectoId, setProyectoId, crear } = useProyecto();
  const [creando, setCreando] = useState(false);
  const [nombre, setNombre] = useState("");

  const actual = proyectos.find((p) => p.id === proyectoId);

  async function onCrear() {
    if (!nombre.trim()) return;
    await crear(nombre.trim());
    setNombre("");
    setCreando(false);
  }

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-6 py-3">
        <div className="min-w-0">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Proyecto
          </div>
          <div className="flex items-center gap-2">
            <select
              className="-ml-1 max-w-[60vw] truncate rounded-md border-0 bg-transparent px-1 py-0.5 text-lg font-bold tracking-tight text-slate-900 outline-none hover:bg-slate-100 focus:ring-2 focus:ring-accent-500/30"
              value={proyectoId}
              onChange={(e) => setProyectoId(e.target.value)}
            >
              {proyectos.length === 0 && <option value="">Sin proyectos</option>}
              {proyectos.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-shrink-0 items-center gap-2">
          {creando ? (
            <div className="flex items-center gap-2">
              <input
                autoFocus
                className="field-sm w-52"
                placeholder="Nombre del proyecto"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onCrear()}
              />
              <button
                onClick={onCrear}
                className="rounded-lg bg-accent-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-accent-700"
              >
                Crear
              </button>
              <button
                onClick={() => setCreando(false)}
                className="rounded-lg px-2 py-1.5 text-sm text-slate-500 hover:bg-slate-100"
              >
                ✕
              </button>
            </div>
          ) : (
            <button
              onClick={() => setCreando(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              <span className="text-base leading-none">+</span> Nuevo proyecto
            </button>
          )}
          {actual && (
            <span className="hidden rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-600 sm:inline">
              {actual.nombre.length > 18 ? actual.nombre.slice(0, 18) + "…" : actual.nombre}
            </span>
          )}
        </div>
      </div>
    </header>
  );
}
