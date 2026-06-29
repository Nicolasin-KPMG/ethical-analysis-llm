"use client";

// Dashboard del proyecto: estado de los requisitos, banderas y métricas.

import { useEffect, useState } from "react";
import Link from "next/link";
import { Requisito, listarRequisitos } from "../lib/api";
import { useProyecto } from "../components/ProyectoContext";
import {
  PageHeader,
  StatCard,
  Card,
  Table,
  Badge,
  Dot,
  EmptyState,
  th,
  td,
} from "../components/ui";
import { tipoBadge, estadoBadge, banderaEstado } from "../lib/estado";

export default function Page() {
  const { proyectoId } = useProyecto();
  const [reqs, setReqs] = useState<Requisito[]>([]);

  useEffect(() => {
    if (!proyectoId) return setReqs([]);
    listarRequisitos(proyectoId).then(setReqs).catch(() => setReqs([]));
  }, [proyectoId]);

  const vigentes = reqs.filter((r) => r.es_vigente !== false && r.estado !== "eliminado");
  const tratados = reqs.filter((r) => r.estado === "mitigado" || r.estado === "reformulado");
  const aceptados = reqs.filter((r) => r.estado === "aceptado");
  const pendientes = vigentes.filter((r) => r.estado === "pendiente_de_analisis");

  return (
    <>
      <PageHeader
        eyebrow="Dashboard"
        title="Dashboard del proyecto"
        subtitle="Estado de los requisitos, bandera ética y avance del proceso de 8 fases."
      />

      {/* Métricas */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Requisitos" value={reqs.length} hint="registrados" />
        <StatCard label="Pendientes" value={pendientes.length} hint="por analizar" accent="slate" />
        <StatCard label="Tratados" value={tratados.length} hint="mitigados / reformulados" accent="amber" />
        <StatCard label="Aceptados" value={aceptados.length} hint="decisión tomada" accent="green" />
      </div>

      {/* Leyenda */}
      <Card className="mb-6">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 px-5 py-3 text-sm text-slate-600">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Bandera ética
          </span>
          <span className="flex items-center gap-2"><Dot tone="slate" /> Pendiente</span>
          <span className="flex items-center gap-2"><Dot tone="green" /> Aceptado</span>
          <span className="flex items-center gap-2"><Dot tone="amber" /> Tratado</span>
          <span className="flex items-center gap-2"><Dot tone="ink" /> Eliminado</span>
        </div>
      </Card>

      {reqs.length === 0 ? (
        <EmptyState>
          Aún no hay requisitos.{" "}
          <Link href="/registro" className="font-medium text-accent-600 hover:underline">
            Registra el primero
          </Link>
          .
        </EmptyState>
      ) : (
        <Table
          head={
            <tr>
              <th className={th}>Código</th>
              <th className={th}>Requisito</th>
              <th className={th}>Tipo</th>
              <th className={th}>Stakeholder</th>
              <th className={th}>Estado</th>
              <th className={`${th} text-center`}>Ética</th>
            </tr>
          }
        >
          {reqs.map((r) => {
            const tb = tipoBadge(r.tipo);
            const eb = estadoBadge(r.estado);
            const bn = banderaEstado(r.estado);
            const archivado = r.es_vigente === false || r.estado === "eliminado";
            return (
              <tr key={r.id} className={"hover:bg-slate-50/60 " + (archivado ? "opacity-50" : "")}>
                <td className={`${td}`}>
                  <Link
                    href="/analisis"
                    className="font-mono text-xs font-medium text-accent-600 hover:underline"
                  >
                    {r.codigo || "—"}
                  </Link>
                </td>
                <td className={`${td} font-medium text-slate-800`}>{r.nombre}</td>
                <td className={td}>
                  <Badge tone={tb.tone}>{tb.label}</Badge>
                </td>
                <td className={`${td} text-slate-600`}>{r.stakeholder || "—"}</td>
                <td className={td}>
                  <Badge tone={eb.tone}>{eb.label}</Badge>
                </td>
                <td className={`${td} text-center`}>
                  <span title={bn.label}>
                    <Dot tone={bn.tone} />
                  </span>
                </td>
              </tr>
            );
          })}
        </Table>
      )}
    </>
  );
}
