"""Orquestacion de las Fases 2-3: analisis etico con LLM + RAG (las tres capas).

Flujo (seccion 7 del contexto):
1. Primera pasada del LLM: temas preliminares + consultas para el RAG.
2. Recuperacion en pgvector filtrando por las normas activas del proyecto.
3. Segunda pasada del LLM: las tres capas, citando los fragmentos recuperados.
4. Validacion contra el esquema Pydantic y persistencia (Capa 1 relacional,
   Capas 2-3 en JSON). Si no hubo recuperacion, baja la confianza.

Los proveedores (LLM y embeddings) se pueden inyectar para poder probar todo el
flujo con dobles deterministas, sin gastar API.
"""

import uuid

from models import (
    Requisito,
    AnalisisEtico,
    TemaEticoDetectado,
    CitaNormativa,
    ChunkNormativo,
)
from schemas.analisis import AnalisisLLM, PrimeraPasada
from providers.llm import get_llm_provider
from providers.embeddings import get_embedding_provider
from rag.retrieve import recuperar
from config import settings

# Instrucciones base del analizador. Resume el rol y las reglas del metodo.
SISTEMA = (
    "Eres un analista de etica de requisitos de software con IA. Tu trabajo es "
    "IDENTIFICAR, ANALIZAR y PROPONER; el humano siempre decide. No eres un oraculo.\n"
    "Analiza el requisito buscando tensiones eticas reales (privacidad, no "
    "discriminacion, transparencia, autonomia, seguridad, etc.). Si propones "
    "reformulaciones, deben estar disenadas para reducir o resolver el conflicto "
    "etico detectado, no ser una redaccion cualquiera."
)


def _texto_requisito(req: Requisito) -> str:
    return (
        f"Codigo: {req.codigo or '-'}\n"
        f"Nombre: {req.nombre}\n"
        f"Descripcion: {req.descripcion or '-'}\n"
        f"Tipo: {req.tipo or '-'}\n"
        f"Stakeholder: {req.stakeholder or '-'}"
    )


def _prompt_pass1(req: Requisito) -> str:
    return (
        f"{SISTEMA}\n\n"
        "PRIMERA PASADA. Lee el requisito y propon:\n"
        "- temas_preliminares: posibles temas eticos que tensiona.\n"
        "- consultas_rag: frases de busqueda para recuperar la normativa pertinente.\n\n"
        f"REQUISITO:\n{_texto_requisito(req)}"
    )


def _prompt_pass2(req: Requisito, fragmentos: list[dict]) -> str:
    if fragmentos:
        ctx = "\n\n".join(
            f"[chunk_id: {f['chunk_id']}] ({f['referencia'] or 's/ref'})\n{f['texto']}"
            for f in fragmentos
        )
        nota_citas = (
            "Cita los fragmentos que respalden cada tema usando su chunk_id exacto "
            "en el campo citas. Si una afirmacion no se apoya en ningun fragmento, "
            "indica menor confianza."
        )
    else:
        ctx = "(No se recuperaron fragmentos normativos.)"
        nota_citas = (
            "No hay fragmentos normativos disponibles: deja citas vacias y usa "
            "nivel_confianza 'baja'."
        )

    return (
        f"{SISTEMA}\n\n"
        "SEGUNDA PASADA. Produce el analisis etico completo en TRES CAPAS:\n"
        "- capa_1_identificacion: temas eticos (con actor afectado, tipo de dano, "
        "norma tensionada, evidencia y citas).\n"
        "- capa_2_analisis: mapa de stakeholders y tensiones de valores.\n"
        "- capa_3_deliberacion: opciones de tratamiento (aceptar/reformular/mitigar/"
        "eliminar), reformulaciones propuestas, requisitos derivados y preguntas "
        "deliberativas.\n"
        f"{nota_citas}\n\n"
        f"REQUISITO:\n{_texto_requisito(req)}\n\n"
        f"FRAGMENTOS NORMATIVOS RECUPERADOS:\n{ctx}"
    )


