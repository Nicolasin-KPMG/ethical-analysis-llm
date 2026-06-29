"""Bandera ética por requisito, derivada del análisis real (Fases 2-3).

Criterio (informativo, no bloquea — fiel al principio del método):
  - sin_analisis (gris): el requisito aún no se ha analizado.
  - verde: analizado y SIN temas éticos detectados.
  - roja: tiene temas éticos detectados y AÚN no se ha tratado (pendiente).
  - amarilla: tenía temas éticos y ya se tomó una decisión de tratamiento
    (aceptar / reformular / mitigar / eliminar).

Así la bandera responde dos preguntas: ¿hay tensiones éticas? y ¿se abordaron?
"""

from models import AnalisisEtico, TemaEticoDetectado

ESTADOS_TRATADOS = ("aceptado", "reformulado", "mitigado", "eliminado")


def bandera_de(db, requisito) -> str:
    analisis = (
        db.query(AnalisisEtico)
        .filter(AnalisisEtico.requisito_id == requisito.id)
        .order_by(AnalisisEtico.creado_en.desc())
        .first()
    )
    if analisis is None:
        return "sin_analisis"

    n_temas = (
        db.query(TemaEticoDetectado)
        .filter(TemaEticoDetectado.analisis_id == analisis.id)
        .count()
    )
    if n_temas == 0:
        return "verde"
    return "amarilla" if requisito.estado in ESTADOS_TRATADOS else "roja"
