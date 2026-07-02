"""Dimensiones eticas por requisito + renombre del tipo.

- Nueva tabla `dimension_aplicabilidad` (dimension_id, requisito_id): restringe
  una dimension a los requisitos a los que aplica. La usan las dimensiones eticas
  que la IA detecta en el analisis (Fases 2-3), que son propias de algunos
  requisitos, no de todos.
- Renombra el valor del tipo de dimension 'riesgo_etico_residual' -> 'riesgo_etico'
  en las filas ya existentes (el tipo se guarda como texto libre).

Revision ID: 0003_dim_aplicabilidad
Revises: 0002_rag_indexes
Create Date: 2026-07-02
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003_dim_aplicabilidad"
down_revision: Union[str, None] = "0002_rag_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS dimension_aplicabilidad (
            dimension_id UUID NOT NULL REFERENCES dimension(id) ON DELETE CASCADE,
            requisito_id UUID NOT NULL REFERENCES requisito(id) ON DELETE CASCADE,
            PRIMARY KEY (dimension_id, requisito_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_dim_aplic_requisito "
        "ON dimension_aplicabilidad (requisito_id)"
    )
    # Renombre del valor del tipo en filas existentes.
    op.execute(
        "UPDATE dimension SET tipo = 'riesgo_etico' "
        "WHERE tipo = 'riesgo_etico_residual'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE dimension SET tipo = 'riesgo_etico_residual' "
        "WHERE tipo = 'riesgo_etico'"
    )
    op.execute("DROP INDEX IF EXISTS ix_dim_aplic_requisito")
    op.execute("DROP TABLE IF EXISTS dimension_aplicabilidad")
