"""Acceso a datos para la consulta de agenda diaria y semanal (C-14).

Recupera turnos activos y bloqueos por profesional o por sillón en un rango
semiabierto [desde, hasta). Solo SQL parametrizado (regla dura 4).
"""

from datetime import datetime
import sqlite3
from typing import Final

from app.db.repositorio_bloqueos import _bloqueo_desde_fila
from app.db.repositorio_turnos import COLUMNAS_TURNO, turno_desde_fila
from app.domain.models import Bloqueo, Turno

_SELECT_TURNOS_PROFESIONAL: Final = f"""
    SELECT {COLUMNAS_TURNO}
    FROM turno
    WHERE profesional_id = ?
      AND estado = 'reservado'
      AND inicio < ? AND fin > ?
    ORDER BY inicio ASC, id ASC
"""

_SELECT_BLOQUEOS_PROFESIONAL: Final = """
    SELECT id, alcance, recurso_id, inicio, fin, motivo
    FROM bloqueo
    WHERE alcance = 'profesional' AND recurso_id = ?
      AND inicio < ? AND fin > ?
    ORDER BY inicio ASC, id ASC
"""

_SELECT_TURNOS_SILLON: Final = f"""
    SELECT {COLUMNAS_TURNO}
    FROM turno
    WHERE sillon_id = ?
      AND estado = 'reservado'
      AND inicio < ? AND fin > ?
    ORDER BY inicio ASC, id ASC
"""

_SELECT_BLOQUEOS_SILLON: Final = """
    SELECT id, alcance, recurso_id, inicio, fin, motivo
    FROM bloqueo
    WHERE alcance = 'sillon' AND recurso_id = ?
      AND inicio < ? AND fin > ?
    ORDER BY inicio ASC, id ASC
"""


def consultar_agenda_profesional(
    conexion: sqlite3.Connection,
    *,
    profesional_id: int,
    desde: datetime,
    hasta: datetime,
) -> tuple[list[Turno], list[Bloqueo]]:
    """Devuelve turnos activos y bloqueos del profesional en el rango `[desde, hasta)` ordenados por inicio."""
    desde_str = desde.isoformat(timespec="seconds")
    hasta_str = hasta.isoformat(timespec="seconds")

    filas_turnos = conexion.execute(
        _SELECT_TURNOS_PROFESIONAL,
        (profesional_id, hasta_str, desde_str),
    ).fetchall()

    filas_bloqueos = conexion.execute(
        _SELECT_BLOQUEOS_PROFESIONAL,
        (profesional_id, hasta_str, desde_str),
    ).fetchall()

    turnos = [turno_desde_fila(fila) for fila in filas_turnos]
    bloqueos = [_bloqueo_desde_fila(fila) for fila in filas_bloqueos]
    return turnos, bloqueos


def consultar_agenda_sillon(
    conexion: sqlite3.Connection,
    *,
    sillon_id: int,
    desde: datetime,
    hasta: datetime,
) -> tuple[list[Turno], list[Bloqueo]]:
    """Devuelve turnos activos y bloqueos del sillón en el rango `[desde, hasta)` ordenados por inicio."""
    desde_str = desde.isoformat(timespec="seconds")
    hasta_str = hasta.isoformat(timespec="seconds")

    filas_turnos = conexion.execute(
        _SELECT_TURNOS_SILLON,
        (sillon_id, hasta_str, desde_str),
    ).fetchall()

    filas_bloqueos = conexion.execute(
        _SELECT_BLOQUEOS_SILLON,
        (sillon_id, hasta_str, desde_str),
    ).fetchall()

    turnos = [turno_desde_fila(fila) for fila in filas_turnos]
    bloqueos = [_bloqueo_desde_fila(fila) for fila in filas_bloqueos]
    return turnos, bloqueos
