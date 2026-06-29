// Primitivas de interfaz reutilizables para mantener una estética coherente
// en todas las pantallas (tarjetas, badges, botones, encabezados, tablas).

import { ReactNode } from "react";

// --- Clases reutilizables (para usar en formularios/botones sueltos) ---
export const btnPrimary =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-accent-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-accent-700 disabled:opacity-50";
export const btnDark =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-ink-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-ink-700 disabled:opacity-50";
export const btnGhost =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50";
export const labelCls = "block text-sm font-medium text-slate-600";

// --- Card ---
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white shadow-card ${className}`}
    >
      {children}
    </div>
  );
}

export function CardBody({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}

// --- Encabezado de página ---
export function PageHeader({
  eyebrow,
  title,
  subtitle,
  actions,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow && (
          <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-accent-600">
            {eyebrow}
          </div>
        )}
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}

// --- Tarjeta de métrica (dashboard) ---
export function StatCard({
  label,
  value,
  hint,
  accent = "slate",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: "slate" | "teal" | "amber" | "red" | "green";
}) {
  const accents: Record<string, string> = {
    slate: "text-slate-900",
    teal: "text-accent-600",
    amber: "text-amber-500",
    red: "text-red-500",
    green: "text-emerald-500",
  };
  return (
    <Card className="transition hover:shadow-cardhover">
      <div className="p-5">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </div>
        <div className={`mt-2 text-3xl font-bold tabular-nums ${accents[accent]}`}>
          {value}
        </div>
        {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
      </div>
    </Card>
  );
}

// --- Badge / pill ---
type Tone = "slate" | "blue" | "teal" | "amber" | "red" | "green" | "violet";
const toneCls: Record<Tone, string> = {
  slate: "bg-slate-100 text-slate-600",
  blue: "bg-blue-50 text-blue-700",
  teal: "bg-accent-50 text-accent-700",
  amber: "bg-amber-50 text-amber-700",
  red: "bg-red-50 text-red-700",
  green: "bg-emerald-50 text-emerald-700",
  violet: "bg-violet-50 text-violet-700",
};
export function Badge({
  children,
  tone = "slate",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${toneCls[tone]}`}
    >
      {children}
    </span>
  );
}

// --- Punto de color (bandera ética) ---
export function Dot({ tone = "slate" }: { tone?: "slate" | "amber" | "red" | "green" | "ink" }) {
  const map: Record<string, string> = {
    slate: "bg-slate-300",
    amber: "bg-amber-400",
    red: "bg-red-500",
    green: "bg-emerald-500",
    ink: "bg-slate-700",
  };
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${map[tone]}`} />;
}

// --- Estado vacío ---
export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <Card>
      <div className="px-5 py-10 text-center text-sm text-slate-500">{children}</div>
    </Card>
  );
}

// --- Tabla (wrapper + clases de celda) ---
export function Table({ head, children }: { head: ReactNode; children: ReactNode }) {
  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50/70 text-xs uppercase tracking-wide text-slate-500">
            {head}
          </thead>
          <tbody className="divide-y divide-slate-100">{children}</tbody>
        </table>
      </div>
    </Card>
  );
}

export const th = "px-4 py-3 font-semibold";
export const td = "px-4 py-3 align-middle";

// --- Alertas ---
export function Alert({
  tone = "red",
  children,
}: {
  tone?: "red" | "green" | "amber";
  children: ReactNode;
}) {
  const map = {
    red: "border-red-200 bg-red-50 text-red-700",
    green: "border-emerald-200 bg-emerald-50 text-emerald-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
  };
  return (
    <div className={`mb-4 rounded-lg border px-4 py-3 text-sm ${map[tone]}`}>{children}</div>
  );
}
