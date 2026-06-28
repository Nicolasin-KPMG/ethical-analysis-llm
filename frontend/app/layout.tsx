import type { Metadata } from "next";
import "./globals.css";
import { ProyectoProvider } from "../components/ProyectoContext";
import Nav from "../components/Nav";

export const metadata: Metadata = {
  title: "Gestión ética de requisitos",
  description: "Método de 8 fases — Tesis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        {/* El proyecto seleccionado es compartido por todas las fases. */}
        <ProyectoProvider>
          <Nav />
          {children}
        </ProyectoProvider>
      </body>
    </html>
  );
}
