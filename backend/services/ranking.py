"""Calculo del ranking (Fase 6). Determinista y sin LLM, para que sea auditable.

Esta es una FUNCION PURA: recibe datos planos (no toca la base de datos) y
devuelve el ranking calculado. Asi es trivial de explicar y de probar, que es
justo lo que pide la tesis.

Formula del contexto, por requisito vigente:

    PuntajeFinal =   Σ (peso × fuerza) de dimensiones tipo beneficio
                   + Σ (peso × fuerza) de dimensiones tipo valor_etico
                   − Σ (peso × fuerza) de dimensiones tipo costo
                   − Σ (peso × fuerza) de dimensiones tipo riesgo_etico_residual

Beneficio y valor_etico SUMAN; costo y riesgo_etico_residual RESTAN.
La fuerza 0 significa "no aplica", asi que no aporta (peso × 0 = 0).
Se ordena de mayor a menor puntaje.
"""

# Tipos de dimension que suman y que restan (seccion 4, Fase 4).
TIPOS_SUMAN = ("beneficio", "valor_etico")
TIPOS_RESTAN = ("costo", "riesgo_etico_residual")


def calcular_ranking(requisitos, dimensiones, evaluaciones):
    """Calcula el ranking a partir de datos planos.

    Parametros (listas de objetos con atributos, p.ej. modelos SQLAlchemy):
      - requisitos: requisitos a rankear (ya filtrados: vigentes y no eliminados).
      - dimensiones: dimensiones del proyecto (con .id, .tipo, .peso).
      - evaluaciones: filas requisito×dimension (con .requisito_id, .dimension_id, .fuerza).

    Devuelve una lista de dicts ordenada de mayor a menor puntaje. Cada item:
      {
        "requisito_id", "codigo", "nombre",
        "puntaje_final",
        "desglose": {"beneficio", "valor_etico", "costo", "riesgo_etico_residual"}
      }
    """
    # Mapa dimension_id -> (tipo, peso). El peso puede ser None si no se cargo;
    # en ese caso lo tratamos como 0 para no romper el calculo.
    dim_info = {
        d.id: (d.tipo, d.peso or 0)
        for d in dimensiones
    }

    # Mapa (requisito_id, dimension_id) -> fuerza.
    fuerza_de = {
        (e.requisito_id, e.dimension_id): (e.fuerza or 0)
        for e in evaluaciones
    }

    items = []
    for r in requisitos:
        # Acumuladores por categoria.
        desglose = {
            "beneficio": 0,
            "valor_etico": 0,
            "costo": 0,
            "riesgo_etico_residual": 0,
        }

        for dim_id, (tipo, peso) in dim_info.items():
            if tipo not in desglose:
                continue  # tipo desconocido: se ignora defensivamente
            fuerza = fuerza_de.get((r.id, dim_id), 0)
            desglose[tipo] += peso * fuerza

        puntaje_final = (
            desglose["beneficio"]
            + desglose["valor_etico"]
            - desglose["costo"]
            - desglose["riesgo_etico_residual"]
        )

        items.append(
            {
                "requisito_id": str(r.id),
                "codigo": r.codigo,
                "nombre": r.nombre,
                "puntaje_final": puntaje_final,
                "desglose": desglose,
            }
        )

    # Orden de mayor a menor puntaje. Empate: por codigo para que sea estable.
    items.sort(key=lambda x: (-x["puntaje_final"], x["codigo"] or ""))
    return items
