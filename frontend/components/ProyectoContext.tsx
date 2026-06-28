"use client";

// Contexto compartido del proyecto seleccionado.
// Todas las pantallas de fase trabajan sobre el mismo proyecto, asi que su
// seleccion vive aqui (y se recuerda en localStorage entre recargas).

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { Proyecto, listarProyectos, crearProyecto } from "../lib/api";

type ProyectoCtx = {
  proyectos: Proyecto[];
  proyectoId: string;
  setProyectoId: (id: string) => void;
  crear: (nombre: string) => Promise<void>;
  cargando: boolean;
};

const Ctx = createContext<ProyectoCtx | null>(null);

const STORAGE_KEY = "proyectoId";

export function ProyectoProvider({ children }: { children: ReactNode }) {
  const [proyectos, setProyectos] = useState<Proyecto[]>([]);
  const [proyectoId, setProyectoIdState] = useState<string>("");
  const [cargando, setCargando] = useState(true);

  function setProyectoId(id: string) {
    setProyectoIdState(id);
    if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, id);
  }

  useEffect(() => {
    listarProyectos()
      .then((data) => {
        setProyectos(data);
        // Reusa la seleccion guardada si sigue existiendo; si no, el primero.
        const guardado =
          typeof window !== "undefined"
            ? localStorage.getItem(STORAGE_KEY)
            : null;
        const valido = data.find((p) => p.id === guardado);
        if (valido) setProyectoIdState(valido.id);
        else if (data.length > 0) setProyectoId(data[0].id);
      })
      .finally(() => setCargando(false));
  }, []);

  async function crear(nombre: string) {
    const p = await crearProyecto({ nombre });
    setProyectos((prev) => [p, ...prev]);
    setProyectoId(p.id);
  }

  return (
    <Ctx.Provider
      value={{ proyectos, proyectoId, setProyectoId, crear, cargando }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useProyecto() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useProyecto debe usarse dentro de ProyectoProvider");
  return ctx;
}
