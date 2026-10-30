"""Router de agenda diaria y semanal por profesional y por sillón (C-14)."""

import sqlite3
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, NaiveDatetime

from app.api.auth import usuario_actual
from app.api.dependencias import obtener_conexion
from app.api.errores import SinPermiso
from app.db.repositorio_agenda import (
    consultar_agenda_profesional,
    consultar_agenda_sillon,
)
from app.db.repositorio_profesionales import obtener_profesional_por_id
from app.db.repositorio_sillones import obtener_sillon_por_id
from app.domain.usuarios import (
    Usuario,
    puede_ver_agenda_profesional,
    puede_ver_agenda_sillon,
    validar_rango_agenda,
)

router = APIRouter(prefix="/agenda", tags=["agenda"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
UsuarioDep = Annotated[Usuario, Depends(usuario_actual)]


class ItemAgenda(BaseModel):
    tipo: Literal["turno", "bloqueo"]
    id: int
    inicio: str
    fin: str
    paciente_id: int | None = None
    profesional_id: int | None = None
    sillon_id: int | None = None
    prestacion_id: int | None = None
    estado: str | None = None
    alcance: str | None = None
    recurso_id: int | None = None
    motivo: str | None = None


class AgendaResponse(BaseModel):
    recurso_tipo: Literal["profesional", "sillon"]
    recurso_id: int
    desde: str
    hasta: str
    items: list[ItemAgenda]
    turnos: list[ItemAgenda] = []
    bloqueos: list[ItemAgenda] = []


@router.get("/profesionales/{profesional_id}")
def get_agenda_profesional(
    profesional_id: Annotated[int, Path(ge=1)],
    desde: Annotated[NaiveDatetime, Query()],
    hasta: Annotated[NaiveDatetime, Query()],
    conexion: ConexionDep,
    usuario: UsuarioDep,
) -> AgendaResponse:
    """Devuelve turnos activos y bloqueos del profesional en el rango cronológico [desde, hasta)."""
    validar_rango_agenda(desde, hasta)

    if not puede_ver_agenda_profesional(usuario, profesional_id):
        raise SinPermiso()

    profesional = obtener_profesional_por_id(conexion, profesional_id)
    if profesional is None:
        raise HTTPException(status_code=404)

    turnos, bloqueos = consultar_agenda_profesional(
        conexion,
        profesional_id=profesional_id,
        desde=desde,
        hasta=hasta,
    )

    items_turno = [
        ItemAgenda(
            tipo="turno",
            id=t.id,  # type: ignore[arg-type]
            inicio=t.inicio.isoformat(timespec="seconds"),
            fin=t.fin.isoformat(timespec="seconds"),
            paciente_id=t.paciente_id,
            profesional_id=t.profesional_id,
            sillon_id=t.sillon_id,
            prestacion_id=t.prestacion_id,
            estado=t.estado,
        )
        for t in turnos
    ]

    items_bloqueo = [
        ItemAgenda(
            tipo="bloqueo",
            id=b.id,  # type: ignore[arg-type]
            inicio=b.inicio.isoformat(timespec="seconds"),
            fin=b.fin.isoformat(timespec="seconds"),
            alcance=b.alcance,
            recurso_id=b.recurso_id,
            motivo=b.motivo,
        )
        for b in bloqueos
    ]

    todos_los_items = items_turno + items_bloqueo
    todos_los_items.sort(key=lambda item: (item.inicio, item.id))

    return AgendaResponse(
        recurso_tipo="profesional",
        recurso_id=profesional_id,
        desde=desde.isoformat(timespec="seconds"),
        hasta=hasta.isoformat(timespec="seconds"),
        items=todos_los_items,
        turnos=items_turno,
        bloqueos=items_bloqueo,
    )


@router.get("/sillones/{sillon_id}")
def get_agenda_sillon(
    sillon_id: Annotated[int, Path(ge=1)],
    desde: Annotated[NaiveDatetime, Query()],
    hasta: Annotated[NaiveDatetime, Query()],
    conexion: ConexionDep,
    usuario: UsuarioDep,
) -> AgendaResponse:
    """Devuelve turnos activos y bloqueos del sillón en el rango cronológico [desde, hasta)."""
    validar_rango_agenda(desde, hasta)

    if not puede_ver_agenda_sillon(usuario):
        raise SinPermiso()

    sillon = obtener_sillon_por_id(conexion, sillon_id)
    if sillon is None:
        raise HTTPException(status_code=404)

    turnos, bloqueos = consultar_agenda_sillon(
        conexion,
        sillon_id=sillon_id,
        desde=desde,
        hasta=hasta,
    )

    items_turno = [
        ItemAgenda(
            tipo="turno",
            id=t.id,  # type: ignore[arg-type]
            inicio=t.inicio.isoformat(timespec="seconds"),
            fin=t.fin.isoformat(timespec="seconds"),
            paciente_id=t.paciente_id,
            profesional_id=t.profesional_id,
            sillon_id=t.sillon_id,
            prestacion_id=t.prestacion_id,
            estado=t.estado,
        )
        for t in turnos
    ]

    items_bloqueo = [
        ItemAgenda(
            tipo="bloqueo",
            id=b.id,  # type: ignore[arg-type]
            inicio=b.inicio.isoformat(timespec="seconds"),
            fin=b.fin.isoformat(timespec="seconds"),
            alcance=b.alcance,
            recurso_id=b.recurso_id,
            motivo=b.motivo,
        )
        for b in bloqueos
    ]

    todos_los_items = items_turno + items_bloqueo
    todos_los_items.sort(key=lambda item: (item.inicio, item.id))

    return AgendaResponse(
        recurso_tipo="sillon",
        recurso_id=sillon_id,
        desde=desde.isoformat(timespec="seconds"),
        hasta=hasta.isoformat(timespec="seconds"),
        items=todos_los_items,
        turnos=items_turno,
        bloqueos=items_bloqueo,
    )
