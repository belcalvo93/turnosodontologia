"""Router de sillones: alta, listado, edición parcial y baja lógica (C-05, US-002)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from app.api.auth import requiere_rol, usuario_actual
from app.api.dependencias import obtener_conexion
from app.db.conexion import transaccion
from app.db.repositorio_sillones import (
    actualizar_sillon,
    crear_sillon,
    listar_sillones,
    obtener_sillon_por_id,
)
from app.domain.errores import DatoInvalido
from app.domain.models import Sillon, validar_datos_sillon
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/sillones", tags=["sillones"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
UsuarioAutenticadoDep = Annotated[Usuario, Depends(usuario_actual)]
AdminDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))]


class SillonEntrada(BaseModel):
    nombre: str


class SillonActualizar(BaseModel):
    nombre: str | None = None
    activo: bool | None = None


class SillonSalida(BaseModel):
    id: int
    nombre: str
    activo: bool


def _a_salida(sillon: Sillon) -> SillonSalida:
    if sillon.id is None:
        raise RuntimeError("El sillón persistido debe tener id.")
    return SillonSalida(id=sillon.id, nombre=sillon.nombre, activo=sillon.activo)


@router.get("")
def get_sillones(
    conexion: ConexionDep,
    _: UsuarioAutenticadoDep,
) -> list[SillonSalida]:
    """Lista todos los sillones registrados, incluyendo activos e inactivos."""
    return [_a_salida(s) for s in listar_sillones(conexion)]


@router.post("", status_code=201)
def post_sillon(
    entrada: SillonEntrada,
    conexion: ConexionDep,
    _: AdminDep,
) -> SillonSalida:
    """Crea un sillón activo tras normalizar y validar su nombre."""
    nombre = validar_datos_sillon(entrada.nombre)
    with transaccion(conexion):
        creado = crear_sillon(conexion, nombre=nombre)
    return _a_salida(creado)


@router.patch("/{id}")
def patch_sillon(
    id: Annotated[int, Path(ge=1)],
    cambios: SillonActualizar,
    conexion: ConexionDep,
    _: AdminDep,
) -> SillonSalida:
    """Actualiza parcialmente un sillón o lo desactiva con activo=false."""
    campos = cambios.model_dump(exclude_unset=True)
    with transaccion(conexion):
        actual = obtener_sillon_por_id(conexion, id)
        if actual is None:
            raise HTTPException(status_code=404)

        if "nombre" in campos and campos["nombre"] is None:
            raise DatoInvalido("El nombre del sillón no puede estar vacío.")
        if "activo" in campos and campos["activo"] is None:
            raise DatoInvalido("El estado activo del sillón no puede ser nulo.")

        nombre_candidato = (
            validar_datos_sillon(campos["nombre"])
            if "nombre" in campos
            else actual.nombre
        )
        activo_candidato = campos["activo"] if "activo" in campos else actual.activo

        actualizado = actualizar_sillon(
            conexion,
            id,
            nombre=nombre_candidato,
            activo=activo_candidato,
        )
    if actualizado is None:
        raise HTTPException(status_code=404)
    return _a_salida(actualizado)
