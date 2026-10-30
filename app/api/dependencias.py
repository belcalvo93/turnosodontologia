"""Dependencias de FastAPI compartidas por los routers (C-03)."""

import sqlite3
from collections.abc import Iterator
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, Request

from app.db.conexion import abrir_conexion


def obtener_conexion(request: Request) -> Iterator[sqlite3.Connection]:
    """Abre una conexión propia del request y la cierra al terminar, aunque el endpoint falle.

    FastAPI puede abrirla y cerrarla en hilos distintos del threadpool; por eso
    `abrir_conexion` usa `check_same_thread=False` (design §5).
    """
    conexion = abrir_conexion(request.app.state.config.database_path)
    try:
        yield conexion
    finally:
        conexion.close()


def obtener_ahora(request: Request) -> datetime:
    """Devuelve el instante actual según el reloj de la app (inyectable en los tests)."""
    ahora: datetime = request.app.state.reloj()
    return ahora


def a_hora_local(instante: datetime, zona: str) -> datetime:
    """Convierte un instante con zona a la hora local de `zona`, sin tzinfo."""
    return instante.astimezone(ZoneInfo(zona)).replace(tzinfo=None)


def obtener_ahora_local(
    request: Request, ahora: Annotated[datetime, Depends(obtener_ahora)]
) -> datetime:
    """Hora local del consultorio (`CLINIC_TIMEZONE`) sin tzinfo, para `creado_en`/`ocurrio_en`.

    `obtener_ahora` debe devolver un instante CON zona (como `_hora_real` y `RelojFijo`):
    con un datetime naive, `astimezone` lo interpretaría en la zona del sistema.
    """
    return a_hora_local(ahora, request.app.state.config.clinic_timezone)
