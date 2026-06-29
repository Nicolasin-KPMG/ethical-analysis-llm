"use client";

// Documentos normativos y normas activas por proyecto (apoyo al RAG).

import { useEffect, useState } from "react";
import {
  Documento,
  listarDocumentos,
  crearDocumento,
  listarNormasActivas,
  configurarNormasActivas,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import {
  Card,
  CardBody,
  PageHeader,
  Badge,
  EmptyState,
  Alert,
  btnPrimary,
  btnDark,
  labelCls,
} from "../../components/ui";

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
    <>
      <PageHeader
        title="Normas y corpus"
        subtitle="Registra los documentos normativos y elige cuáles contrasta este proyecto. El texto se ingiere al RAG por separado."
      />

      {error && <Alert>{error}</Alert>}
      {msg && <Alert tone="green">{msg}</Alert>}

      <Card className="mb-6">
        <CardBody>
          <h2 className="mb-4 text-sm font-semibold text-slate-700">Nuevo documento normativo</h2>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[240px]">
              <label className={labelCls}>Nombre</label>
              <input
                className="field mt-1"
                placeholder="EU AI Act, GDPR, Ley 19.628…"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>
            <div>
              <label className={labelCls}>Jurisdicción</label>
              <input
                className="field mt-1 w-40"
                placeholder="UE, Chile…"
                value={jurisdiccion}
                onChange={(e) => setJurisdiccion(e.target.value)}
              />
            </div>
            <button onClick={onCrear} className={btnPrimary}>Agregar</button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-700">Normas activas del proyecto</h2>
            <button onClick={onGuardar} className={btnDark}>Guardar selección</button>
          </div>
          {documentos.length === 0 ? (
            <p className="text-sm text-slate-500">No hay documentos registrados.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {documentos.map((d) => (
                <li key={d.id} className="flex items-center gap-3 py-2.5">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300 text-accent-600 focus:ring-accent-500"
                    checked={activas.has(d.id)}
                    onChange={() => toggle(d.id)}
                    id={`doc-${d.id}`}
                  />
                  <label htmlFor={`doc-${d.id}`} className="flex flex-1 items-center gap-2 text-sm text-slate-700">
                    <span className="font-medium">{d.nombre}</span>
                    {d.jurisdiccion && <Badge tone="slate">{d.jurisdiccion}</Badge>}
                  </label>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>
    </>
  );
}
