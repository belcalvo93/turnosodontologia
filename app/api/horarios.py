"""Router de horarios de atención por profesional (C-08)."""

import sqlite3
from datetime import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from app.api.auth import requiere_rol, usuario_actual
from app.api.dependencias import obtener_conexion
from app.api.errores import SinPermiso
from app.db.conexion import transaccion
from app.db.repositorio_horarios import (
    crear_horario,
    listar_horarios_por_profesional,
    listar_horarios_por_profesional_y_dia,
)
from app.db.repositorio_profesionales import obtener_profesional_por_id
from app.domain.errores import DatoInvalido
from app.domain.models import (
    HorarioAtencion,
    validar_datos_horario,
    validar_horario_no_solapa,
)
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/profesionales", tags=["horarios"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
UsuarioAutenticadoDep = Annotated[Usuario, Depends(usuario_actual)]
AdminDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))]


class HorarioAtencionEntrada(BaseModel):
    dia_semana: int
    hora_desde: time
    hora_hasta: time


class HorarioAtencionSalida(BaseModel):
    id: int
    profesional_id: int
    dia_semana: int
    hora_desde: str
    hora_hasta: str


def _a_salida(horario: HorarioAtencion) -> HorarioAtencionSalida:
    if horario.id is None:
        raise RuntimeError("El horario persistido debe tener id.")
    return HorarioAtencionSalida(
        id=horario.id,
        profesional_id=horario.profesional_id,
        dia_semana=horario.dia_semana,
        hora_desde=horario.hora_desde.strftime("%H:%M"),
        hora_hasta=horario.hora_hasta.strftime("%H:%M"),
    )


@router.get("/{id}/horarios")
def get_horarios_profesional(
    id: Annotated[int, Path(ge=1)],
    conexion: ConexionDep,
    usuario: UsuarioAutenticadoDep,
) -> list[HorarioAtencionSalida]:
    """Lista las franjas horarias de un profesional."""
    if usuario.rol == Rol.ODONTOLOGO and usuario.profesional_id != id:
        raise SinPermiso()

    profesional = obtener_profesional_por_id(conexion, id)
    if profesional is None:
        raise HTTPException(status_code=404)

    horarios = listar_horarios_por_profesional(conexion, id)
    return [_a_salida(h) for h in horarios]


@router.post("/{id}/horarios", status_code=201)
def post_horario_profesional(
    id: Annotated[int, Path(ge=1)],
    entrada: HorarioAtencionEntrada,
    conexion: ConexionDep,
    _: AdminDep,
) -> HorarioAtencionSalida:
    """Crea una franja de atención para el profesional tras validar en el dominio."""
    horario_validado = validar_datos_horario(
        profesional_id=id,
        dia_semana=entrada.dia_semana,
        hora_desde=entrada.hora_desde,
        hora_hasta=entrada.hora_hasta,
    )
    with transaccion(conexion):
        profesional = obtener_profesional_por_id(conexion, id)
        if profesional is None:
            raise DatoInvalido("El profesional indicado no existe.")

        existentes = listar_horarios_por_profesional_y_dia(
            conexion, id, entrada.dia_semana
        )
        validar_horario_no_solapa(horario_validado, existentes)

        creado = crear_horario(conexion, horario_validado)

    return _a_salida(creado)
