"""Router de prestaciones: alta, listado, edición parcial y baja lógica (C-05)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from app.api.auth import requiere_rol, usuario_actual
from app.api.dependencias import obtener_conexion
from app.db.conexion import transaccion
from app.db.repositorio_prestaciones import (
    actualizar_prestacion,
    crear_prestacion,
    listar_prestaciones,
    obtener_prestacion_por_id,
)
from app.domain.errores import DatoInvalido
from app.domain.models import Prestacion, validar_datos_prestacion
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/prestaciones", tags=["prestaciones"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
UsuarioAutenticadoDep = Annotated[Usuario, Depends(usuario_actual)]
AdminDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))]


class PrestacionEntrada(BaseModel):
    nombre: str
    duracion_minutos: int


class PrestacionActualizar(BaseModel):
    nombre: str | None = None
    duracion_minutos: int | None = None
    activa: bool | None = None


class PrestacionSalida(BaseModel):
    id: int
    nombre: str
    duracion_minutos: int
    activa: bool


def _a_salida(prestacion: Prestacion) -> PrestacionSalida:
    if prestacion.id is None:
        raise RuntimeError("La prestación persistida debe tener id.")
    return PrestacionSalida(
        id=prestacion.id,
        nombre=prestacion.nombre,
        duracion_minutos=prestacion.duracion_minutos,
        activa=prestacion.activa,
    )


@router.get("")
def get_prestaciones(
    conexion: ConexionDep,
    _: UsuarioAutenticadoDep,
) -> list[PrestacionSalida]:
    """Lista todas las prestaciones registradas, incluyendo activas e inactivas."""
    return [_a_salida(p) for p in listar_prestaciones(conexion)]


@router.post("", status_code=201)
def post_prestacion(
    entrada: PrestacionEntrada,
    conexion: ConexionDep,
    _: AdminDep,
) -> PrestacionSalida:
    """Crea una prestación activa tras normalizar y validar sus datos."""
    nombre, duracion_minutos = validar_datos_prestacion(
        entrada.nombre, entrada.duracion_minutos
    )
    with transaccion(conexion):
        creada = crear_prestacion(
            conexion, nombre=nombre, duracion_minutos=duracion_minutos
        )
    return _a_salida(creada)


@router.patch("/{id}")
def patch_prestacion(
    id: Annotated[int, Path(ge=1)],
    cambios: PrestacionActualizar,
    conexion: ConexionDep,
    _: AdminDep,
) -> PrestacionSalida:
    """Actualiza parcialmente una prestación o la desactiva con activa=false."""
    campos = cambios.model_dump(exclude_unset=True)
    with transaccion(conexion):
        actual = obtener_prestacion_por_id(conexion, id)
        if actual is None:
            raise HTTPException(status_code=404)

        if "nombre" in campos and campos["nombre"] is None:
            raise DatoInvalido("El nombre de la prestación no puede estar vacío.")
        if "duracion_minutos" in campos and campos["duracion_minutos"] is None:
            raise DatoInvalido("La duración de la prestación no puede ser nula.")
        if "activa" in campos and campos["activa"] is None:
            raise DatoInvalido("El estado activa de la prestación no puede ser nulo.")

        nombre_candidato = campos["nombre"] if "nombre" in campos else actual.nombre
        duracion_candidata = (
            campos["duracion_minutos"]
            if "duracion_minutos" in campos
            else actual.duracion_minutos
        )
        activa_candidata = campos["activa"] if "activa" in campos else actual.activa

        nombre, duracion_minutos = validar_datos_prestacion(
            nombre_candidato, duracion_candidata
        )
        actualizada = actualizar_prestacion(
            conexion,
            id,
            nombre=nombre,
            duracion_minutos=duracion_minutos,
            activa=activa_candidata,
        )
    if actualizada is None:
        raise HTTPException(status_code=404)
    return _a_salida(actualizada)
