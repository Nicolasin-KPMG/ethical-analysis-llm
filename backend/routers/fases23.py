"""Endpoints de las Fases 2-3 (analisis etico y tratamiento).

- POST /requisitos/{id}/analizar     -> corre el analisis (LLM + RAG) y lo guarda.
- GET  /requisitos/{id}/analisis      -> ultimo analisis (para mostrar/editar).
- PUT  /requisitos/{id}/analisis      -> edicion humana del analisis.
- POST /requisitos/{id}/tratamiento   -> decision de tratamiento (Fase 3).

Reglas de negocio aplicadas (criticas, ver seccion 3 del contexto):
- Reformular crea una version NUEVA del requisito (version_anterior_id); la anterior
  queda es_vigente=false como historial; la nueva nace pendiente de re-analisis.
- Mitigar crea requisitos derivados (origen_requisito_id) y filas en relacion_requisito.
- Eliminar marca estado='eliminado' (no borra).
- El humano decide siempre; el re-analisis es una accion explicita (este endpoint).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Proyecto,
    Requisito,
    AnalisisEtico,
    TemaEticoDetectado,
    CitaNormativa,
    Tratamiento,
    RelacionRequisito,
)
from schemas import (
    AnalisisOut,
    AnalisisUpdate,
    TratamientoCreate,
    TratamientoOut,
    ChatRequest,
    ChatResponse,
)
from services.analysis import analizar_requisito
from services.bandera import bandera_de
from providers.llm import get_llm_provider

router = APIRouter(tags=["fases-2-3"])


@router.get("/proyectos/{proyecto_id}/banderas")
def banderas_proyecto(proyecto_id: uuid.UUID, db: Session = Depends(get_db)):
    """Bandera ética (derivada del análisis) de cada requisito del proyecto.

    La usa el dashboard para pintar el indicador de color por requisito.
    """
    if db.get(Proyecto, proyecto_id) is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    requisitos = db.query(Requisito).filter(Requisito.proyecto_id == proyecto_id).all()
    return [{"requisito_id": str(r.id), "bandera": bandera_de(db, r)} for r in requisitos]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _analisis_out(db: Session, analisis: AnalisisEtico) -> dict:
    """Arma el AnalisisOut: el analisis + sus temas (Capa 1) con citas."""
    temas = (
        db.query(TemaEticoDetectado)
        .filter(TemaEticoDetectado.analisis_id == analisis.id)
        .all()
    )
    temas_out = []
    for t in temas:
        citas = (
            db.query(CitaNormativa).filter(CitaNormativa.tema_id == t.id).all()
        )
        temas_out.append(
            {
                "id": t.id,
                "tema_etico": t.tema_etico,
                "actor_afectado": t.actor_afectado,
                "tipo_dano": t.tipo_dano,
                "norma_tensionada_texto": t.norma_tensionada_texto,
                "evidencia": t.evidencia,
                "citas": [
                    {"chunk_id": c.chunk_id, "texto_citado": c.texto_citado}
                    for c in citas
                ],
            }
        )
    return {
        "id": analisis.id,
        "requisito_id": analisis.requisito_id,
        "generado_por": analisis.generado_por,
        "modelo_usado": analisis.modelo_usado,
        "nivel_confianza": analisis.nivel_confianza,
        "limitaciones": analisis.limitaciones,
        "capas_2_3": analisis.capas_2_3,
        "creado_en": analisis.creado_en,
        "temas": temas_out,
    }


def _ultimo_analisis(db: Session, requisito_id: uuid.UUID) -> AnalisisEtico | None:
    return (
        db.query(AnalisisEtico)
        .filter(AnalisisEtico.requisito_id == requisito_id)
        .order_by(AnalisisEtico.creado_en.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Fase 2: analisis
# ---------------------------------------------------------------------------
@router.post("/requisitos/{requisito_id}/analizar", response_model=AnalisisOut)
def analizar(requisito_id: uuid.UUID, db: Session = Depends(get_db)):
    req = db.get(Requisito, requisito_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")
    # Solo se analizan requisitos vigentes y no eliminados (Fase 2).
    if not req.es_vigente or req.estado == "eliminado":
        raise HTTPException(
            status_code=400, detail="Solo se analizan requisitos vigentes y no eliminados"
        )
    try:
        analisis = analizar_requisito(db, requisito_id)
    except RuntimeError as e:
        # P.ej. falta ANTHROPIC_API_KEY: error claro para el cliente.
        raise HTTPException(status_code=502, detail=str(e))
    return _analisis_out(db, analisis)


@router.get("/requisitos/{requisito_id}/analisis", response_model=AnalisisOut)
def obtener_analisis(requisito_id: uuid.UUID, db: Session = Depends(get_db)):
    analisis = _ultimo_analisis(db, requisito_id)
    if analisis is None:
        raise HTTPException(status_code=404, detail="El requisito no tiene analisis")
    return _analisis_out(db, analisis)


@router.put("/requisitos/{requisito_id}/analisis", response_model=AnalisisOut)
def editar_analisis(
    requisito_id: uuid.UUID,
    payload: AnalisisUpdate,
    db: Session = Depends(get_db),
):
    """Edicion humana: el humano puede ajustar texto, confianza y los temas."""
    analisis = _ultimo_analisis(db, requisito_id)
    if analisis is None:
        raise HTTPException(status_code=404, detail="El requisito no tiene analisis")

    if payload.nivel_confianza is not None:
        analisis.nivel_confianza = payload.nivel_confianza
    if payload.limitaciones is not None:
        analisis.limitaciones = payload.limitaciones
    if payload.capas_2_3 is not None:
        analisis.capas_2_3 = payload.capas_2_3
    # Al editar, el analisis pasa a ser de autoria humana.
    analisis.generado_por = "humano"

    # Si se envian temas, reemplazan los actuales (con sus citas por cascade).
    if payload.temas is not None:
        db.query(TemaEticoDetectado).filter(
            TemaEticoDetectado.analisis_id == analisis.id
        ).delete()
        for t in payload.temas:
            fila = TemaEticoDetectado(
                analisis_id=analisis.id,
                tema_etico=t.tema_etico,
                actor_afectado=t.actor_afectado,
                tipo_dano=t.tipo_dano,
                norma_tensionada_texto=t.norma_tensionada_texto,
                evidencia=t.evidencia,
            )
            db.add(fila)
            db.flush()
            for cita in t.citas:
                chunk_id = uuid.UUID(cita.chunk_id) if cita.chunk_id else None
                db.add(
                    CitaNormativa(
                        tema_id=fila.id, chunk_id=chunk_id, texto_citado=cita.texto_citado
                    )
                )

    db.commit()
    db.refresh(analisis)
    return _analisis_out(db, analisis)


# ---------------------------------------------------------------------------
# Fase 3: tratamiento
# ---------------------------------------------------------------------------
@router.post("/requisitos/{requisito_id}/tratamiento", response_model=TratamientoOut)
def crear_tratamiento(
    requisito_id: uuid.UUID,
    payload: TratamientoCreate,
    db: Session = Depends(get_db),
):
    req = db.get(Requisito, requisito_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")

    nuevo_requisito_id = None
    derivados_ids: list[uuid.UUID] = []

    if payload.decision == "aceptar":
        req.estado = "aceptado"

    elif payload.decision == "eliminar":
        # No borra: marca el estado y queda fuera del ranking (regla 5).
        req.estado = "eliminado"

    elif payload.decision == "reformular":
        # Regla 1: nueva fila enlazada por version_anterior_id.
        if not payload.nuevo_nombre:
            raise HTTPException(
                status_code=400, detail="reformular requiere nuevo_nombre"
            )
        nueva = Requisito(
            proyecto_id=req.proyecto_id,
            codigo=req.codigo,
            nombre=payload.nuevo_nombre,
            descripcion=payload.nueva_descripcion,
            tipo=req.tipo,
            stakeholder=req.stakeholder,
            estado="pendiente_de_analisis",  # debe re-analizarse (Fase 2)
            es_vigente=True,                  # la nueva version es la vigente
            version_anterior_id=req.id,
        )
        db.add(nueva)
        db.flush()
        nuevo_requisito_id = nueva.id
        # La version anterior queda archivada como historial.
        req.es_vigente = False
        req.estado = "reformulado"

    elif payload.decision == "mitigar":
        # Regla 3: crea requisitos derivados enlazados al padre.
        if not payload.derivados:
            raise HTTPException(
                status_code=400, detail="mitigar requiere al menos un derivado"
            )
        for d in payload.derivados:
            derivado = Requisito(
                proyecto_id=req.proyecto_id,
                nombre=d.nombre,
                descripcion=d.descripcion,
                tipo="otro",
                estado="pendiente_de_analisis",
                es_vigente=True,
                origen_requisito_id=req.id,
            )
            db.add(derivado)
            db.flush()
            derivados_ids.append(derivado.id)
            db.add(
                RelacionRequisito(
                    origen_id=req.id,
                    derivado_id=derivado.id,
                    tipo_relacion="mitigacion",
                    obligatorio=d.obligatorio,
                )
            )
        # El padre sigue vigente (se sigue evaluando), marcado como mitigado.
        req.estado = "mitigado"

    # Registro del tratamiento (siempre).
    tratamiento = Tratamiento(
        requisito_id=req.id,
        decision=payload.decision,
        justificacion=payload.justificacion,
        responsable=payload.responsable,
    )
    db.add(tratamiento)
    db.commit()
    db.refresh(tratamiento)

    return {
        "id": tratamiento.id,
        "requisito_id": tratamiento.requisito_id,
        "decision": tratamiento.decision,
        "justificacion": tratamiento.justificacion,
        "responsable": tratamiento.responsable,
        "creado_en": tratamiento.creado_en,
        "nuevo_requisito_id": nuevo_requisito_id,
        "derivados_ids": derivados_ids,
    }


# ---------------------------------------------------------------------------
# Chat deliberativo: conversar con el asistente sobre el requisito y su analisis
# ---------------------------------------------------------------------------
def _contexto_chat(db: Session, req: Requisito, analisis: AnalisisEtico | None) -> str:
    """Arma el contexto (texto) que el asistente conoce: el requisito y su analisis."""
    partes = [
        "REQUISITO EN DISCUSION:",
        f"- Codigo: {req.codigo or '-'}",
        f"- Nombre: {req.nombre}",
        f"- Descripcion: {req.descripcion or '-'}",
        f"- Estado: {req.estado}",
    ]
    if analisis is None:
        partes.append("\n(El requisito aun no tiene analisis etico.)")
        return "\n".join(partes)

    temas = (
        db.query(TemaEticoDetectado)
        .filter(TemaEticoDetectado.analisis_id == analisis.id)
        .all()
    )
    partes.append("\nCAPA 1 - Temas eticos detectados:")
    if temas:
        for t in temas:
            partes.append(
                f"- {t.tema_etico} | actor: {t.actor_afectado or '-'} | "
                f"dano: {t.tipo_dano or '-'} | norma: {t.norma_tensionada_texto or '-'}"
            )
    else:
        partes.append("- (sin temas detectados)")

    capas = analisis.capas_2_3 or {}
    c2 = capas.get("capa_2_analisis", {})
    c3 = capas.get("capa_3_deliberacion", {})
    if c2.get("mapa_stakeholders"):
        partes.append("\nCAPA 2 - Stakeholders: " + "; ".join(
            f"{s.get('stakeholder','')}: {s.get('interes','')}" for s in c2["mapa_stakeholders"]
        ))
    if c2.get("tensiones_de_valores"):
        partes.append("Tensiones de valores: " + "; ".join(
            f"{t.get('valor_a','')} vs {t.get('valor_b','')}" for t in c2["tensiones_de_valores"]
        ))
    if c3.get("preguntas_deliberativas"):
        partes.append("\nCAPA 3 - Preguntas deliberativas abiertas: " + " | ".join(
            c3["preguntas_deliberativas"]
        ))
    if analisis.limitaciones:
        partes.append(f"\nLimitaciones del analisis: {analisis.limitaciones}")
    return "\n".join(partes)


@router.post("/requisitos/{requisito_id}/chat", response_model=ChatResponse)
def chat_requisito(
    requisito_id: uuid.UUID,
    payload: ChatRequest,
    db: Session = Depends(get_db),
):
    """Conversa con el asistente de etica sobre ESTE requisito y su analisis.

    El asistente acompaña la deliberacion: no decide por el equipo, ayuda a pensar.
    """
    req = db.get(Requisito, requisito_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Requisito no encontrado")

    analisis = _ultimo_analisis(db, requisito_id)
    contexto = _contexto_chat(db, req, analisis)
    system = (
        "Eres un asistente de etica de requisitos de software con IA que acompaña "
        "la deliberacion de un equipo. Conversas de forma clara y breve, haces "
        "preguntas cuando ayudan, y NO decides por el equipo: el humano siempre "
        "decide. Basate en el contexto del requisito y su analisis; si algo no "
        "esta en el contexto, dilo en vez de inventar.\n\n" + contexto
    )
    mensajes = [{"role": m.role, "content": m.content} for m in payload.messages]
    if not mensajes:
        raise HTTPException(status_code=400, detail="Faltan mensajes en la conversacion")

    try:
        reply = get_llm_provider().chat(system, mensajes)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"reply": reply}
