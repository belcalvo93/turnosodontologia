"""Login con usuario y contraseña (C-03, RN-ACC-01, RN-ACC-04)."""

import secrets
import sqlite3
from datetime import datetime
from functools import cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.api.dependencias import obtener_ahora, obtener_conexion
from app.api.errores import CredencialesInvalidas
from app.api.seguridad import emitir_token, hashear, verificar
from app.db.repositorio import buscar_credenciales

router = APIRouter(prefix="/auth", tags=["auth"])


@cache
def _hash_ficticio() -> str:
    """Hash de una contraseña aleatoria, calculado una sola vez y al primer uso."""
    return hashear(secrets.token_urlsafe(32))


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
        # Mismo costo que un usuario real: el tiempo de respuesta no revela si existe (design §4).
        verificar(credenciales.password, _hash_ficticio())
        raise CredencialesInvalidas()
    usuario, password_hash = encontrado
    # Se verifica la contraseña aunque el usuario esté inactivo, por la misma razón.
    if not verificar(credenciales.password, password_hash) or not usuario.activo:
        raise CredencialesInvalidas()
    return TokenSalida(access_token=emitir_token(usuario, request.app.state.config, ahora))
