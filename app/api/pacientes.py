"""Router de pacientes: alta, listado y edición parcial (C-06, US-011)."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from app.api.auth import requiere_rol
from app.api.dependencias import obtener_conexion
from app.db.conexion import transaccion
from app.db.repositorio_pacientes import (
    actualizar_paciente,
    crear_paciente,
    listar_pacientes,
    obtener_paciente_por_id,
)
from app.domain.errores import DatoInvalido
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


class PacienteActualizar(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    dni: str | None = None
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


@router.patch("/{id}")
def patch_paciente(
    id: Annotated[int, Path(ge=1)],
    cambios: PacienteActualizar,
    conexion: ConexionDep,
    _: AdminORecepcionDep,
) -> PacienteSalida:
    """Actualiza parcialmente un paciente; permite limpiar opcionales con null."""
    campos = cambios.model_dump(exclude_unset=True)
    with transaccion(conexion):
        actual = obtener_paciente_por_id(conexion, id)
        if actual is None:
            raise HTTPException(status_code=404)

        if "nombre" in campos and campos["nombre"] is None:
            raise DatoInvalido("El nombre del paciente no puede estar vacío.")
        if "apellido" in campos and campos["apellido"] is None:
            raise DatoInvalido("El apellido del paciente no puede estar vacío.")
        if "dni" in campos and campos["dni"] is None:
            raise DatoInvalido("El DNI del paciente no puede estar vacío.")

        nombre_candidato = campos["nombre"] if "nombre" in campos else actual.nombre
        apellido_candidato = (
            campos["apellido"] if "apellido" in campos else actual.apellido
        )
        dni_candidato = campos["dni"] if "dni" in campos else actual.dni
        telefono_candidato = (
            campos["telefono"] if "telefono" in campos else actual.telefono
        )
        obra_social_candidata = (
            campos["obra_social"] if "obra_social" in campos else actual.obra_social
        )
        nro_afiliado_candidato = (
            campos["nro_afiliado"]
            if "nro_afiliado" in campos
            else actual.nro_afiliado
        )

        nombre, apellido, dni, telefono, obra_social, nro_afiliado = (
            validar_datos_paciente(
                nombre_candidato,
                apellido_candidato,
                dni_candidato,
                telefono=telefono_candidato,
                obra_social=obra_social_candidata,
                nro_afiliado=nro_afiliado_candidato,
            )
        )
        actualizado = actualizar_paciente(
            conexion,
            id,
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            telefono=telefono,
            obra_social=obra_social,
            nro_afiliado=nro_afiliado,
        )
    if actualizado is None:
        raise HTTPException(status_code=404)
    return _a_salida(actualizado)
