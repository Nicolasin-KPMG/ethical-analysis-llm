import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "../components/AuthContext";
import AppShell from "../components/AppShell";

export const metadata: Metadata = {
  title: "Gestión ética de requisitos",
  description: "Método de seis fases para la gestión ética y priorización de requisitos",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
