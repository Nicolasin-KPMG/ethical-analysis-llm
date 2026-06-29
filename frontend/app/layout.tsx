import type { Metadata } from "next";
import "./globals.css";
import { ProyectoProvider } from "../components/ProyectoContext";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";

export const metadata: Metadata = {
  title: "Gestión ética de requisitos",
  description: "Método de 8 fases para la gestión ética y priorización de requisitos",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
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
      </body>
    </html>
  );
}
