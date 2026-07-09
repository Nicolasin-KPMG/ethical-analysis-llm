"use client";

// Barra lateral oscura con el proceso guiado de 8 fases (estética de referencia:
// navy profundo + acento teal). Wordmark sobrio, sin logo recargado.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./AuthContext";

type Item = { href: string; paso: string; label: string };

// Iniciales del usuario para el avatar (máx. 2 letras).
function iniciales(nombre: string): string {
  const partes = nombre.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return "?";
  if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
  return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}

const PASOS: Item[] = [
  { href: "/", paso: "•", label: "Dashboard" },
  { href: "/registro", paso: "1", label: "Registro de requisitos" },
  { href: "/analisis", paso: "2·3", label: "Análisis ético" },
  { href: "/dimensiones", paso: "4", label: "Dimensiones" },
  { href: "/evaluacion", paso: "5", label: "Evaluación" },
  { href: "/ranking", paso: "6", label: "Ranking" },
  { href: "/trazabilidad", paso: "7", label: "Trazabilidad" },
  { href: "/visualizacion", paso: "8", label: "Visualización" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { usuario, logout } = useAuth();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <aside className="sidebar-scroll flex h-screen w-64 flex-shrink-0 flex-col overflow-y-auto bg-ink-900 text-slate-300">
      {/* Marca (sobria) */}
      <div className="px-5 py-5">
        <div className="flex items-center gap-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-accent-400" />
          <span className="text-[15px] font-semibold tracking-tight text-white">
            Gestión Ética
          </span>
        </div>
        <div className="mt-0.5 pl-5 text-[11px] uppercase tracking-wider text-slate-500">
          Priorización de requisitos
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 px-3">
        <div className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          Proceso guiado
        </div>
        <ul className="space-y-1">
          {PASOS.map((it) => {
            const active = isActive(it.href);
            return (
              <li key={it.href}>
                <Link
                  href={it.href}
                  className={
                    "group relative flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition " +
                    (active
                      ? "bg-ink-700/70 font-medium text-white before:absolute before:-left-2 before:top-1.5 before:bottom-1.5 before:w-1 before:rounded-full before:bg-accent-400"
                      : "text-slate-400 hover:bg-ink-800 hover:text-slate-100")
                  }
                >
                  <span
                    className={
                      "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md text-[11px] font-semibold " +
                      (active
                        ? "bg-accent-500 text-ink-950"
                        : "bg-ink-700 text-slate-400 group-hover:text-slate-200")
                    }
                  >
                    {it.paso}
                  </span>
                  <span className="truncate">{it.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="my-4 border-t border-white/5" />
        <ul className="space-y-1">
          <li>
            <Link
              href="/normas"
              className={
                "flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition " +
                (isActive("/normas")
                  ? "bg-ink-700/70 font-medium text-white"
                  : "text-slate-400 hover:bg-ink-800 hover:text-slate-100")
              }
            >
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-ink-700 text-[12px]">
                ⚖
              </span>
              <span>Normas y corpus</span>
            </Link>
          </li>
        </ul>
      </nav>

      {/* Perfil + cerrar sesión */}
      <div className="mt-auto border-t border-white/5 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-accent-600 text-sm font-semibold text-white">
            {usuario ? iniciales(usuario.nombre) : "?"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-white">
              {usuario?.nombre ?? "Invitado"}
            </div>
            <div className="truncate text-xs text-slate-500">{usuario?.email ?? ""}</div>
          </div>
          <button
            onClick={logout}
            title="Cerrar sesión"
            aria-label="Cerrar sesión"
            className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-ink-800 hover:text-white"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-4 w-4"
            >
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  );
}
