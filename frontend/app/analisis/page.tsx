"use client";

// Fases 2-3 — Análisis ético (LLM + RAG) y tratamiento.
// El LLM identifica, analiza y propone; el humano edita y decide. Re-análisis manual.

import { useEffect, useState } from "react";
import {
  Requisito,
  Analisis,
  Tema,
  Decision,
  Dimension,
  TipoDimension,
  ChatMessage,
  listarRequisitos,
  analizarRequisito,
  obtenerAnalisis,
  editarAnalisis,
  crearTratamiento,
  listarDimensiones,
  editarDimension,
  eliminarDimension,
  chatRequisito,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import {
  Card,
  CardBody,
  PageHeader,
  Badge,
  Dot,
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

  // Dimensiones éticas detectadas por la IA para este requisito (editables).
  const [dimsEticas, setDimsEticas] = useState<Dimension[]>([]);

  // Chat deliberativo con el asistente sobre el requisito.
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatCargando, setChatCargando] = useState(false);

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
    setChat([]);
    setChatInput("");
    obtenerAnalisis(selId).then(cargarAnalisis).catch((e) => setError(e.message));
    cargarDimsEticas();
  }, [selId]);

  // Dimensiones éticas = las restringidas y aplicables a este requisito.
  function cargarDimsEticas() {
    if (!proyectoId || !selId) return setDimsEticas([]);
    listarDimensiones(proyectoId)
      .then((ds) =>
        setDimsEticas(
          ds.filter(
            (d) =>
              (d.tipo === "valor_etico" || d.tipo === "riesgo_etico") &&
              (d.requisitos_aplica ?? []).includes(selId),
          ),
        ),
      )
      .catch((e) => setError(e.message));
  }

  async function onEditarDimEtica(id: string, cambios: Partial<Dimension>) {
    setDimsEticas(dimsEticas.map((d) => (d.id === id ? { ...d, ...cambios } : d)));
    try {
      await editarDimension(id, cambios as any);
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function onQuitarDimEtica(id: string) {
    if (!confirm("¿Quitar esta dimensión ética? Se borrará del proyecto y sus evaluaciones.")) return;
    try {
      await eliminarDimension(id);
      setDimsEticas(dimsEticas.filter((d) => d.id !== id));
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function onEnviarChat() {
    const texto = chatInput.trim();
    if (!texto || !selId) return;
    const nuevos: ChatMessage[] = [...chat, { role: "user", content: texto }];
    setChat(nuevos);
    setChatInput("");
    setChatCargando(true);
    try {
      const { reply } = await chatRequisito(selId, nuevos);
      setChat([...nuevos, { role: "assistant", content: reply }]);
    } catch (e: any) {
      setError(e.message);
      setChat(nuevos); // conserva lo enviado; el usuario puede reintentar
    } finally {
      setChatCargando(false);
    }
  }

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
      cargarDimsEticas();
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
                        <div className="space-y-4">
                          {temas.map((t, i) => {
                            const citasReales = t.citas.filter((c) => (c.texto_citado ?? "").trim());
                            return (
                            <div key={i} className="overflow-hidden rounded-xl border border-slate-200 border-l-4 border-l-accent-400 bg-slate-50/40">
                              <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2">
                                <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent-100 text-[11px] font-bold text-accent-700">{i + 1}</span>
                                  Tema ético
                                </span>
                                <button onClick={() => setTemas(temas.filter((_, k) => k !== i))} className="text-xs font-medium text-slate-400 hover:text-red-600">
                                  Quitar
                                </button>
                              </div>
                              <div className="grid grid-cols-1 gap-4 p-4 sm:grid-cols-2">
                                <Campo label="Tema" className="sm:col-span-2">
                                  <input className="field font-medium" placeholder="p. ej. Falta de transparencia" value={t.tema_etico} onChange={(e) => setTema(i, "tema_etico", e.target.value)} />
                                </Campo>
                                <Campo label="Actor afectado">
                                  <input className="field" placeholder="p. ej. Personas postulantes" value={t.actor_afectado ?? ""} onChange={(e) => setTema(i, "actor_afectado", e.target.value)} />
                                </Campo>
                                <Campo label="Tipo de daño">
                                  <input className="field" placeholder="p. ej. exclusión injusta" value={t.tipo_dano ?? ""} onChange={(e) => setTema(i, "tipo_dano", e.target.value)} />
                                </Campo>
                                <Campo label="Norma tensionada (norma + artículo)" className="sm:col-span-2">
                                  <textarea className="field resize-y" rows={2} placeholder="p. ej. EU AI Act, Anexo III(4)" value={t.norma_tensionada_texto ?? ""} onChange={(e) => setTema(i, "norma_tensionada_texto", e.target.value)} />
                                </Campo>
                                <Campo label="Evidencia" className="sm:col-span-2">
                                  <textarea className="field resize-y" rows={3} placeholder="Por qué se detecta este tema" value={t.evidencia ?? ""} onChange={(e) => setTema(i, "evidencia", e.target.value)} />
                                </Campo>
                                <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm sm:col-span-2">
                                  <div className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                                    <span>📎 Citas normativas</span>
                                    <span className="font-normal normal-case text-slate-400">respaldo del RAG</span>
                                  </div>
                                  {citasReales.length > 0 ? (
                                    <ul className="space-y-1.5">
                                      {citasReales.map((c, k) => (
                                        <li key={k} className="flex gap-2 text-slate-600">
                                          <span className="text-accent-500">›</span>
                                          <span>
                                            {c.texto_citado}
                                            {c.chunk_id ? (
                                              <Badge tone="green">verificada</Badge>
                                            ) : (
                                              <span className="ml-1 text-xs text-amber-600">(sin respaldo verificado)</span>
                                            )}
                                          </span>
                                        </li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p className="text-xs text-slate-400">
                                      Sin citas recuperadas. Ingresa el corpus normativo y un proveedor de
                                      embeddings activo para que el RAG cite artículos concretos.
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                            );
                          })}
                        </div>
                      )}
                    </CardBody>
                  </Card>

                  {/* Dimensiones éticas detectadas (Fase 4 asistida) */}
                  <Card>
                    <CardBody>
                      <h3 className="font-semibold text-slate-900">Dimensiones éticas detectadas</h3>
                      <p className="mt-0.5 text-xs text-slate-500">
                        La IA las deriva de los temas de este requisito. Edítalas: define si es
                        valor ético (+) o riesgo ético (−) y su peso. Solo aplican a este requisito;
                        en la evaluación, los demás requisitos quedan en 0 para estas columnas.
                      </p>
                      {dimsEticas.length === 0 ? (
                        <p className="mt-3 text-sm text-slate-500">
                          Sin dimensiones éticas para este requisito. Se generan al analizar con IA.
                        </p>
                      ) : (
                        <div className="mt-3 space-y-2">
                          {dimsEticas.map((d) => (
                            <div key={d.id} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-3 sm:grid-cols-[1fr_150px_90px_auto] sm:items-end">
                              <Campo label="Nombre">
                                <input
                                  className="field-sm w-full"
                                  value={d.nombre}
                                  onChange={(e) => setDimsEticas(dimsEticas.map((x) => (x.id === d.id ? { ...x, nombre: e.target.value } : x)))}
                                  onBlur={(e) => onEditarDimEtica(d.id, { nombre: e.target.value })}
                                />
                              </Campo>
                              <Campo label="Tipo">
                                <select
                                  className="field-sm w-full"
                                  value={d.tipo}
                                  onChange={(e) => onEditarDimEtica(d.id, { tipo: e.target.value as TipoDimension })}
                                >
                                  <option value="valor_etico">Valor ético (+)</option>
                                  <option value="riesgo_etico">Riesgo ético (−)</option>
                                </select>
                              </Campo>
                              <Campo label="Peso">
                                <input
                                  type="number"
                                  min={1}
                                  max={5}
                                  className="field-sm w-full text-center"
                                  value={d.peso ?? 3}
                                  onChange={(e) => setDimsEticas(dimsEticas.map((x) => (x.id === d.id ? { ...x, peso: Number(e.target.value) } : x)))}
                                  onBlur={(e) => onEditarDimEtica(d.id, { peso: Number(e.target.value) })}
                                />
                              </Campo>
                              <button onClick={() => onQuitarDimEtica(d.id)} className="pb-2 text-xs font-medium text-red-500 hover:text-red-600">
                                Quitar
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

                  {/* Chat deliberativo con el asistente */}
                  <Card>
                    <CardBody>
                      <h3 className="font-semibold text-slate-900">Conversar con el equipo</h3>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Discute este requisito y su análisis con el asistente de ética. Acompaña la
                        deliberación; no decide por el equipo.
                      </p>

                      <div className="mt-3 max-h-80 space-y-3 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50/60 p-3">
                        {chat.length === 0 ? (
                          <p className="py-6 text-center text-sm text-slate-400">
                            Escribe una pregunta para empezar la conversación.
                          </p>
                        ) : (
                          chat.map((m, i) => (
                            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                              <div
                                className={
                                  "max-w-[80%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm " +
                                  (m.role === "user"
                                    ? "bg-accent-600 text-white"
                                    : "border border-slate-200 bg-white text-slate-700")
                                }
                              >
                                {m.content}
                              </div>
                            </div>
                          ))
                        )}
                        {chatCargando && (
                          <div className="flex justify-start">
                            <div className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-400">
                              escribiendo…
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="mt-3 flex gap-2">
                        <input
                          className="field flex-1"
                          placeholder="Escribe tu mensaje…"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                              e.preventDefault();
                              onEnviarChat();
                            }
                          }}
                        />
                        <button onClick={onEnviarChat} disabled={chatCargando || !chatInput.trim()} className={btnPrimary}>
                          Enviar
                        </button>
                      </div>
                    </CardBody>
                  </Card>

                  {/* Limitaciones + confianza + guardar */}
                  <Card>
                    <CardBody>
                      <div className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_auto] sm:items-start">
                        <div>
                          <label className={labelCls}>Limitaciones</label>
                          <textarea className="field mt-1 resize-y" rows={2} value={limitaciones} onChange={(e) => setLimitaciones(e.target.value)} />
                        </div>
                        <div>
                          <label className={labelCls}>Confianza</label>
                          <div className="mt-1 flex items-center gap-2">
                            <Dot tone={confianzaTone(confianza)} />
                            <select className="field-sm" value={confianza} onChange={(e) => setConfianza(e.target.value)}>
                              <option value="alta">alta</option>
                              <option value="media">media</option>
                              <option value="baja">baja</option>
                            </select>
                          </div>
                        </div>
                      </div>
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

function Campo({
  label,
  className = "",
  children,
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={className}>
      <label className="mb-1 block text-xs font-medium text-slate-500">{label}</label>
      {children}
    </div>
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
