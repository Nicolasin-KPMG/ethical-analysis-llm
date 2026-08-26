"use client";

// Pantalla de acceso: panel de marca (navy + teal) a la izquierda y formulario
// a la derecha, con alternancia entre iniciar sesión y crear cuenta. Se muestra
// sola (sin sidebar); AppShell redirige aquí cuando no hay sesión.

import { FormEvent, useState } from "react";
import { useAuth } from "../../components/AuthContext";
import { btnPrimary } from "../../components/ui";

type Modo = "login" | "registro";

const FEATURES = [
  "Detecta riesgos éticos en tus requisitos",
  "Propone tratamientos con base normativa",
  "Prioriza equilibrando beneficio y riesgo",
];

export default function LoginPage() {
  const { login, registrar } = useAuth();
  const [modo, setModo] = useState<Modo>("login");
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const esRegistro = modo === "registro";

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      if (esRegistro) await registrar(nombre.trim(), email.trim(), password);
      else await login(email.trim(), password);
      // AppShell detecta la sesión y redirige al dashboard.
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo completar la acción");
      setEnviando(false);
    }
  }

  function cambiarModo(nuevo: Modo) {
    setModo(nuevo);
    setError(null);
  }

  return (
    <div className="flex min-h-screen bg-canvas">
      {/* Panel de marca */}
      <aside className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-ink-900 p-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-accent-500/20 blur-3xl"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-accent-700/20 blur-3xl"
          aria-hidden
        />
        <div className="relative flex items-center gap-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-accent-400" />
          <span className="text-[15px] font-semibold tracking-tight">Gestión Ética</span>
        </div>

        <div className="relative">
          <h1 className="text-4xl font-bold leading-tight tracking-tight">
            Gestiona la ética de
            <br />
            tus requisitos con IA.
          </h1>
          <p className="mt-4 max-w-md text-[15px] leading-relaxed text-slate-300">
            Un método de seis fases para decidir qué construir — y hacerlo bien.
          </p>
          <ul className="mt-8 space-y-3">
            {FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-3 text-sm text-slate-200">
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-accent-500/20 text-accent-300">
                  ✓
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative text-xs text-slate-500">
          Tesis · Nicolás Pérez — Universidad San Sebastián
        </div>
      </aside>

      {/* Formulario */}
      <main className="flex w-full flex-col justify-center px-6 py-12 sm:px-12 lg:w-1/2">
        <div className="mx-auto w-full max-w-sm">
          {/* Marca visible en móvil */}
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <span className="h-2.5 w-2.5 rounded-full bg-accent-500" />
            <span className="text-[15px] font-semibold tracking-tight text-slate-900">
              Gestión Ética
            </span>
          </div>

          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            {esRegistro ? "Crea tu cuenta" : "Bienvenido de vuelta"}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {esRegistro
              ? "Regístrate para empezar a analizar requisitos."
              : "Ingresa para continuar con tu proyecto."}
          </p>

          {/* Alternador de modo */}
          <div className="mt-6 grid grid-cols-2 gap-1 rounded-lg bg-slate-100 p-1 text-sm font-medium">
            <button
              type="button"
              onClick={() => cambiarModo("login")}
              className={
                "rounded-md py-1.5 transition " +
                (!esRegistro ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700")
              }
            >
              Iniciar sesión
            </button>
            <button
              type="button"
              onClick={() => cambiarModo("registro")}
              className={
                "rounded-md py-1.5 transition " +
                (esRegistro ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700")
              }
            >
              Crear cuenta
            </button>
          </div>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            {esRegistro && (
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-600">Nombre</label>
                <input
                  className="field"
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Tu nombre"
                  required
                  autoComplete="name"
                />
              </div>
            )}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Correo</label>
              <input
                className="field"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@correo.com"
                required
                autoComplete="email"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-600">Contraseña</label>
              <input
                className="field"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={esRegistro ? "Mínimo 6 caracteres" : "••••••••"}
                required
                minLength={6}
                autoComplete={esRegistro ? "new-password" : "current-password"}
              />
            </div>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </div>
            )}

            <button type="submit" disabled={enviando} className={`${btnPrimary} w-full`}>
              {enviando
                ? "Un momento…"
                : esRegistro
                  ? "Crear cuenta"
                  : "Iniciar sesión"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            {esRegistro ? "¿Ya tienes cuenta? " : "¿No tienes cuenta? "}
            <button
              type="button"
              onClick={() => cambiarModo(esRegistro ? "login" : "registro")}
              className="font-medium text-accent-600 hover:text-accent-700"
            >
              {esRegistro ? "Inicia sesión" : "Regístrate"}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}
