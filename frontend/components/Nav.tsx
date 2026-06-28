"use client";

// Barra superior: selector de proyecto (compartido) + crear inline + navegacion
// por fases. El metodo es un flujo de pasos, asi que se navega como pestanas.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useProyecto } from "./ProyectoContext";

// Fases disponibles hasta M2. Las demas se agregaran en sus hitos.
const FASES = [
  { href: "/", label: "Fase 1 · Requisitos" },
  { href: "/analisis", label: "Fases 2-3 · Análisis" },
  { href: "/dimensiones", label: "Fase 4 · Dimensiones" },
  { href: "/evaluacion", label: "Fase 5 · Evaluación" },
  { href: "/ranking", label: "Fase 6 · Ranking" },
  { href: "/visualizacion", label: "Fase 8 · Visualización" },
  { href: "/normas", label: "Normas" },
];

export default function Nav() {
  const pathname = usePathname();
  const { proyectos, proyectoId, setProyectoId, crear } = useProyecto();
  const [nuevo, setNuevo] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onCrear() {
    if (!nuevo.trim()) return;
    setError(null);
    try {
      await crear(nuevo.trim());
      setNuevo("");
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <nav className="border-b bg-white">
      <div className="mx-auto max-w-5xl p-4">
        {/* Selector de proyecto */}
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-gray-700">Proyecto:</span>
          <select
            className="rounded border px-3 py-1.5"
            value={proyectoId}
            onChange={(e) => setProyectoId(e.target.value)}
          >
            {proyectos.length === 0 && <option value="">(sin proyectos)</option>}
            {proyectos.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
          <span className="text-gray-400">o crear:</span>
          <input
            className="rounded border px-3 py-1.5"
            placeholder="Nuevo proyecto"
            value={nuevo}
            onChange={(e) => setNuevo(e.target.value)}
          />
          <button
            type="button"
            onClick={onCrear}
            className="rounded bg-gray-800 px-3 py-1.5 text-sm text-white hover:bg-gray-700"
          >
            Crear
          </button>
          {error && <span className="text-sm text-red-600">{error}</span>}
        </div>

        {/* Pestanas de fases */}
        <div className="flex flex-wrap gap-1">
          {FASES.map((f) => {
            const activo = pathname === f.href;
            return (
              <Link
                key={f.href}
                href={f.href}
                className={
                  "rounded px-3 py-1.5 text-sm " +
                  (activo
                    ? "bg-blue-600 text-white"
                    : "text-gray-700 hover:bg-gray-100")
                }
              >
                {f.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
