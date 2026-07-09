"use client";

// Envoltura de la app: decide que se renderiza segun la sesion.
// - Ruta /login: se muestra sola (sin sidebar).
// - Sin sesion: redirige a /login.
// - Con sesion: monta el proyecto compartido y el chrome (sidebar + topbar).
//
// El ProyectoProvider se monta solo aqui (con sesion) para no llamar a la API
// protegida antes de tener token.

import { ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "./AuthContext";
import { ProyectoProvider } from "./ProyectoContext";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function Cargando() {
  return (
    <div className="flex h-screen items-center justify-center bg-canvas">
      <div className="flex items-center gap-3 text-slate-400">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-accent-500" />
        <span className="text-sm">Cargando…</span>
      </div>
    </div>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const { usuario, cargando } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const enLogin = pathname === "/login";

  // Redirecciones segun el estado de sesion.
  useEffect(() => {
    if (cargando) return;
    if (!usuario && !enLogin) router.replace("/login");
    if (usuario && enLogin) router.replace("/");
  }, [cargando, usuario, enLogin, router]);

  // La pantalla de login se muestra sola, sin chrome.
  if (enLogin) return <>{children}</>;

  if (cargando) return <Cargando />;

  // Aún sin sesión (mientras corre el replace a /login): no parpadees la app.
  if (!usuario) return <Cargando />;

  return (
    <ProyectoProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-6xl px-6 py-8">{children}</div>
          </main>
        </div>
      </div>
    </ProyectoProvider>
  );
}
