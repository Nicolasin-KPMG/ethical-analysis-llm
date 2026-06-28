"use client";

// Documentos normativos y normas activas por proyecto (apoyo al RAG, regla 9).
// Por defecto un proyecto contrasta contra TODAS las normas; aquí se puede acotar
// el conjunto activo con checkboxes.

import { useEffect, useState } from "react";
import {
  Documento,
  listarDocumentos,
  crearDocumento,
  listarNormasActivas,
  configurarNormasActivas,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";

export default function Page() {
  const { proyectoId } = useProyecto();
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [activas, setActivas] = useState<Set<string>>(new Set());
  const [nombre, setNombre] = useState("");
  const [jurisdiccion, setJurisdiccion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    listarDocumentos().then(setDocumentos).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!proyectoId) return;
    listarNormasActivas(proyectoId)
      .then((d) => setActivas(new Set(d.map((x) => x.id))))
      .catch((e) => setError(e.message));
  }, [proyectoId]);

  async function onCrear() {
    if (!nombre.trim()) return;
    setError(null);
    try {
      await crearDocumento({ nombre: nombre.trim(), jurisdiccion: jurisdiccion.trim() || undefined });
      setNombre("");
      setJurisdiccion("");
      setDocumentos(await listarDocumentos());
    } catch (e: any) {
      setError(e.message);
    }
  }

  function toggle(id: string) {
    const s = new Set(activas);
    s.has(id) ? s.delete(id) : s.add(id);
    setActivas(s);
  }

  async function onGuardar() {
    if (!proyectoId) return;
    setError(null);
    setMsg(null);
    try {
      await configurarNormasActivas(proyectoId, Array.from(activas));
      setMsg("Normas activas guardadas. (Sin selección = todas activas por defecto.)");
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <main className="mx-auto max-w-4xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Documentos normativos y normas activas</h1>
        <p className="text-sm text-gray-600">
          Registra los documentos y elige cuáles contrasta este proyecto. El texto
          de cada norma se ingiere al RAG por separado (ver backend/datos).
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}
      {msg && (
        <div className="mb-4 rounded border border-green-300 bg-green-50 p-3 text-sm text-green-700">{msg}</div>
      )}

      <section className="mb-6 rounded-lg border bg-white p-4">
        <h2 className="mb-3 font-semibold">Nuevo documento normativo</h2>
        <div className="flex flex-wrap gap-2">
          <input
            className="flex-1 rounded border px-3 py-2"
            placeholder="Nombre (EU AI Act, GDPR, Ley 19.628…)"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
          <input
            className="rounded border px-3 py-2"
            placeholder="Jurisdicción (UE, Chile…)"
            value={jurisdiccion}
            onChange={(e) => setJurisdiccion(e.target.value)}
          />
          <button onClick={onCrear} className="rounded bg-gray-800 px-4 py-2 text-white hover:bg-gray-700">
            Agregar
          </button>
        </div>
      </section>

      <section className="rounded-lg border bg-white p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold">Normas activas del proyecto</h2>
          <button onClick={onGuardar} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500">
            Guardar selección
          </button>
        </div>
        {documentos.length === 0 ? (
          <p className="text-sm text-gray-500">No hay documentos registrados.</p>
        ) : (
          <ul className="space-y-2">
            {documentos.map((d) => (
              <li key={d.id} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={activas.has(d.id)}
                  onChange={() => toggle(d.id)}
                  id={`doc-${d.id}`}
                />
                <label htmlFor={`doc-${d.id}`} className="text-sm">
                  {d.nombre} {d.jurisdiccion && <span className="text-gray-400">· {d.jurisdiccion}</span>}
                </label>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
