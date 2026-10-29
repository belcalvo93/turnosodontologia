"""Router de turnos: alta con POST /turnos (C-11, design D1).

El router solo orquesta: valida la forma de la entrada (Pydantic), abre la transacción,
carga el contexto desde los repositorios y delega las reglas en `app/domain/`.
"""

import sqlite3
from datetime import datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, NaiveDatetime

from app.api.auth import requiere_rol
from app.api.dependencias import obtener_ahora_local, obtener_conexion
from app.db.conexion import transaccion
from app.db.repositorio_bloqueos import listar_bloqueos_de_recursos
from app.db.repositorio_horarios import listar_horarios_por_profesional_y_dia
from app.db.repositorio_pacientes import obtener_paciente_por_id
from app.db.repositorio_prestaciones import obtener_prestacion_por_id
from app.db.repositorio_profesionales import obtener_profesional_por_id
from app.db.repositorio_sillones import obtener_sillon_por_id
from app.db.repositorio_turnos import crear_turno, listar_turnos_activos_del_dia
from app.domain.models import EstadoTurno, Turno
from app.domain.reglas_turno import validar_alta, validar_recursos_alta
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/turnos", tags=["turnos"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
AhoraLocalDep = Annotated[datetime, Depends(obtener_ahora_local)]
CreadorDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION))]


class CrearTurnoRequest(BaseModel):
    """Entrada del alta: el fin no se envía, lo calcula el dominio (RN-TUR-01)."""

    paciente_id: int
    profesional_id: int
    sillon_id: int
    prestacion_id: int
    inicio: NaiveDatetime  # hora local del consultorio; con zona u offset -> 422


class TurnoResponse(BaseModel):
    id: int
    paciente_id: int
    profesional_id: int
    sillon_id: int
    prestacion_id: int
    inicio: str
    fin: str
    estado: EstadoTurno


def turno_a_response(turno: Turno) -> TurnoResponse:
    """Serializa un turno persistido con fechas `YYYY-MM-DDTHH:MM:SS`."""
    if turno.id is None:
        raise RuntimeError("El turno persistido debe tener id.")
    return TurnoResponse(
        id=turno.id,
        paciente_id=turno.paciente_id,
        profesional_id=turno.profesional_id,
        sillon_id=turno.sillon_id,
        prestacion_id=turno.prestacion_id,
        inicio=turno.inicio.isoformat(timespec="seconds"),
        fin=turno.fin.isoformat(timespec="seconds"),
        estado=turno.estado,
    )


@router.post("", status_code=201)
def post_turno(
    entrada: CrearTurnoRequest,
    conexion: ConexionDep,
    usuario: CreadorDep,
    ahora_local: AhoraLocalDep,
) -> TurnoResponse:
    """Reserva un turno validando recursos, horario, bloqueos y solapamientos (SE-06)."""
    dia = entrada.inicio.date()
    desde = datetime.combine(dia, time.min)
    # BEGIN IMMEDIATE: el contexto se lee con el lock de escritura ya tomado.
    with transaccion(conexion):
        prestacion = validar_recursos_alta(
            obtener_prestacion_por_id(conexion, entrada.prestacion_id),
            obtener_profesional_por_id(conexion, entrada.profesional_id),
            obtener_sillon_por_id(conexion, entrada.sillon_id),
            obtener_paciente_por_id(conexion, entrada.paciente_id),
        )
        candidato = validar_alta(
            entrada.inicio,
            prestacion,
            entrada.profesional_id,
            entrada.sillon_id,
            entrada.paciente_id,
            listar_horarios_por_profesional_y_dia(
                conexion, entrada.profesional_id, entrada.inicio.weekday()
            ),
            listar_bloqueos_de_recursos(
                conexion,
                profesional_id=entrada.profesional_id,
                sillon_id=entrada.sillon_id,
                desde=desde,
                hasta=desde + timedelta(days=1),
            ),
            listar_turnos_activos_del_dia(
                conexion,
                dia=dia,
                profesional_id=entrada.profesional_id,
                sillon_id=entrada.sillon_id,
                paciente_id=entrada.paciente_id,
            ),
        )
        creado = crear_turno(conexion, candidato, creado_por=usuario.id, creado_en=ahora_local)
    return turno_a_response(creado)
