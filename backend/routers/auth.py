"""Endpoints de autenticacion: registro, login y perfil.

Auth simple para la fase de experimentacion. El registro es abierto (cualquiera
crea su cuenta); para restringirlo bastaria con exigir un rol admin aqui.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from schemas.auth import LoginInput, RegistroInput, TokenOut, UsuarioOut
from services.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(usuario: Usuario) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(usuario.id),
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.post("/register", response_model=TokenOut, status_code=201)
def registrar(payload: RegistroInput, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    existe = db.query(Usuario).filter(Usuario.email == email).first()
    if existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese correo",
        )
    usuario = Usuario(
        email=email,
        nombre=payload.nombre.strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return _token_response(usuario)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginInput, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not verify_password(payload.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contrasena incorrectos",
        )
    return _token_response(usuario)


@router.get("/me", response_model=UsuarioOut)
def perfil(usuario: Usuario = Depends(get_current_user)):
    return usuario
