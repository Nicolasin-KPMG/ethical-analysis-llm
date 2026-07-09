"use client";

// Contexto de sesion: guarda el usuario y el token, y expone login / registro /
// logout. El token vive en localStorage (via lib/api). Al montar, si hay token
// se valida contra /auth/me; si el backend responde 401 en cualquier llamada,
// se cierra la sesion automaticamente.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import {
  Usuario,
  getToken,
  setToken,
  setUnauthorizedHandler,
  obtenerPerfil,
  login as apiLogin,
  registrar as apiRegistrar,
} from "../lib/api";

type AuthCtx = {
  usuario: Usuario | null;
  cargando: boolean;
  login: (email: string, password: string) => Promise<void>;
  registrar: (nombre: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  const logout = useCallback(() => {
    setToken(null);
    setUsuario(null);
  }, []);

  // Cualquier 401 desde la API cierra la sesion.
  useEffect(() => {
    setUnauthorizedHandler(() => logout());
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  // Al cargar: si hay token, validarlo trayendo el perfil.
  useEffect(() => {
    if (!getToken()) {
      setCargando(false);
      return;
    }
    obtenerPerfil()
      .then((u) => setUsuario(u))
      .catch(() => logout())
      .finally(() => setCargando(false));
  }, [logout]);

  async function login(email: string, password: string) {
    const res = await apiLogin({ email, password });
    setToken(res.access_token);
    setUsuario(res.usuario);
  }

  async function registrar(nombre: string, email: string, password: string) {
    const res = await apiRegistrar({ nombre, email, password });
    setToken(res.access_token);
    setUsuario(res.usuario);
  }

  return (
    <Ctx.Provider value={{ usuario, cargando, login, registrar, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
