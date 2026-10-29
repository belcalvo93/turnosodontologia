"""Router de pacientes: alta, listado y edición parcial (C-06, US-011)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import requiere_rol
from app.api.dependencias import obtener_conexion
from app.db.conexion import transaccion
from app.db.repositorio_pacientes import crear_paciente, listar_pacientes
from app.domain.models import Paciente, validar_datos_paciente
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/pacientes", tags=["pacientes"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
AdminORecepcionDep = Annotated[
    Usuario, Depends(requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION))
]


class PacienteEntrada(BaseModel):
    nombre: str
    apellido: str
    dni: str
    telefono: str | None = None
    obra_social: str | None = None
    nro_afiliado: str | None = None


class PacienteSalida(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    telefono: str | None
    obra_social: str | None
    nro_afiliado: str | None


def _a_salida(paciente: Paciente) -> PacienteSalida:
    if paciente.id is None:
        raise RuntimeError("El paciente persistido debe tener id.")
    return PacienteSalida(
        id=paciente.id,
        nombre=paciente.nombre,
        apellido=paciente.apellido,
        dni=paciente.dni,
        telefono=paciente.telefono,
        obra_social=paciente.obra_social,
        nro_afiliado=paciente.nro_afiliado,
    )


@router.get("")
def get_pacientes(
    conexion: ConexionDep,
    _: AdminORecepcionDep,
) -> list[PacienteSalida]:
    """Lista todos los pacientes ordenados por id."""
    return [_a_salida(p) for p in listar_pacientes(conexion)]


@router.post("", status_code=201)
def post_paciente(
    entrada: PacienteEntrada,
    conexion: ConexionDep,
    _: AdminORecepcionDep,
) -> PacienteSalida:
    """Crea un paciente tras normalizar y validar sus datos."""
    nombre, apellido, dni, telefono, obra_social, nro_afiliado = validar_datos_paciente(
        entrada.nombre,
        entrada.apellido,
        entrada.dni,
        telefono=entrada.telefono,
        obra_social=entrada.obra_social,
        nro_afiliado=entrada.nro_afiliado,
    )
    with transaccion(conexion):
        creado = crear_paciente(
            conexion,
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            telefono=telefono,
            obra_social=obra_social,
            nro_afiliado=nro_afiliado,
        )
    return _a_salida(creado)
