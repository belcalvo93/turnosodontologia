"""Router de profesionales: alta, listado, edición parcial y baja lógica (C-04)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from app.api.auth import requiere_rol, usuario_actual
from app.api.dependencias import obtener_conexion
from app.db.conexion import transaccion
from app.db.repositorio_profesionales import (
    actualizar_profesional,
    crear_profesional,
    listar_profesionales,
    obtener_profesional_por_id,
)
from app.domain.errores import DatoInvalido
from app.domain.models import Profesional, validar_datos_profesional
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/profesionales", tags=["profesionales"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
UsuarioAutenticadoDep = Annotated[Usuario, Depends(usuario_actual)]
AdminDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))]


class ProfesionalEntrada(BaseModel):
    nombre: str
    apellido: str
    matricula: str | None = None


class ProfesionalActualizar(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    matricula: str | None = None
    activo: bool | None = None


class ProfesionalSalida(BaseModel):
    id: int
    nombre: str
    apellido: str
    matricula: str | None
    activo: bool


def _a_salida(profesional: Profesional) -> ProfesionalSalida:
    if profesional.id is None:
        raise RuntimeError("El profesional persistido debe tener id.")
    return ProfesionalSalida(
        id=profesional.id,
        nombre=profesional.nombre,
        apellido=profesional.apellido,
        matricula=profesional.matricula,
        activo=profesional.activo,
    )


@router.get("")
def get_profesionales(
    conexion: ConexionDep,
    _: UsuarioAutenticadoDep,
) -> list[ProfesionalSalida]:
    """Lista todos los profesionales registrados, incluyendo activos e inactivos."""
    return [_a_salida(p) for p in listar_profesionales(conexion)]


@router.post("", status_code=201)
def post_profesional(
    entrada: ProfesionalEntrada,
    conexion: ConexionDep,
    _: AdminDep,
) -> ProfesionalSalida:
    """Crea un profesional activo tras validar sus datos en el dominio."""
    nombre, apellido, matricula = validar_datos_profesional(
        entrada.nombre, entrada.apellido, entrada.matricula
    )
    with transaccion(conexion):
        creado = crear_profesional(
            conexion,
            nombre=nombre,
            apellido=apellido,
            matricula=matricula,
        )
    return _a_salida(creado)


@router.patch("/{id}")
def patch_profesional(
    id: Annotated[int, Path(ge=1)],
    cambios: ProfesionalActualizar,
    conexion: ConexionDep,
    _: AdminDep,
) -> ProfesionalSalida:
    """Actualiza parcialmente un profesional o lo desactiva con activo=false."""
    campos = cambios.model_dump(exclude_unset=True)
    with transaccion(conexion):
        actual = obtener_profesional_por_id(conexion, id)
        if actual is None:
            raise HTTPException(status_code=404)

        if "nombre" in campos and campos["nombre"] is None:
            raise DatoInvalido("El nombre del profesional no puede estar vacío.")
        if "apellido" in campos and campos["apellido"] is None:
            raise DatoInvalido("El apellido del profesional no puede estar vacío.")
        if "activo" in campos and campos["activo"] is None:
            raise DatoInvalido("El estado activo del profesional no puede ser nulo.")

        nombre_candidato = campos.get("nombre", actual.nombre)
        apellido_candidato = campos.get("apellido", actual.apellido)
        matricula_candidata = (
            campos["matricula"] if "matricula" in campos else actual.matricula
        )
        activo_candidato = campos["activo"] if "activo" in campos else actual.activo

        nombre, apellido, matricula = validar_datos_profesional(
            nombre_candidato, apellido_candidato, matricula_candidata
        )
        actualizado = actualizar_profesional(
            conexion,
            id,
            nombre=nombre,
            apellido=apellido,
            matricula=matricula,
            activo=activo_candidato,
        )
    if actualizado is None:
        raise HTTPException(status_code=404)
    return _a_salida(actualizado)
