"""Login con usuario y contraseña (C-03, RN-ACC-01, RN-ACC-04)."""

import secrets
import sqlite3
from datetime import datetime
from functools import cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.api.dependencias import obtener_ahora, obtener_conexion
from app.api.errores import CredencialesInvalidas, NoAutenticado
from app.api.seguridad import TokenInvalido, decodificar_token, emitir_token, hashear, verificar
from app.db.repositorio import buscar_credenciales, buscar_usuario_por_id
from app.domain.usuarios import Usuario

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


# Con auto_error=False, una cabecera ausente o que no es "Bearer" llega como None y la
# convertimos en nuestro NoAutenticado, en vez del 401/403 en inglés de FastAPI (design §4).
_esquema_bearer = HTTPBearer(auto_error=False)


def usuario_actual(
    request: Request,
    credencial: Annotated[HTTPAuthorizationCredentials | None, Depends(_esquema_bearer)],
    conexion: Annotated[sqlite3.Connection, Depends(obtener_conexion)],
    ahora: Annotated[datetime, Depends(obtener_ahora)],
) -> Usuario:
    """Valida el token bearer contra `ahora` y devuelve el usuario guardado en la base."""
    if credencial is None:
        raise NoAutenticado()
    try:
        claims = decodificar_token(credencial.credentials, request.app.state.config, ahora)
        id_usuario = int(claims["sub"])  # un `sub` que no es un id también es un token inválido
    except (TokenInvalido, ValueError) as error:
        raise NoAutenticado() from error
    # Se recarga en cada request: una baja o un cambio de rol se aplican en el acto (design §1).
    usuario = buscar_usuario_por_id(conexion, id_usuario)
    if usuario is None or not usuario.activo:
        raise NoAutenticado()
    return usuario
