"""Acceso a la tabla `horario_atencion` (C-08). Solo consultas parametrizadas (regla dura 4)."""

import sqlite3
from dataclasses import replace
from datetime import time
from typing import Final

from app.domain.errores import DatoInvalido
from app.domain.models import HorarioAtencion

_EXISTE_PROFESIONAL: Final = "SELECT 1 FROM profesional WHERE id = ?"
_INSERTAR_HORARIO: Final = """
    INSERT INTO horario_atencion (profesional_id, dia_semana, hora_desde, hora_hasta)
    VALUES (?, ?, ?, ?)
"""
_SELECT_POR_PROFESIONAL: Final = """
    SELECT id, profesional_id, dia_semana, hora_desde, hora_hasta
    FROM horario_atencion
    WHERE profesional_id = ?
    ORDER BY dia_semana ASC, hora_desde ASC, id ASC
"""
_SELECT_POR_PROFESIONAL_Y_DIA: Final = """
    SELECT id, profesional_id, dia_semana, hora_desde, hora_hasta
    FROM horario_atencion
    WHERE profesional_id = ? AND dia_semana = ?
    ORDER BY hora_desde ASC, id ASC
"""

_FilaHorario = tuple[int, int, int, str, str]


def _existe_profesional(conexion: sqlite3.Connection, profesional_id: int) -> bool:
    fila = conexion.execute(_EXISTE_PROFESIONAL, (profesional_id,)).fetchone()
    return fila is not None


def crear_horario(
    conexion: sqlite3.Connection, horario: HorarioAtencion
) -> HorarioAtencion:
    """Verifica que el profesional exista e inserta la franja devolviéndola con su id."""
    if not _existe_profesional(conexion, horario.profesional_id):
        raise DatoInvalido("El profesional indicado no existe.")
    cursor = conexion.execute(
        _INSERTAR_HORARIO,
        (
            horario.profesional_id,
            horario.dia_semana,
            horario.hora_desde.strftime("%H:%M"),
            horario.hora_hasta.strftime("%H:%M"),
        ),
    )
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id del horario insertado.")
    return replace(horario, id=cursor.lastrowid)


def listar_horarios_por_profesional(
    conexion: sqlite3.Connection, profesional_id: int
) -> list[HorarioAtencion]:
    """Devuelve todas las franjas horarias de un profesional ordenadas por día y hora."""
    filas = conexion.execute(_SELECT_POR_PROFESIONAL, (profesional_id,)).fetchall()
    return [_horario_desde_fila(fila) for fila in filas]


def listar_horarios_por_profesional_y_dia(
    conexion: sqlite3.Connection, profesional_id: int, dia_semana: int
) -> list[HorarioAtencion]:
    """Devuelve las franjas de un profesional para un día de la semana ordenadas por hora."""
    filas = conexion.execute(
        _SELECT_POR_PROFESIONAL_Y_DIA, (profesional_id, dia_semana)
    ).fetchall()
    return [_horario_desde_fila(fila) for fila in filas]


def _horario_desde_fila(fila: _FilaHorario) -> HorarioAtencion:
    id_horario, profesional_id, dia_semana, hora_desde, hora_hasta = fila
    return HorarioAtencion(
        id=id_horario,
        profesional_id=profesional_id,
        dia_semana=dia_semana,
        hora_desde=time.fromisoformat(hora_desde),
        hora_hasta=time.fromisoformat(hora_hasta),
    )
