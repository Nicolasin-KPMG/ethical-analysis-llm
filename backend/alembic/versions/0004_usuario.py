"""Tabla de usuarios para el login (auth con JWT).

Crea `usuario` (email unico, nombre, hash de contrasena, rol). Los proyectos
siguen siendo compartidos; el usuario solo controla el acceso a la herramienta.

Revision ID: 0004_usuario
Revises: 0003_dim_aplicabilidad
Create Date: 2026-07-08
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004_usuario"
down_revision: Union[str, None] = "0003_dim_aplicabilidad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS usuario (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'participante',
            creado_en TIMESTAMPTZ DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS usuario")
