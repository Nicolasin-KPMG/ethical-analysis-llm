"""Esquemas Pydantic de autenticacion (login)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegistroInput(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    nombre: str
    rol: str
    creado_en: datetime | None = None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    """Respuesta del login/registro: el token y los datos del usuario."""

    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
