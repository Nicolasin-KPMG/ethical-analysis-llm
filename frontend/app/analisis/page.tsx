"use client";

// Fases 2-3 — Análisis ético (LLM + RAG) y tratamiento.
// El LLM identifica, analiza y propone; el humano edita y decide. Re-análisis manual.

import { useEffect, useRef, useState } from "react";
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
  cribarProyecto,
  obtenerAnalisis,
  editarAnalisis,
  crearTratamiento,
  listarDimensiones,
  editarDimension,
  eliminarDimension,
  chatRequisito,
} from "../../lib/api";
import { useProyecto } from "../../components/ProyectoContext";
import { useToast } from "../../components/Toast";
import ProgresoAnalisis from "../../components/ProgresoAnalisis";
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


export default function Page() {
  const { proyectoId } = useProyecto();
  const [requisitos, setRequisitos] = useState<Requisito[]>([]);
  const [selId, setSelId] = useState<string | null>(null);

  const [analisis, setAnalisis] = useState<Analisis | null>(null);
  const [temas, setTemas] = useState<Tema[]>([]);
  const [confianza, setConfianza] = useState("media");
  const [limitaciones, setLimitaciones] = useState("");

  // Ids de requisitos que se están analizando ahora mismo. Al cambiar de
  // requisito, el análisis en curso sigue "pegado" a su requisito: puedes ver
  // los demás y el resultado aparece cuando vuelves al que se estaba analizando.
  const [analizandoIds, setAnalizandoIds] = useState<string[]>([]);
  const [cribando, setCribando] = useState(false);
  const [tratando, setTratando] = useState(false);
  const [verDescartados, setVerDescartados] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

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

  // Referencia siempre-actual del requisito visible, para decidir al terminar un
  // análisis si el usuario sigue mirándolo (y aplicar el resultado) o no.
  const selIdRef = useRef(selId);
  useEffect(() => {
    selIdRef.current = selId;
  }, [selId]);

  useEffect(() => {
    if (!proyectoId) return setRequisitos([]);
    listarRequisitos(proyectoId)
      .then((rs) => setRequisitos(rs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado")))
      .catch((e) => setError(e.message));
  }, [proyectoId]);

  useEffect(() => {
    if (!selId) return;
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

  async function onCribar() {
    if (!proyectoId) return;
    setCribando(true);
    setError(null);
    try {
      const rs = await cribarProyecto(proyectoId);
      setRequisitos(rs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado"));
      const n = rs.filter((r) => r.riesgo_preliminar).length;
      toast.exito(`Pre-análisis listo: ${n} requisito(s) con posible riesgo ético.`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setCribando(false);
    }
  }

  async function onAnalizar() {
    const id = selId;
    if (!id) return;
    setAnalizandoIds((prev) => (prev.includes(id) ? prev : [...prev, id]));
    setError(null);
    try {
      const resultado = await analizarRequisito(id);
      // Solo pintamos el resultado si el usuario sigue viendo ESTE requisito.
      if (selIdRef.current === id) {
        cargarAnalisis(resultado);
        cargarDimsEticas();
        toast.exito("Análisis generado. Revísalo y edítalo libremente.");
      }
      // La lista (estado/puntos) se refresca siempre.
      listarRequisitos(proyectoId)
        .then((rs) => setRequisitos(rs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado")))
        .catch(() => {});
    } catch (e: any) {
      if (selIdRef.current === id) setError(e.message);
    } finally {
      setAnalizandoIds((prev) => prev.filter((x) => x !== id));
    }
  }
  async function onGuardarAnalisis() {
    if (!selId) return;
    setError(null);
    try {
      cargarAnalisis(await editarAnalisis(selId, { nivel_confianza: confianza, limitaciones, temas }));
      toast.exito("Cambios del análisis guardados.");
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function onTratar() {
    if (!selId) return;
    setError(null);
    setTratando(true);
    if (decision === "mitigar") toast.info("Registrando y analizando los controles…");
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
        toast.exito("Tratamiento registrado: reformulado (nueva versión creada).");
        setSelId(res.nuevo_requisito_id);
      } else if (decision === "mitigar") {
        toast.exito(`Tratamiento registrado: mitigado (${res.derivados_ids.length} derivado/s).`);
      } else if (decision === "eliminar") {
        toast.exito("Tratamiento registrado: eliminado.");
        setSelId(null);
      } else {
        toast.exito("Tratamiento registrado: aceptado.");
      }
    } catch (e: any) {
      setError(e.message);
      toast.error("No se pudo registrar el tratamiento.");
    } finally {
      setTratando(false);
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
        actions={
          <button onClick={onCribar} disabled={cribando || requisitos.length === 0} className={btnDark}>
            {cribando ? "Cribando…" : "Ejecutar pre-análisis"}
          </button>
        }
      />

      {error && <Alert>{error}</Alert>}

      {cribando && (
        <div className="mb-5">
          <ProgresoAnalisis
            titulo="Pre-análisis (cribado)"
            subtitulo="Revisando todos los requisitos para detectar cuáles podrían tener riesgo ético."
            etapas={["Leyendo los requisitos…", "Clasificando riesgo ético…", "Marcando los que entran al análisis…"]}
            duracionEstimadaMs={12000}
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-[260px_1fr]">
        {/* Lista de requisitos */}
        <Card className="h-fit">
          <div className="border-b border-slate-100 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Requisitos vigentes
          </div>
          {requisitos.length === 0 ? (
            <p className="px-4 py-4 text-sm text-slate-500">No hay requisitos.</p>
          ) : (
            (() => {
              // Tras el pre-análisis: los con riesgo (y los aún no cribados) entran;
              // los descartados (riesgo_preliminar === false) se colapsan aparte.
              const entran = requisitos.filter((r) => r.riesgo_preliminar !== false);
              const descartados = requisitos.filter((r) => r.riesgo_preliminar === false);
              const cribadoHecho = requisitos.some((r) => r.riesgo_preliminar != null);

              const Item = ({ r, mute = false }: { r: Requisito; mute?: boolean }) => (
                <li key={r.id}>
                  <button
                    onClick={() => setSelId(r.id)}
                    title={r.motivo_preliminar ?? undefined}
                    className={
                      "flex w-full items-start gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition " +
                      (selId === r.id ? "bg-accent-50 text-accent-800" : "hover:bg-slate-50")
                    }
                  >
                    <span className="mt-1.5">
                      {r.riesgo_preliminar === true ? (
                        <Dot tone="red" />
                      ) : r.riesgo_preliminar === false ? (
                        <Dot tone="slate" />
                      ) : (
                        <span className="inline-block h-2.5 w-2.5 rounded-full border border-slate-300" />
                      )}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className={"block font-medium " + (mute ? "text-slate-500" : "text-slate-800")}>
                        {r.nombre}
                      </span>
                      <span className="block font-mono text-xs text-slate-400">
                        {r.codigo} · {r.estado}
                      </span>
                    </span>
                    {analizandoIds.includes(r.id) && (
                      <span
                        title="Analizando…"
                        className="mt-1 h-3.5 w-3.5 flex-shrink-0 animate-spin rounded-full border-2 border-slate-200 border-t-accent-500"
                      />
                    )}
                  </button>
                </li>
              );

              return (
                <div className="max-h-[70vh] overflow-y-auto p-2">
                  {cribadoHecho && (
                    <div className="px-2 pb-1 pt-1 text-[10px] font-semibold uppercase tracking-wider text-red-500">
                      Con posible riesgo ético ({entran.filter((r) => r.riesgo_preliminar === true).length})
                    </div>
                  )}
                  <ul className="space-y-0.5">
                    {entran.map((r) => (
                      <Item key={r.id} r={r} />
                    ))}
                  </ul>

                  {descartados.length > 0 && (
                    <div className="mt-2 border-t border-slate-100 pt-2">
                      <button
                        onClick={() => setVerDescartados((v) => !v)}
                        className="flex w-full items-center justify-between px-2 py-1 text-xs font-medium text-slate-400 hover:text-slate-600"
                      >
                        <span>Sin riesgo aparente ({descartados.length})</span>
                        <span>{verDescartados ? "▲" : "▼"}</span>
                      </button>
                      {verDescartados && (
                        <ul className="space-y-0.5 opacity-70">
                          {descartados.map((r) => (
                            <Item key={r.id} r={r} mute />
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              );
            })()
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
                      {seleccionado.riesgo_preliminar === true && (
                        <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-700">
                          <Dot tone="red" />
                          <span>
                            <span className="font-medium">Pre-análisis: posible riesgo ético.</span>{" "}
                            {seleccionado.motivo_preliminar}
                          </span>
                        </div>
                      )}
                      {seleccionado.riesgo_preliminar === false && (
                        <p className="mt-3 text-xs text-slate-400">
                          Pre-análisis: sin riesgo ético aparente. Puedes analizarlo igualmente si lo consideras necesario.
                        </p>
                      )}
                    </div>
                    <button
                      onClick={onAnalizar}
                      disabled={!!selId && analizandoIds.includes(selId)}
                      className={btnPrimary}
                    >
                      {selId && analizandoIds.includes(selId)
                        ? "Analizando…"
                        : analisis
                          ? "Re-analizar con IA"
                          : "Analizar con IA"}
                    </button>
                  </div>
                </CardBody>
              </Card>

              {selId && analizandoIds.includes(selId) ? (
                <ProgresoAnalisis
                  etapas={[
                    "Primera pasada del LLM (temas preliminares)…",
                    "Recuperando normativa relevante (RAG)…",
                    "Analizando las tres capas…",
                    "Guardando el resultado…",
                  ]}
                />
              ) : !analisis ? (
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
                                    <ul className="space-y-3">
                                      {citasReales.map((c, k) => {
                                        const fuente = [c.documento, c.referencia]
                                          .filter((x) => (x ?? "").trim())
                                          .join(" · ");
                                        return (
                                          <li key={k} className="flex gap-2 text-slate-600">
                                            <span className="mt-0.5 text-accent-500">›</span>
                                            <div className="min-w-0 flex-1">
                                              <p className="italic">“{c.texto_citado}”</p>
                                              <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
                                                {fuente ? (
                                                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-600">
                                                    {fuente}
                                                    {c.jurisdiccion ? ` (${c.jurisdiccion})` : ""}
                                                  </span>
                                                ) : (
                                                  <span className="text-xs text-slate-400">Fuente no identificada</span>
                                                )}
                                                {c.chunk_id ? (
                                                  <Badge tone="green">verificada</Badge>
                                                ) : (
                                                  <span className="text-xs text-amber-600">sin respaldo verificado</span>
                                                )}
                                              </div>
                                            </div>
                                          </li>
                                        );
                                      })}
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

                  {/* Limitaciones del análisis + guardar */}
                  <Card>
                    <CardBody>
                      <label className={labelCls}>Limitaciones del análisis</label>
                      <textarea
                        className="field mt-1 resize-y"
                        rows={3}
                        placeholder="Salvedades del análisis: qué no se pudo evaluar bien, supuestos, advertencias…"
                        value={limitaciones}
                        onChange={(e) => setLimitaciones(e.target.value)}
                      />
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
                      <button onClick={onTratar} disabled={tratando} className={`${btnPrimary} mt-2`}>
                        {tratando
                          ? decision === "mitigar"
                            ? "Analizando controles…"
                            : "Procesando…"
                          : "Registrar tratamiento"}
                      </button>
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
