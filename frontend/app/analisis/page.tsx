"use client";

// Fases 2-3 — Análisis ético (LLM + RAG) y tratamiento.
// El LLM identifica, analiza y propone; el humano edita y decide. Re-análisis manual.

import { useEffect, useState } from "react";
import {
  Requisito,
  Analisis,
  Tema,
  Decision,
  listarRequisitos,
  analizarRequisito,
  obtenerAnalisis,
  editarAnalisis,
  crearTratamiento,
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
  btnGhost,
  btnDark,
  labelCls,
} from "../../components/ui";

const TEMA_VACIO: Tema = {
  tema_etico: "",
  actor_afectado: "",
  tipo_dano: "",
  norma_tensionada_texto: "",
  evidencia: "",
  citas: [],
};

function confianzaTone(c?: string | null) {
  return c === "alta" ? "green" : c === "baja" ? "red" : "amber";
}

export default function Page() {
  const { proyectoId } = useProyecto();
  const [requisitos, setRequisitos] = useState<Requisito[]>([]);
  const [selId, setSelId] = useState<string | null>(null);

  const [analisis, setAnalisis] = useState<Analisis | null>(null);
  const [temas, setTemas] = useState<Tema[]>([]);
  const [confianza, setConfianza] = useState("media");
  const [limitaciones, setLimitaciones] = useState("");

  const [analizando, setAnalizando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const [decision, setDecision] = useState<Decision>("aceptar");
  const [justificacion, setJustificacion] = useState("");
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevaDescripcion, setNuevaDescripcion] = useState("");
  const [derivados, setDerivados] = useState<{ nombre: string; descripcion: string }[]>([]);

  const seleccionado = requisitos.find((r) => r.id === selId) || null;

  useEffect(() => {
    if (!proyectoId) return setRequisitos([]);
    listarRequisitos(proyectoId)
      .then((rs) => setRequisitos(rs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado")))
      .catch((e) => setError(e.message));
  }, [proyectoId]);

  useEffect(() => {
    if (!selId) return;
    setMsg(null);
    setError(null);
    obtenerAnalisis(selId).then(cargarAnalisis).catch((e) => setError(e.message));
  }, [selId]);

  function cargarAnalisis(a: Analisis | null) {
    setAnalisis(a);
    setTemas(a ? a.temas.map((t) => ({ ...t })) : []);
    setConfianza(a?.nivel_confianza ?? "media");
    setLimitaciones(a?.limitaciones ?? "");
    const c3 = a?.capas_2_3?.capa_3_deliberacion;
    setNuevoNombre(c3?.reformulaciones_propuestas?.[0]?.texto_propuesto ?? "");
    setNuevaDescripcion("");
    setDerivados((c3?.requisitos_derivados_propuestos ?? []).map((d) => ({ nombre: d.nombre, descripcion: d.descripcion ?? "" })));
    setDecision("aceptar");
    setJustificacion("");
  }

  async function onAnalizar() {
    if (!selId) return;
    setAnalizando(true);
    setError(null);
    setMsg(null);
    try {
      cargarAnalisis(await analizarRequisito(selId));
      setMsg("Análisis generado por el LLM. Revísalo y edítalo libremente.");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAnalizando(false);
    }
  }
  async function onGuardarAnalisis() {
    if (!selId) return;
    setError(null);
    try {
      cargarAnalisis(await editarAnalisis(selId, { nivel_confianza: confianza, limitaciones, temas }));
      setMsg("Cambios del análisis guardados.");
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function onTratar() {
    if (!selId) return;
    setError(null);
    try {
      const res = await crearTratamiento(selId, {
        decision,
        justificacion,
        nuevo_nombre: decision === "reformular" ? nuevoNombre : undefined,
        nueva_descripcion: decision === "reformular" ? nuevaDescripcion : undefined,
        derivados: decision === "mitigar" ? derivados : undefined,
      });
      const rs = await listarRequisitos(proyectoId);
      setRequisitos(rs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado"));
      if (decision === "reformular" && res.nuevo_requisito_id) {
        setMsg("Se creó una versión nueva (pendiente de re-análisis). La anterior quedó archivada.");
        setSelId(res.nuevo_requisito_id);
      } else if (decision === "mitigar") setMsg(`Se crearon ${res.derivados_ids.length} requisito(s) derivado(s).`);
      else if (decision === "eliminar") { setMsg("Requisito marcado como eliminado."); setSelId(null); }
      else setMsg("Tratamiento registrado: aceptado.");
    } catch (e: any) {
      setError(e.message);
    }
  }
  function setTema(i: number, campo: keyof Tema, valor: string) {
    setTemas(temas.map((t, k) => (k === i ? { ...t, [campo]: valor } : t)));
  }

  if (!proyectoId) return <EmptyState>Selecciona o crea un proyecto arriba.</EmptyState>;

  const c2 = analisis?.capas_2_3?.capa_2_analisis;
  const c3 = analisis?.capas_2_3?.capa_3_deliberacion;

  return (
    <>
      <PageHeader
        eyebrow="Fases 2 y 3"
        title="Análisis ético y tratamiento"
        subtitle="El LLM identifica, analiza y propone; tú editas y decides. El re-análisis es manual."
      />

      {error && <Alert>{error}</Alert>}
      {msg && <Alert tone="green">{msg}</Alert>}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-[260px_1fr]">
        {/* Lista de requisitos */}
        <Card className="h-fit">
          <div className="border-b border-slate-100 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Requisitos vigentes
          </div>
          {requisitos.length === 0 ? (
            <p className="px-4 py-4 text-sm text-slate-500">No hay requisitos.</p>
          ) : (
            <ul className="max-h-[70vh] overflow-y-auto p-2">
              {requisitos.map((r) => (
                <li key={r.id}>
                  <button
                    onClick={() => setSelId(r.id)}
                    className={
                      "w-full rounded-lg px-3 py-2 text-left text-sm transition " +
                      (selId === r.id ? "bg-accent-50 text-accent-800" : "hover:bg-slate-50")
                    }
                  >
                    <div className="font-medium text-slate-800">{r.nombre}</div>
                    <div className="font-mono text-xs text-slate-400">{r.codigo} · {r.estado}</div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Panel del requisito */}
        <div className="space-y-5">
          {!seleccionado ? (
            <EmptyState>Selecciona un requisito para analizarlo.</EmptyState>
          ) : (
            <>
              <Card>
                <CardBody>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h2 className="font-semibold text-slate-900">{seleccionado.nombre}</h2>
                      <p className="mt-0.5 text-xs text-slate-400">
                        {seleccionado.codigo} · {seleccionado.estado}
                        {seleccionado.version_anterior_id && " · versión reformulada"}
                        {seleccionado.origen_requisito_id && " · requisito derivado"}
                      </p>
                      {seleccionado.descripcion && (
                        <p className="mt-2 text-sm text-slate-600">{seleccionado.descripcion}</p>
                      )}
                    </div>
                    <button onClick={onAnalizar} disabled={analizando} className={btnPrimary}>
                      {analizando ? "Analizando…" : analisis ? "Re-analizar con IA" : "Analizar con IA"}
                    </button>
                  </div>
                </CardBody>
              </Card>

              {!analisis ? (
                <EmptyState>Este requisito aún no tiene análisis. Pulsa “Analizar con IA”.</EmptyState>
              ) : (
                <>
                  {/* Metadatos */}
                  <Card>
                    <div className="flex flex-wrap items-center gap-4 px-5 py-3 text-sm">
                      <span className="text-slate-500">Origen: <Badge tone="teal">{analisis.generado_por}</Badge></span>
                      <span className="text-slate-500">Modelo: <span className="font-medium text-slate-700">{analisis.modelo_usado || "—"}</span></span>
                      <span className="flex items-center gap-2 text-slate-500">
                        Confianza:
                        <select className="field-sm" value={confianza} onChange={(e) => setConfianza(e.target.value)}>
                          <option value="alta">alta</option>
                          <option value="media">media</option>
                          <option value="baja">baja</option>
                        </select>
                        <Badge tone={confianzaTone(confianza)}>{confianza}</Badge>
                      </span>
                    </div>
                  </Card>

                  {/* Capa 1 */}
                  <Card>
                    <CardBody>
                      <div className="mb-3 flex items-center justify-between">
                        <h3 className="font-semibold text-slate-900">Capa 1 · Identificación de temas éticos</h3>
                        <button onClick={() => setTemas([...temas, { ...TEMA_VACIO }])} className="text-sm font-medium text-accent-600 hover:text-accent-700">
                          + Añadir tema
                        </button>
                      </div>
                      {temas.length === 0 ? (
                        <p className="text-sm text-slate-500">Sin temas detectados.</p>
                      ) : (
                        <div className="space-y-3">
                          {temas.map((t, i) => (
                            <div key={i} className="rounded-lg border border-slate-200 p-3">
                              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                                <input className="field-sm font-medium" placeholder="Tema ético" value={t.tema_etico} onChange={(e) => setTema(i, "tema_etico", e.target.value)} />
                                <input className="field-sm" placeholder="Actor afectado" value={t.actor_afectado ?? ""} onChange={(e) => setTema(i, "actor_afectado", e.target.value)} />
                                <input className="field-sm" placeholder="Tipo de daño" value={t.tipo_dano ?? ""} onChange={(e) => setTema(i, "tipo_dano", e.target.value)} />
                                <textarea className="field-sm sm:col-span-2" rows={2} placeholder="Norma tensionada (norma + artículo concreto)" value={t.norma_tensionada_texto ?? ""} onChange={(e) => setTema(i, "norma_tensionada_texto", e.target.value)} />
                              </div>
                              <textarea className="field-sm mt-2 w-full" rows={2} placeholder="Evidencia" value={t.evidencia ?? ""} onChange={(e) => setTema(i, "evidencia", e.target.value)} />
                              {t.citas.length > 0 && (
                                <div className="mt-2 rounded-md bg-slate-50 p-2 text-xs text-slate-500">
                                  <span className="font-semibold text-slate-600">Citas normativas</span>
                                  <ul className="mt-1 ml-4 list-disc space-y-0.5">
                                    {t.citas.map((c, k) => (
                                      <li key={k}>{c.texto_citado}{c.chunk_id ? "" : " (sin respaldo verificado)"}</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              <button onClick={() => setTemas(temas.filter((_, k) => k !== i))} className="mt-2 text-xs font-medium text-red-500 hover:text-red-600">
                                Quitar tema
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardBody>
                  </Card>

                  {/* Capa 2 */}
                  <Card>
                    <details open>
                      <summary className="cursor-pointer px-5 py-3 font-semibold text-slate-900">Capa 2 · Análisis</summary>
                      <div className="space-y-3 px-5 pb-5 text-sm">
                        <Bloque titulo="Mapa de stakeholders">
                          {(c2?.mapa_stakeholders ?? []).map((s, i) => (<li key={i}><b>{s.stakeholder}</b>: {s.interes} {s.impacto && `(impacto: ${s.impacto})`}</li>))}
                        </Bloque>
                        <Bloque titulo="Tensiones de valores">
                          {(c2?.tensiones_de_valores ?? []).map((tv, i) => (<li key={i}>{tv.valor_a} ↔ {tv.valor_b}: {tv.descripcion}</li>))}
                        </Bloque>
                      </div>
                    </details>
                  </Card>

                  {/* Capa 3 */}
                  <Card>
                    <details open>
                      <summary className="cursor-pointer px-5 py-3 font-semibold text-slate-900">Capa 3 · Deliberación</summary>
                      <div className="space-y-3 px-5 pb-5 text-sm">
                        <Bloque titulo="Opciones de tratamiento">
                          {(c3?.opciones_tratamiento ?? []).map((o, i) => (<li key={i}><b>{o.decision}</b>: {o.justificacion}</li>))}
                        </Bloque>
                        <Bloque titulo="Reformulaciones propuestas">
                          {(c3?.reformulaciones_propuestas ?? []).map((r, i) => (<li key={i}>“{r.texto_propuesto}” — {r.como_reduce_conflicto}</li>))}
                        </Bloque>
                        <Bloque titulo="Requisitos derivados propuestos">
                          {(c3?.requisitos_derivados_propuestos ?? []).map((d, i) => (<li key={i}><b>{d.nombre}</b>: {d.descripcion}</li>))}
                        </Bloque>
                        <Bloque titulo="Preguntas deliberativas">
                          {(c3?.preguntas_deliberativas ?? []).map((q, i) => (<li key={i}>{q}</li>))}
                        </Bloque>
                      </div>
                    </details>
                  </Card>

                  {/* Limitaciones + guardar */}
                  <Card>
                    <CardBody>
                      <label className={labelCls}>Limitaciones</label>
                      <textarea className="field mt-1" rows={2} value={limitaciones} onChange={(e) => setLimitaciones(e.target.value)} />
                      <button onClick={onGuardarAnalisis} className={`${btnDark} mt-3`}>Guardar cambios del análisis</button>
                    </CardBody>
                  </Card>

                  {/* Tratamiento */}
                  <Card>
                    <CardBody>
                      <h3 className="mb-3 font-semibold text-slate-900">Tratamiento (Fase 3)</h3>
                      <div className="flex items-center gap-2">
                        <label className="text-sm text-slate-600">Decisión:</label>
                        <select className="field-sm" value={decision} onChange={(e) => setDecision(e.target.value as Decision)}>
                          <option value="aceptar">Aceptar</option>
                          <option value="reformular">Reformular (crea versión nueva)</option>
                          <option value="mitigar">Mitigar (crea derivados)</option>
                          <option value="eliminar">Eliminar (excluye del ranking)</option>
                        </select>
                      </div>

                      {decision === "reformular" && (
                        <div className="mt-3 space-y-2">
                          <input className="field" placeholder="Nuevo nombre del requisito" value={nuevoNombre} onChange={(e) => setNuevoNombre(e.target.value)} />
                          <textarea className="field" rows={2} placeholder="Nueva descripción" value={nuevaDescripcion} onChange={(e) => setNuevaDescripcion(e.target.value)} />
                        </div>
                      )}
                      {decision === "mitigar" && (
                        <div className="mt-3 space-y-2">
                          {derivados.map((d, i) => (
                            <div key={i} className="flex gap-2">
                              <input className="field flex-1" placeholder="Nombre del derivado" value={d.nombre} onChange={(e) => setDerivados(derivados.map((x, k) => (k === i ? { ...x, nombre: e.target.value } : x)))} />
                              <button onClick={() => setDerivados(derivados.filter((_, k) => k !== i))} className="text-sm text-red-500 hover:text-red-600">quitar</button>
                            </div>
                          ))}
                          <button onClick={() => setDerivados([...derivados, { nombre: "", descripcion: "" }])} className="text-sm font-medium text-accent-600 hover:text-accent-700">+ Añadir derivado</button>
                        </div>
                      )}

                      <textarea className="field mt-3" rows={2} placeholder="Justificación de la decisión" value={justificacion} onChange={(e) => setJustificacion(e.target.value)} />
                      <button onClick={onTratar} className={`${btnPrimary} mt-2`}>Registrar tratamiento</button>
                    </CardBody>
                  </Card>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

function Bloque({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  const items = Array.isArray(children) ? children : [children];
  if (items.length === 0) return null;
  return (
    <div>
      <div className="font-medium text-slate-700">{titulo}</div>
      <ul className="ml-4 list-disc text-slate-600">{children}</ul>
    </div>
  );
}
