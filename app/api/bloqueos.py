"""Router de bloqueos horarios sobre profesionales o sillones (C-09)."""

import sqlite3
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response
from pydantic import BaseModel

from app.api.auth import requiere_rol, usuario_actual
from app.api.dependencias import obtener_conexion
from app.db.conexion import transaccion
from app.db.repositorio_bloqueos import (
    crear_bloqueo,
    eliminar_bloqueo,
    listar_bloqueos,
)
from app.domain.models import AlcanceBloqueo, Bloqueo, validar_datos_bloqueo
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/bloqueos", tags=["bloqueos"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
UsuarioAutenticadoDep = Annotated[Usuario, Depends(usuario_actual)]
AdminDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))]


class BloqueoEntrada(BaseModel):
    alcance: str
    recurso_id: int
    inicio: datetime
    fin: datetime
    motivo: str = ""


class BloqueoSalida(BaseModel):
    id: int
    alcance: AlcanceBloqueo
    recurso_id: int
    inicio: str
    fin: str
    motivo: str


def _a_salida(bloqueo: Bloqueo) -> BloqueoSalida:
    if bloqueo.id is None:
        raise RuntimeError("El bloqueo persistido debe tener id.")
    return BloqueoSalida(
        id=bloqueo.id,
        alcance=bloqueo.alcance,
        recurso_id=bloqueo.recurso_id,
        inicio=bloqueo.inicio.isoformat(timespec="seconds"),
        fin=bloqueo.fin.isoformat(timespec="seconds"),
        motivo=bloqueo.motivo,
    )


@router.get("")
def get_bloqueos(
    conexion: ConexionDep,
    _: UsuarioAutenticadoDep,
) -> list[BloqueoSalida]:
    """Lista todos los bloqueos registrados ordenados por inicio."""
    return [_a_salida(b) for b in listar_bloqueos(conexion)]


@router.post("", status_code=201)
def post_bloqueo(
    entrada: BloqueoEntrada,
    conexion: ConexionDep,
    _: AdminDep,
) -> BloqueoSalida:
    """Valida el intervalo y el recurso y crea un bloqueo."""
    bloqueo_validado = validar_datos_bloqueo(
        alcance=entrada.alcance,
        recurso_id=entrada.recurso_id,
        inicio=entrada.inicio,
        fin=entrada.fin,
        motivo=entrada.motivo,
    )
    with transaccion(conexion):
        creado = crear_bloqueo(conexion, bloqueo_validado)
    return _a_salida(creado)


@router.delete("/{id}", status_code=204)
def delete_bloqueo(
    id: Annotated[int, Path(ge=1)],
    conexion: ConexionDep,
    _: AdminDep,
) -> Response:
    """Elimina un bloqueo por id o responde 404 si no existe."""
    with transaccion(conexion):
        eliminado = eliminar_bloqueo(conexion, id)
    if not eliminado:
        raise HTTPException(status_code=404)
    return Response(status_code=204)
