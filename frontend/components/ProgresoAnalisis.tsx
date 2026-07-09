"use client";

// Pantalla de carga con barra de progreso "por etapas" para operaciones que
// tardan (el análisis con IA es una sola llamada bloqueante, así que el progreso
// es estimado: la barra avanza suave hacia ~92% y las etapas se van marcando;
// al terminar, el padre desmonta este componente).

import { useEffect, useRef, useState } from "react";

export default function ProgresoAnalisis({
  titulo = "Analizando con IA",
  subtitulo = "Esto puede tardar unos segundos. No cierres la pantalla.",
  etapas,
  duracionEstimadaMs = 22000,
}: {
  titulo?: string;
  subtitulo?: string;
  etapas: string[];
  duracionEstimadaMs?: number;
}) {
  const [progreso, setProgreso] = useState(6);
  const inicio = useRef<number>(Date.now());

  useEffect(() => {
    inicio.current = Date.now();
    const id = setInterval(() => {
      const t = (Date.now() - inicio.current) / duracionEstimadaMs;
      // Ease-out asintótico hacia 92%: rápido al inicio, lento cerca del final.
      const objetivo = 92 * (1 - Math.exp(-2.2 * t));
      setProgreso((p) => Math.max(p, Math.min(92, objetivo)));
    }, 180);
    return () => clearInterval(id);
  }, [duracionEstimadaMs]);

  const n = Math.max(etapas.length, 1);
  const etapaActual = Math.min(n - 1, Math.floor((progreso / 92) * n));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
      <div className="flex items-center gap-3">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-accent-500" />
        <div>
          <h3 className="font-semibold text-slate-900">{titulo}</h3>
          <p className="text-xs text-slate-500">{subtitulo}</p>
        </div>
        <span className="ml-auto text-sm font-semibold tabular-nums text-accent-600">
          {Math.round(progreso)}%
        </span>
      </div>

      {/* Barra */}
      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-accent-500 transition-[width] duration-200 ease-out"
          style={{ width: `${progreso}%` }}
        />
      </div>

      {/* Etapas */}
      <ul className="mt-4 space-y-2">
        {etapas.map((e, i) => {
          const hecha = i < etapaActual;
          const activa = i === etapaActual;
          return (
            <li key={i} className="flex items-center gap-2.5 text-sm">
              <span
                className={
                  "flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[11px] " +
                  (hecha
                    ? "bg-accent-500 text-white"
                    : activa
                      ? "bg-accent-100 text-accent-700"
                      : "bg-slate-100 text-slate-400")
                }
              >
                {hecha ? "✓" : activa ? (
                  <span className="h-2 w-2 animate-pulse rounded-full bg-accent-500" />
                ) : (
                  i + 1
                )}
              </span>
              <span className={hecha ? "text-slate-400 line-through" : activa ? "font-medium text-slate-800" : "text-slate-400"}>
                {e}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
