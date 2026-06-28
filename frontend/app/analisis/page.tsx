"use client";

// Fases 2-3 — Análisis ético (LLM + RAG) y tratamiento.
// Izquierda: requisitos vigentes del proyecto. Derecha: análisis del requisito
// seleccionado en las TRES CAPAS (editable la capa 1), más el panel de decisión
// de tratamiento (aceptar / reformular / mitigar / eliminar).
//
// El re-análisis es siempre una acción explícita del usuario (botón), nunca
// automática, para evitar bucles. El humano edita y decide; el LLM solo propone.

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

  const [analizando, setAnalizando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  // Estado del panel de tratamiento.
  const [decision, setDecision] = useState<Decision>("aceptar");
  const [justificacion, setJustificacion] = useState("");
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevaDescripcion, setNuevaDescripcion] = useState("");
  const [derivados, setDerivados] = useState<{ nombre: string; descripcion: string }[]>([]);

  const seleccionado = requisitos.find((r) => r.id === selId) || null;

  useEffect(() => {
    if (!proyectoId) {
      setRequisitos([]);
      return;
    }
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
    // Prefills del tratamiento desde las propuestas del LLM (capa 3).
    const c3 = a?.capas_2_3?.capa_3_deliberacion;
    setNuevoNombre(c3?.reformulaciones_propuestas?.[0]?.texto_propuesto ?? "");
    setNuevaDescripcion("");
    setDerivados(
      (c3?.requisitos_derivados_propuestos ?? []).map((d) => ({
        nombre: d.nombre,
        descripcion: d.descripcion ?? "",
      })),
    );
    setDecision("aceptar");
    setJustificacion("");
  }

  async function onAnalizar() {
    if (!selId) return;
    setAnalizando(true);
    setError(null);
    setMsg(null);
    try {
      const a = await analizarRequisito(selId);
      cargarAnalisis(a);
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
      const a = await editarAnalisis(selId, {
        nivel_confianza: confianza,
        limitaciones,
        temas,
      });
      cargarAnalisis(a);
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
      // Refresca la lista (cambian estados/vigencia/derivados).
      const rs = await listarRequisitos(proyectoId);
      setRequisitos(rs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado"));
      if (decision === "reformular" && res.nuevo_requisito_id) {
        setMsg("Se creó una versión nueva (pendiente de re-análisis). La anterior quedó archivada.");
        setSelId(res.nuevo_requisito_id);
      } else if (decision === "mitigar") {
        setMsg(`Se crearon ${res.derivados_ids.length} requisito(s) derivado(s).`);
      } else if (decision === "eliminar") {
        setMsg("Requisito marcado como eliminado (excluido del ranking).");
        setSelId(null);
      } else {
        setMsg("Tratamiento registrado: aceptado.");
      }
    } catch (e: any) {
      setError(e.message);
    }
  }

  function setTema(i: number, campo: keyof Tema, valor: string) {
    setTemas(temas.map((t, k) => (k === i ? { ...t, [campo]: valor } : t)));
  }

  if (!proyectoId) {
    return (
      <main className="mx-auto max-w-6xl p-6">
        <p className="text-sm text-gray-500">Selecciona o crea un proyecto en la barra superior.</p>
      </main>
    );
  }

  const c2 = analisis?.capas_2_3?.capa_2_analisis;
  const c3 = analisis?.capas_2_3?.capa_3_deliberacion;

  return (
    <main className="mx-auto max-w-6xl p-6">
      <header className="mb-4">
        <h1 className="text-2xl font-bold">Fases 2-3 — Análisis ético y tratamiento</h1>
        <p className="text-sm text-gray-600">
          El LLM identifica, analiza y propone; tú editas y decides. El re-análisis es manual.
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}
      {msg && (
        <div className="mb-4 rounded border border-green-300 bg-green-50 p-3 text-sm text-green-700">{msg}</div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-[260px_1fr]">
        {/* Lista de requisitos */}
        <aside className="rounded-lg border bg-white p-3">
          <h2 className="mb-2 text-sm font-semibold text-gray-700">Requisitos vigentes</h2>
          {requisitos.length === 0 ? (
            <p className="text-sm text-gray-500">No hay requisitos.</p>
          ) : (
            <ul className="space-y-1">
              {requisitos.map((r) => (
                <li key={r.id}>
                  <button
                    onClick={() => setSelId(r.id)}
                    className={
                      "w-full rounded px-2 py-1.5 text-left text-sm " +
                      (selId === r.id ? "bg-blue-600 text-white" : "hover:bg-gray-100")
                    }
                  >
                    <div className="font-medium">{r.nombre}</div>
                    <div className={"text-xs " + (selId === r.id ? "text-blue-100" : "text-gray-400")}>
                      {r.codigo} · {r.estado}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* Panel del requisito seleccionado */}
        <section className="space-y-4">
          {!seleccionado ? (
            <p className="rounded-lg border bg-white p-4 text-sm text-gray-500">
              Selecciona un requisito para analizarlo.
            </p>
          ) : (
            <>
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="font-semibold">{seleccionado.nombre}</h2>
                    <p className="text-xs text-gray-500">
                      {seleccionado.codigo} · estado: {seleccionado.estado}
                      {seleccionado.version_anterior_id && " · (versión reformulada)"}
                      {seleccionado.origen_requisito_id && " · (requisito derivado)"}
                    </p>
                    {seleccionado.descripcion && (
                      <p className="mt-1 text-sm text-gray-700">{seleccionado.descripcion}</p>
                    )}
                  </div>
                  <button
                    onClick={onAnalizar}
                    disabled={analizando}
                    className="shrink-0 rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500 disabled:opacity-50"
                  >
                    {analizando ? "Analizando…" : analisis ? "Re-analizar con IA" : "Analizar con IA"}
                  </button>
                </div>
              </div>

              {!analisis ? (
                <p className="rounded-lg border bg-white p-4 text-sm text-gray-500">
                  Este requisito aún no tiene análisis. Pulsa “Analizar con IA”.
                </p>
              ) : (
                <>
                  {/* Metadatos del análisis */}
                  <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-white p-3 text-sm">
                    <span>
                      Origen: <b>{analisis.generado_por}</b>
                    </span>
                    <span>Modelo: {analisis.modelo_usado || "—"}</span>
                    <label className="flex items-center gap-1">
                      Confianza:
                      <select
                        className="rounded border px-2 py-1"
                        value={confianza}
                        onChange={(e) => setConfianza(e.target.value)}
                      >
                        <option value="alta">alta</option>
                        <option value="media">media</option>
                        <option value="baja">baja</option>
                      </select>
                    </label>
                  </div>

                  {/* CAPA 1 — Identificación (editable) */}
                  <div className="rounded-lg border bg-white p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="font-semibold">Capa 1 — Identificación de temas éticos</h3>
                      <button
                        onClick={() => setTemas([...temas, { ...TEMA_VACIO }])}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        + Añadir tema
                      </button>
                    </div>
                    {temas.length === 0 ? (
                      <p className="text-sm text-gray-500">Sin temas detectados.</p>
                    ) : (
                      <div className="space-y-3">
                        {temas.map((t, i) => (
                          <div key={i} className="rounded border p-3">
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                              <input
                                className="rounded border px-2 py-1 text-sm font-medium"
                                placeholder="Tema ético"
                                value={t.tema_etico}
                                onChange={(e) => setTema(i, "tema_etico", e.target.value)}
                              />
                              <input
                                className="rounded border px-2 py-1 text-sm"
                                placeholder="Actor afectado"
                                value={t.actor_afectado ?? ""}
                                onChange={(e) => setTema(i, "actor_afectado", e.target.value)}
                              />
                              <input
                                className="rounded border px-2 py-1 text-sm"
                                placeholder="Tipo de daño"
                                value={t.tipo_dano ?? ""}
                                onChange={(e) => setTema(i, "tipo_dano", e.target.value)}
                              />
                              <input
                                className="rounded border px-2 py-1 text-sm"
                                placeholder="Norma tensionada"
                                value={t.norma_tensionada_texto ?? ""}
                                onChange={(e) => setTema(i, "norma_tensionada_texto", e.target.value)}
                              />
                            </div>
                            <textarea
                              className="mt-2 w-full rounded border px-2 py-1 text-sm"
                              rows={2}
                              placeholder="Evidencia"
                              value={t.evidencia ?? ""}
                              onChange={(e) => setTema(i, "evidencia", e.target.value)}
                            />
                            {t.citas.length > 0 && (
                              <div className="mt-2 text-xs text-gray-500">
                                <b>Citas normativas:</b>
                                <ul className="ml-4 list-disc">
                                  {t.citas.map((c, k) => (
                                    <li key={k}>
                                      {c.texto_citado}
                                      {c.chunk_id ? "" : " (sin respaldo verificado)"}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            <button
                              onClick={() => setTemas(temas.filter((_, k) => k !== i))}
                              className="mt-2 text-xs text-red-600 hover:underline"
                            >
                              Quitar tema
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* CAPA 2 — Análisis (lectura) */}
                  <details className="rounded-lg border bg-white p-4" open>
                    <summary className="cursor-pointer font-semibold">Capa 2 — Análisis</summary>
                    <div className="mt-2 space-y-2 text-sm">
                      <Bloque titulo="Mapa de stakeholders">
                        {(c2?.mapa_stakeholders ?? []).map((s, i) => (
                          <li key={i}>
                            <b>{s.stakeholder}</b>: {s.interes} {s.impacto && `(impacto: ${s.impacto})`}
                          </li>
                        ))}
                      </Bloque>
                      <Bloque titulo="Tensiones de valores">
                        {(c2?.tensiones_de_valores ?? []).map((tv, i) => (
                          <li key={i}>
                            {tv.valor_a} ↔ {tv.valor_b}: {tv.descripcion}
                          </li>
                        ))}
                      </Bloque>
                    </div>
                  </details>

                  {/* CAPA 3 — Deliberación (lectura) */}
                  <details className="rounded-lg border bg-white p-4" open>
                    <summary className="cursor-pointer font-semibold">Capa 3 — Deliberación</summary>
                    <div className="mt-2 space-y-2 text-sm">
                      <Bloque titulo="Opciones de tratamiento">
                        {(c3?.opciones_tratamiento ?? []).map((o, i) => (
                          <li key={i}>
                            <b>{o.decision}</b>: {o.justificacion}
                          </li>
                        ))}
                      </Bloque>
                      <Bloque titulo="Reformulaciones propuestas">
                        {(c3?.reformulaciones_propuestas ?? []).map((r, i) => (
                          <li key={i}>
                            “{r.texto_propuesto}” — {r.como_reduce_conflicto}
                          </li>
                        ))}
                      </Bloque>
                      <Bloque titulo="Requisitos derivados propuestos">
                        {(c3?.requisitos_derivados_propuestos ?? []).map((d, i) => (
                          <li key={i}>
                            <b>{d.nombre}</b>: {d.descripcion}
                          </li>
                        ))}
                      </Bloque>
                      <Bloque titulo="Preguntas deliberativas">
                        {(c3?.preguntas_deliberativas ?? []).map((q, i) => (
                          <li key={i}>{q}</li>
                        ))}
                      </Bloque>
                    </div>
                  </details>

                  <div className="rounded-lg border bg-white p-4">
                    <label className="text-sm">
                      Limitaciones
                      <textarea
                        className="mt-1 w-full rounded border px-2 py-1 text-sm"
                        rows={2}
                        value={limitaciones}
                        onChange={(e) => setLimitaciones(e.target.value)}
                      />
                    </label>
                    <button
                      onClick={onGuardarAnalisis}
                      className="mt-2 rounded bg-gray-800 px-4 py-2 text-sm text-white hover:bg-gray-700"
                    >
                      Guardar cambios del análisis
                    </button>
                  </div>

                  {/* TRATAMIENTO (Fase 3) */}
                  <div className="rounded-lg border bg-white p-4">
                    <h3 className="mb-2 font-semibold">Tratamiento (Fase 3)</h3>
                    <div className="flex flex-wrap items-center gap-3">
                      <label className="text-sm">
                        Decisión:
                        <select
                          className="ml-2 rounded border px-2 py-1"
                          value={decision}
                          onChange={(e) => setDecision(e.target.value as Decision)}
                        >
                          <option value="aceptar">Aceptar</option>
                          <option value="reformular">Reformular (crea versión nueva)</option>
                          <option value="mitigar">Mitigar (crea derivados)</option>
                          <option value="eliminar">Eliminar (excluye del ranking)</option>
                        </select>
                      </label>
                    </div>

                    {decision === "reformular" && (
                      <div className="mt-3 space-y-2">
                        <input
                          className="w-full rounded border px-2 py-1 text-sm"
                          placeholder="Nuevo nombre del requisito"
                          value={nuevoNombre}
                          onChange={(e) => setNuevoNombre(e.target.value)}
                        />
                        <textarea
                          className="w-full rounded border px-2 py-1 text-sm"
                          rows={2}
                          placeholder="Nueva descripción"
                          value={nuevaDescripcion}
                          onChange={(e) => setNuevaDescripcion(e.target.value)}
                        />
                      </div>
                    )}

                    {decision === "mitigar" && (
                      <div className="mt-3 space-y-2">
                        {derivados.map((d, i) => (
                          <div key={i} className="flex gap-2">
                            <input
                              className="flex-1 rounded border px-2 py-1 text-sm"
                              placeholder="Nombre del derivado"
                              value={d.nombre}
                              onChange={(e) =>
                                setDerivados(derivados.map((x, k) => (k === i ? { ...x, nombre: e.target.value } : x)))
                              }
                            />
                            <button
                              onClick={() => setDerivados(derivados.filter((_, k) => k !== i))}
                              className="text-xs text-red-600 hover:underline"
                            >
                              quitar
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => setDerivados([...derivados, { nombre: "", descripcion: "" }])}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          + Añadir derivado
                        </button>
                      </div>
                    )}

                    <textarea
                      className="mt-3 w-full rounded border px-2 py-1 text-sm"
                      rows={2}
                      placeholder="Justificación de la decisión"
                      value={justificacion}
                      onChange={(e) => setJustificacion(e.target.value)}
                    />
                    <button
                      onClick={onTratar}
                      className="mt-2 rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500"
                    >
                      Registrar tratamiento
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </section>
      </div>
    </main>
  );
}

// Pequeño bloque con título y lista; oculta el título si no hay items.
function Bloque({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  const items = Array.isArray(children) ? children : [children];
  if (items.length === 0) return null;
  return (
    <div>
      <div className="font-medium text-gray-700">{titulo}</div>
      <ul className="ml-4 list-disc text-gray-600">{children}</ul>
    </div>
  );
}
