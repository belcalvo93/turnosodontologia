"""Login con usuario y contraseña (C-03, RN-ACC-01, RN-ACC-04)."""

import sqlite3
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.dependencias import obtener_ahora, obtener_conexion
from app.api.errores import CredencialesInvalidas
from app.api.seguridad import emitir_token, verificar
from app.db.repositorio import buscar_credenciales

router = APIRouter(prefix="/auth", tags=["auth"])


class CredencialesEntrada(BaseModel):
    """Body JSON del login (design §4)."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenSalida(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


@router.post("/login")
def login(
    credenciales: CredencialesEntrada,
    request: Request,
    conexion: Annotated[sqlite3.Connection, Depends(obtener_conexion)],
    ahora: Annotated[datetime, Depends(obtener_ahora)],
) -> TokenSalida:
    """Devuelve un token firmado si el usuario y la contraseña coinciden."""
    encontrado = buscar_credenciales(conexion, credenciales.username)
    if encontrado is None:
        raise CredencialesInvalidas()
    usuario, password_hash = encontrado
    if not verificar(credenciales.password, password_hash):
        raise CredencialesInvalidas()
    return TokenSalida(access_token=emitir_token(usuario, request.app.state.config, ahora))
