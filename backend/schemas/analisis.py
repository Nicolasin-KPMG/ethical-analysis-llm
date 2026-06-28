"""Esquemas Pydantic de las Fases 2-3.

Incluye:
- El esquema de SALIDA DEL LLM en tres capas (lo que el analizador debe producir
  y contra lo que se valida la respuesta). Es la materializacion de la seccion 5
  del contexto.
- El esquema de la primera pasada (temas preliminares + consultas para el RAG).
- Los esquemas de lectura/edicion del analisis persistido y del tratamiento.

Las descripciones (Field description) se envian al LLM como parte del esquema de
la herramienta, asi que ayudan a que produzca cada campo bien.
"""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

NivelConfianza = Literal["alta", "media", "baja"]
Decision = Literal["aceptar", "reformular", "mitigar", "eliminar"]


# ---------------------------------------------------------------------------
# Primera pasada: el LLM propone temas y que buscar en la normativa (RAG).
# ---------------------------------------------------------------------------
class PrimeraPasada(BaseModel):
    temas_preliminares: list[str] = Field(
        default=[], description="Temas eticos preliminares que el requisito podria tensionar."
    )
    consultas_rag: list[str] = Field(
        default=[],
        description="Consultas de busqueda (frases) para recuperar los fragmentos normativos relevantes.",
    )


# ---------------------------------------------------------------------------
# Salida del LLM en tres capas (segunda pasada).
# ---------------------------------------------------------------------------
class Cita(BaseModel):
    chunk_id: Optional[str] = Field(
        default=None,
        description="UUID del fragmento normativo citado (de los recuperados). null si no hay respaldo.",
    )
    texto_citado: str = Field(default="", description="Fragmento textual en que se apoya el tema.")


class TemaIdentificado(BaseModel):
    """Capa 1: un tema etico detectado."""

    tema_etico: str
    actor_afectado: str = ""
    tipo_dano: str = ""
    norma_tensionada_texto: str = ""
    evidencia: str = ""
    citas: list[Cita] = []


class StakeholderItem(BaseModel):
    stakeholder: str
    interes: str = ""
    impacto: str = ""


class TensionValor(BaseModel):
    valor_a: str
    valor_b: str
    descripcion: str = ""


class Capa2Analisis(BaseModel):
    mapa_stakeholders: list[StakeholderItem] = []
    tensiones_de_valores: list[TensionValor] = []


class OpcionTratamiento(BaseModel):
    decision: Decision
    justificacion: str = ""
    pros: str = ""
    contras: str = ""


class ReformulacionPropuesta(BaseModel):
    texto_propuesto: str = Field(description="Nueva redaccion del requisito.")
    como_reduce_conflicto: str = Field(
        default="",
        description="Por que esta redaccion reduce o resuelve el conflicto etico detectado.",
    )


class DerivadoPropuesto(BaseModel):
    nombre: str
    descripcion: str = ""
    obligatorio: bool = True


class Capa3Deliberacion(BaseModel):
    opciones_tratamiento: list[OpcionTratamiento] = []
    reformulaciones_propuestas: list[ReformulacionPropuesta] = []
    requisitos_derivados_propuestos: list[DerivadoPropuesto] = []
    preguntas_deliberativas: list[str] = []


class AnalisisLLM(BaseModel):
    """Objeto completo que devuelve el analizador (las tres capas)."""

    capa_1_identificacion: list[TemaIdentificado] = []
    capa_2_analisis: Capa2Analisis = Capa2Analisis()
    capa_3_deliberacion: Capa3Deliberacion = Capa3Deliberacion()
    nivel_confianza: NivelConfianza = "media"
    limitaciones: str = ""


# ---------------------------------------------------------------------------
# Lectura del analisis persistido.
# ---------------------------------------------------------------------------
class CitaOut(BaseModel):
    chunk_id: Optional[uuid.UUID] = None
    texto_citado: Optional[str] = None


class TemaOut(BaseModel):
    id: uuid.UUID
    tema_etico: Optional[str] = None
    actor_afectado: Optional[str] = None
    tipo_dano: Optional[str] = None
    norma_tensionada_texto: Optional[str] = None
    evidencia: Optional[str] = None
    citas: list[CitaOut] = []


class AnalisisOut(BaseModel):
    id: uuid.UUID
    requisito_id: uuid.UUID
    generado_por: Optional[str] = None
    modelo_usado: Optional[str] = None
    nivel_confianza: Optional[str] = None
    limitaciones: Optional[str] = None
    capas_2_3: Optional[dict] = None
    creado_en: Optional[datetime] = None
    temas: list[TemaOut] = []


# ---------------------------------------------------------------------------
# Edicion humana del analisis (el humano edita libremente lo del LLM).
# ---------------------------------------------------------------------------
class TemaEdit(BaseModel):
    tema_etico: str
    actor_afectado: str = ""
    tipo_dano: str = ""
    norma_tensionada_texto: str = ""
    evidencia: str = ""
    citas: list[Cita] = []


class AnalisisUpdate(BaseModel):
    nivel_confianza: Optional[NivelConfianza] = None
    limitaciones: Optional[str] = None
    capas_2_3: Optional[dict] = None
    temas: Optional[list[TemaEdit]] = None


# ---------------------------------------------------------------------------
# Tratamiento (Fase 3).
# ---------------------------------------------------------------------------
class DerivadoInput(BaseModel):
    nombre: str
    descripcion: str = ""
    obligatorio: bool = True


class TratamientoCreate(BaseModel):
    decision: Decision
    justificacion: str = ""
    responsable: str = ""
    # Solo para "reformular": texto de la nueva version.
    nuevo_nombre: Optional[str] = None
    nueva_descripcion: Optional[str] = None
    # Solo para "mitigar": requisitos derivados a crear.
    derivados: list[DerivadoInput] = []


class TratamientoOut(BaseModel):
    id: uuid.UUID
    requisito_id: uuid.UUID
    decision: str
    justificacion: Optional[str] = None
    responsable: Optional[str] = None
    creado_en: Optional[datetime] = None
    # Efectos colaterales segun la decision:
    nuevo_requisito_id: Optional[uuid.UUID] = None  # reformular
    derivados_ids: list[uuid.UUID] = []             # mitigar
