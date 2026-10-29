"""Router de usuarios: alta, listado y edición parcial (C-07, US-013)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from app.api.auth import requiere_rol
from app.api.dependencias import obtener_conexion
from app.api.seguridad import hashear
from app.db.conexion import transaccion
from app.db.repositorio import buscar_usuario_por_id
from app.db.repositorio_profesionales import obtener_profesional_por_id
from app.db.repositorio_usuarios import actualizar_usuario, crear_usuario, listar_usuarios
from app.domain.errores import DatoInvalido
from app.domain.models import Profesional
from app.domain.usuarios import (
    Rol,
    SIN_CAMBIO,
    Usuario,
    aplicar_cambios_usuario,
    validar_datos_usuario,
    validar_username,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
AdminDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))]


class UsuarioEntrada(BaseModel):
    username: str
    password: str = Field(min_length=1)
    rol: Rol
    profesional_id: int | None = None


class UsuarioActualizar(BaseModel):
    """Body del PATCH: todos los campos opcionales; `exclude_unset` distingue omitido de null."""

    # Se declara solo para poder dar un mensaje específico cuando el cliente intenta cambiarlo.
    username: str | None = None
    password: str | None = Field(default=None, min_length=1)
    rol: Rol | None = None
    profesional_id: int | None = None
    activo: bool | None = None


class UsuarioSalida(BaseModel):
    id: int
    username: str
    rol: Rol
    profesional_id: int | None
    activo: bool


def _a_salida(usuario: Usuario) -> UsuarioSalida:
    """Arma la respuesta campo por campo: el hash nunca se serializa (D8)."""
    if usuario.id is None:
        raise RuntimeError("El usuario persistido debe tener id.")
    return UsuarioSalida(
        id=usuario.id,
        username=usuario.username,
        rol=usuario.rol,
        profesional_id=usuario.profesional_id,
        activo=usuario.activo,
    )


def _obtener_profesional(
    conexion: sqlite3.Connection, profesional_id: int | None
) -> Profesional | None:
    """Lee el profesional solo si el request lo informó (el dominio decide si es válido)."""
    if profesional_id is None:
        return None
    return obtener_profesional_por_id(conexion, profesional_id)


@router.get("")
def get_usuarios(conexion: ConexionDep, _: AdminDep) -> list[UsuarioSalida]:
    """Lista todos los usuarios (activos e inactivos) ordenados por id."""
    return [_a_salida(usuario) for usuario in listar_usuarios(conexion)]


@router.post("", status_code=201)
def post_usuario(
    entrada: UsuarioEntrada,
    conexion: ConexionDep,
    _: AdminDep,
) -> UsuarioSalida:
    """Crea un usuario tras validar el username y la invariante rol ↔ profesional."""
    username = validar_username(entrada.username)
    profesional = _obtener_profesional(conexion, entrada.profesional_id)
    rol, profesional_id = validar_datos_usuario(
        rol=entrada.rol,
        profesional_id=entrada.profesional_id,
        profesional=profesional,
    )
    password_hash = hashear(entrada.password)
    with transaccion(conexion):
        creado = crear_usuario(
            conexion,
            username=username,
            password_hash=password_hash,
            rol=rol,
            profesional_id=profesional_id,
        )
    return _a_salida(creado)


@router.patch("/{id}")
def patch_usuario(
    id: Annotated[int, Path(ge=1)],
    cambios: UsuarioActualizar,
    conexion: ConexionDep,
    _: AdminDep,
) -> UsuarioSalida:
    """Actualiza parcialmente un usuario y mantiene la invariante rol ↔ profesional."""
    campos = cambios.model_dump(exclude_unset=True)
    if "username" in campos:
        raise DatoInvalido("El nombre de usuario no se puede modificar.")
    if "rol" in campos and cambios.rol is None:
        raise DatoInvalido("El rol no puede ser nulo.")
    if "activo" in campos and cambios.activo is None:
        raise DatoInvalido("El estado activo no puede ser nulo.")
    if "password" in campos and cambios.password is None:
        raise DatoInvalido("La contraseña no puede ser nula.")

    with transaccion(conexion):
        actual = buscar_usuario_por_id(conexion, id)
        if actual is None:
            raise HTTPException(status_code=404)

        profesional_cambio = (
            campos["profesional_id"] if "profesional_id" in campos else SIN_CAMBIO
        )
        rol_candidato, profesional_candidato, activo_candidato = aplicar_cambios_usuario(
            actual,
            rol=cambios.rol,
            profesional_id=profesional_cambio,
            activo=cambios.activo,
        )
        profesional = (
            None
            if profesional_candidato is None
            else obtener_profesional_por_id(conexion, profesional_candidato)
        )
        rol_candidato, profesional_candidato = validar_datos_usuario(
            rol=rol_candidato,
            profesional_id=profesional_candidato,
            profesional=profesional,
        )
        hash_nuevo: dict[str, str] = (
            {"password_hash": hashear(str(campos["password"]))} if "password" in campos else {}
        )
        actualizado = actualizar_usuario(
            conexion,
            id,
            rol=rol_candidato,
            profesional_id=profesional_candidato,
            activo=activo_candidato,
            **hash_nuevo,
        )
    if actualizado is None:
        raise HTTPException(status_code=404)
    return _a_salida(actualizado)
