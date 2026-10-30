"""Router de turnos: alta con POST /turnos, consulta con GET /turnos/{id} (C-11, design D1, D5, D7)
y reprogramación con POST /turnos/{id}/reprogramar (C-13).

El router solo orquesta: valida la forma de la entrada (Pydantic), abre la transacción,
carga el contexto desde los repositorios y delega las reglas en `app/domain/`.
"""

import sqlite3
from datetime import datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, NaiveDatetime

from app.api.auth import requiere_rol, usuario_actual
from app.api.dependencias import obtener_ahora_local, obtener_conexion
from app.api.errores import SinPermiso
from app.db.conexion import transaccion
from app.db.repositorio_bloqueos import listar_bloqueos_de_recursos
from app.db.repositorio_horarios import listar_horarios_por_profesional_y_dia
from app.db.repositorio_pacientes import obtener_paciente_por_id
from app.db.repositorio_prestaciones import obtener_prestacion_por_id
from app.db.repositorio_profesionales import obtener_profesional_por_id
from app.db.repositorio_sillones import obtener_sillon_por_id
from app.db.repositorio_turnos import (
    crear_turno,
    listar_turnos_activos_del_dia,
    obtener_turno,
    reprogramar_turno,
)
from app.domain.models import EstadoTurno, Turno
from app.domain.reglas_turno import validar_alta, validar_recursos_alta, validar_reprogramacion
from app.domain.usuarios import Rol, Usuario, puede_ver_turno

router = APIRouter(prefix="/turnos", tags=["turnos"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
AhoraLocalDep = Annotated[datetime, Depends(obtener_ahora_local)]
UsuarioDep = Annotated[Usuario, Depends(usuario_actual)]
CreadorDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION))]


class CrearTurnoRequest(BaseModel):
    """Entrada del alta: el fin no se envía, lo calcula el dominio (RN-TUR-01)."""

    paciente_id: int
    profesional_id: int
    sillon_id: int
    prestacion_id: int
    inicio: NaiveDatetime  # hora local del consultorio; con zona u offset -> 422


class ReprogramarTurnoRequest(BaseModel):
    """Entrada de la reprogramación: profesional y sillón son opcionales (RN-TUR-07)."""

    nuevo_inicio: NaiveDatetime  # hora local del consultorio; con zona u offset -> 422
    nuevo_profesional_id: int | None = None
    nuevo_sillon_id: int | None = None


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


@router.post("/{turno_id}/reprogramar")
def post_reprogramar_turno(
    turno_id: Annotated[int, Path(ge=1)],
    entrada: ReprogramarTurnoRequest,
    conexion: ConexionDep,
    usuario: CreadorDep,
    ahora_local: AhoraLocalDep,
) -> TurnoResponse:
    """Mueve un turno futuro activo a otro horario, y opcionalmente a otro profesional o sillón."""
    dia = entrada.nuevo_inicio.date()
    desde = datetime.combine(dia, time.min)
    # BEGIN IMMEDIATE: el turno y el contexto se leen con el lock de escritura ya tomado.
    with transaccion(conexion):
        turno = obtener_turno(conexion, turno_id)
        if turno is None:
            raise HTTPException(status_code=404)
        profesional_id = (
            turno.profesional_id
            if entrada.nuevo_profesional_id is None
            else entrada.nuevo_profesional_id
        )
        sillon_id = turno.sillon_id if entrada.nuevo_sillon_id is None else entrada.nuevo_sillon_id
        # Solo se cargan los recursos enviados; las reglas las aplica el dominio.
        nuevo_profesional = (
            None
            if entrada.nuevo_profesional_id is None
            else obtener_profesional_por_id(conexion, entrada.nuevo_profesional_id)
        )
        nuevo_sillon = (
            None
            if entrada.nuevo_sillon_id is None
            else obtener_sillon_por_id(conexion, entrada.nuevo_sillon_id)
        )
        prestacion = obtener_prestacion_por_id(conexion, turno.prestacion_id)
        if prestacion is None:
            raise RuntimeError("El turno referencia una prestación inexistente.")
        nuevo = validar_reprogramacion(
            turno,
            entrada.nuevo_inicio,
            ahora_local,
            prestacion,
            listar_horarios_por_profesional_y_dia(
                conexion, profesional_id, entrada.nuevo_inicio.weekday()
            ),
            listar_bloqueos_de_recursos(
                conexion,
                profesional_id=profesional_id,
                sillon_id=sillon_id,
                desde=desde,
                hasta=desde + timedelta(days=1),
            ),
            listar_turnos_activos_del_dia(
                conexion,
                dia=dia,
                profesional_id=profesional_id,
                sillon_id=sillon_id,
                paciente_id=turno.paciente_id,
            ),
            nuevo_profesional_id=entrada.nuevo_profesional_id,
            nuevo_sillon_id=entrada.nuevo_sillon_id,
            nuevo_profesional=nuevo_profesional,
            nuevo_sillon=nuevo_sillon,
        )
        reprogramado = reprogramar_turno(
            conexion, turno, nuevo, usuario_id=usuario.id, ocurrio_en=ahora_local
        )
    return turno_a_response(reprogramado)


@router.get("/{turno_id}")
def get_turno(
    turno_id: Annotated[int, Path(ge=1)],
    conexion: ConexionDep,
    usuario: UsuarioDep,
) -> TurnoResponse:
    """Devuelve un turno por id: 404 si no existe (para todos los roles) y luego 403 por rol."""
    turno = obtener_turno(conexion, turno_id)
    if turno is None:
        raise HTTPException(status_code=404)
    if not puede_ver_turno(usuario, turno):
        raise SinPermiso()
    return turno_a_response(turno)
