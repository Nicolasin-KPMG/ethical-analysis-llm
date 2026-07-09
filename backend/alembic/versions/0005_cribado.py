"""Pre-fase de analisis (cribado): marca de riesgo preliminar por requisito.

Agrega a `requisito`:
- riesgo_preliminar BOOLEAN (None = no cribado; True = entra al analisis 2-3;
  False = sin riesgo aparente, no entra).
- motivo_preliminar TEXT (justificacion breve del LLM).

Revision ID: 0005_cribado
Revises: 0004_usuario
Create Date: 2026-07-09
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005_cribado"
down_revision: Union[str, None] = "0004_usuario"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE requisito ADD COLUMN IF NOT EXISTS riesgo_preliminar BOOLEAN")
    op.execute("ALTER TABLE requisito ADD COLUMN IF NOT EXISTS motivo_preliminar TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE requisito DROP COLUMN IF EXISTS motivo_preliminar")
    op.execute("ALTER TABLE requisito DROP COLUMN IF EXISTS riesgo_preliminar")