def _recuperar_fragmentos(db, req, consultas, embed_provider, k, max_total):
    """Recupera fragmentos para varias consultas, deduplica y deja los mejores.

    - Por cada chunk repetido conserva la menor distancia (mas parecido).
    - Devuelve como mucho `max_total` fragmentos, ordenados de mas a menos
      relevante. Esto acota el contexto enviado al LLM (y el gasto de tokens).
    - Es tolerante a fallos: si no hay embeddings o el RAG esta vacio, devuelve [].
    """
    mejores = {}  # chunk_id -> (distancia, fragmento)
    for consulta in consultas or [req.nombre]:
        try:
            resultados = recuperar(
                db, consulta, proyecto_id=req.proyecto_id, k=k, provider=embed_provider
            )
        except Exception:
            # Embeddings no configurados / endpoint caido: seguimos sin citas.
            return []
        for chunk, dist in resultados:
            previo = mejores.get(chunk.id)
            if previo is None or dist < previo[0]:
                mejores[chunk.id] = (
                    dist,
                    {
                        "chunk_id": str(chunk.id),
                        "referencia": chunk.referencia,
                        "texto": chunk.texto,
                    },
                )
    # Ordena por distancia ascendente (mas relevante primero) y corta al tope.
    ordenados = sorted(mejores.values(), key=lambda x: x[0])[:max_total]
    return [frag for _dist, frag in ordenados]


def analizar_requisito(db, requisito_id, llm_provider=None, embed_provider=None, k=None, max_fragmentos=None):
    """Ejecuta el analisis completo de un requisito y lo persiste.

    `k` (fragmentos por consulta) y `max_fragmentos` (tope total) controlan cuanto
    contexto normativo se inyecta; por defecto vienen de la configuracion (.env).

    Devuelve el AnalisisEtico creado (con sus temas y citas ya guardados).
    """
    llm = llm_provider or get_llm_provider()
    embed = embed_provider or get_embedding_provider()
    k = k if k is not None else settings.rag_k_por_consulta
    max_fragmentos = max_fragmentos if max_fragmentos is not None else settings.rag_max_fragmentos

    req = db.get(Requisito, requisito_id)
    if req is None:
        raise ValueError("Requisito no encontrado")

    # 1) Primera pasada.
    pass1 = PrimeraPasada(**llm.analyze(_prompt_pass1(req), PrimeraPasada.model_json_schema()))

    # 2) Recuperacion RAG (acotada por k y por el tope total de fragmentos).
    fragmentos = _recuperar_fragmentos(db, req, pass1.consultas_rag, embed, k, max_fragmentos)

    # 3) Segunda pasada (las tres capas).
    pass2 = AnalisisLLM(**llm.analyze(_prompt_pass2(req, fragmentos), AnalisisLLM.model_json_schema()))

    # 4) Si no hubo recuperacion, baja la confianza (afirmaciones sin respaldo).
    limitaciones = pass2.limitaciones
    nivel = pass2.nivel_confianza
    if not fragmentos:
        nivel = "baja"
        nota = "Sin recuperacion normativa (RAG vacio o sin embeddings): citas no verificadas."
        limitaciones = f"{limitaciones}\n{nota}".strip() if limitaciones else nota

    # --- Persistencia ---
    modelo = getattr(llm, "model", "desconocido")
    analisis = AnalisisEtico(
        requisito_id=req.id,
        generado_por="llm",
        modelo_usado=modelo,
        nivel_confianza=nivel,
        limitaciones=limitaciones,
        capas_2_3={
            "capa_2_analisis": pass2.capa_2_analisis.model_dump(),
            "capa_3_deliberacion": pass2.capa_3_deliberacion.model_dump(),
        },
    )
    db.add(analisis)
    db.flush()  # para obtener analisis.id

    # Capa 1 relacional: tema_etico_detectado + cita_normativa.
    ids_validos = {f["chunk_id"] for f in fragmentos}
    for tema in pass2.capa_1_identificacion:
        fila_tema = TemaEticoDetectado(
            analisis_id=analisis.id,
            tema_etico=tema.tema_etico,
            actor_afectado=tema.actor_afectado,
            tipo_dano=tema.tipo_dano,
            norma_tensionada_texto=tema.norma_tensionada_texto,
            evidencia=tema.evidencia,
        )
        db.add(fila_tema)
        db.flush()
        for cita in tema.citas:
            # Solo enlazamos chunk_id si corresponde a un fragmento real recuperado.
            chunk_id = None
            if cita.chunk_id and cita.chunk_id in ids_validos:
                chunk_id = uuid.UUID(cita.chunk_id)
            db.add(
                CitaNormativa(
                    tema_id=fila_tema.id,
                    chunk_id=chunk_id,
                    texto_citado=cita.texto_citado,
                )
            )

    db.commit()
    db.refresh(analisis)
    return analisis
