"use client";

// Notificaciones "toast" (arriba a la derecha). Provider + hook useToast():
//   const toast = useToast();
//   toast.exito("Tratamiento registrado: aceptado");
// Se auto-cierran y se apilan. Reutilizable en cualquier pantalla.

import { createContext, useCallback, useContext, useState, ReactNode } from "react";

type Tono = "exito" | "error" | "info";
type Item = { id: number; mensaje: string; tono: Tono };

type ToastCtx = {
  push: (mensaje: string, tono?: Tono) => void;
  exito: (mensaje: string) => void;
  error: (mensaje: string) => void;
  info: (mensaje: string) => void;
};

const Ctx = createContext<ToastCtx | null>(null);
let _id = 1;

const ESTILO: Record<Tono, { borde: string; icono: string; color: string }> = {
  exito: { borde: "border-l-emerald-500", icono: "✓", color: "text-emerald-600" },
  error: { borde: "border-l-red-500", icono: "!", color: "text-red-600" },
  info: { borde: "border-l-accent-500", icono: "i", color: "text-accent-600" },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Item[]>([]);

  const quitar = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (mensaje: string, tono: Tono = "exito") => {
      const id = _id++;
      setItems((prev) => [...prev, { id, mensaje, tono }]);
      setTimeout(() => quitar(id), 4000);
    },
    [quitar],
  );

  const api: ToastCtx = {
    push,
    exito: (m) => push(m, "exito"),
    error: (m) => push(m, "error"),
    info: (m) => push(m, "info"),
  };

  return (
    <Ctx.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2">
        {items.map((t) => {
          const s = ESTILO[t.tono];
          return (
            <div
              key={t.id}
              className={`animate-toast-in pointer-events-auto flex items-start gap-3 rounded-lg border border-slate-200 border-l-4 ${s.borde} bg-white px-4 py-3 shadow-cardhover`}
            >
              <span className={`mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-slate-50 text-xs font-bold ${s.color}`}>
                {s.icono}
              </span>
              <span className="flex-1 text-sm text-slate-700">{t.mensaje}</span>
              <button
                onClick={() => quitar(t.id)}
                className="flex-shrink-0 text-slate-300 transition hover:text-slate-500"
                aria-label="Cerrar"
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
    </Ctx.Provider>
  );
}

export function useToast() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast debe usarse dentro de ToastProvider");
  return ctx;
}
