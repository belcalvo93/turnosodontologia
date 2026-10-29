"""Acceso a la tabla `prestacion` (C-05). Solo consultas parametrizadas (regla dura 4)."""

import sqlite3
from typing import Final

from app.domain.errores import NombreDuplicado
from app.domain.models import Prestacion

_INSERTAR_PRESTACION: Final = """
    INSERT INTO prestacion (nombre, duracion_minutos, activa)
    VALUES (?, ?, ?)
"""
_SELECT_POR_ID: Final = """
    SELECT id, nombre, duracion_minutos, activa
    FROM prestacion
    WHERE id = ?
"""
_SELECT_TODOS: Final = """
    SELECT id, nombre, duracion_minutos, activa
    FROM prestacion
    ORDER BY id ASC
"""
_UPDATE_PRESTACION: Final = """
    UPDATE prestacion
    SET nombre = ?, duracion_minutos = ?, activa = ?
    WHERE id = ?
"""

_SIN_CAMBIO: Final = object()
_FilaPrestacion = tuple[int, str, int, int]
_MENSAJE_NOMBRE_DUPLICADO = "Ya existe una prestación con ese nombre."


def crear_prestacion(
    conexion: sqlite3.Connection,
    *,
    nombre: str,
    duracion_minutos: int,
    activa: bool = True,
) -> Prestacion:
    """Inserta una prestación y devuelve la entidad con su id asignado."""
    try:
        cursor = conexion.execute(
            _INSERTAR_PRESTACION, (nombre, duracion_minutos, int(activa))
        )
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id de la prestación insertada.")
    return Prestacion(
        id=cursor.lastrowid,
        nombre=nombre,
        duracion_minutos=duracion_minutos,
        activa=activa,
    )


def obtener_prestacion_por_id(
    conexion: sqlite3.Connection, id_prestacion: int
) -> Prestacion | None:
    """Devuelve la prestación por id o None si no existe."""
    fila = conexion.execute(_SELECT_POR_ID, (id_prestacion,)).fetchone()
    return None if fila is None else _prestacion_desde_fila(fila)


def listar_prestaciones(conexion: sqlite3.Connection) -> list[Prestacion]:
    """Devuelve todas las prestaciones (activas e inactivas) ordenadas por id."""
    filas = conexion.execute(_SELECT_TODOS).fetchall()
    return [_prestacion_desde_fila(fila) for fila in filas]


def actualizar_prestacion(
    conexion: sqlite3.Connection,
    id_prestacion: int,
    *,
    nombre: str | object = _SIN_CAMBIO,
    duracion_minutos: int | object = _SIN_CAMBIO,
    activa: bool | object = _SIN_CAMBIO,
) -> Prestacion | None:
    """Actualiza los campos provistos de la prestación y la devuelve, o None si no existe."""
    actual = obtener_prestacion_por_id(conexion, id_prestacion)
    if actual is None:
        return None
    nuevo_nombre = actual.nombre if nombre is _SIN_CAMBIO else str(nombre)
    nueva_duracion = (
        actual.duracion_minutos
        if duracion_minutos is _SIN_CAMBIO
        else int(duracion_minutos)
    )
    nueva_activa = actual.activa if activa is _SIN_CAMBIO else bool(activa)
    try:
        conexion.execute(
            _UPDATE_PRESTACION,
            (nuevo_nombre, nueva_duracion, int(nueva_activa), id_prestacion),
        )
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    return Prestacion(
        id=id_prestacion,
        nombre=nuevo_nombre,
        duracion_minutos=nueva_duracion,
        activa=nueva_activa,
    )


def _prestacion_desde_fila(fila: _FilaPrestacion) -> Prestacion:
    id_prestacion, nombre, duracion_minutos, activa = fila
    return Prestacion(
        id=id_prestacion,
        nombre=nombre,
        duracion_minutos=duracion_minutos,
        activa=bool(activa),
    )


def _traducir_integridad(error: sqlite3.IntegrityError) -> None:
    """Convierte la violación de UNIQUE(nombre) en NombreDuplicado; deja pasar el resto."""
    if "UNIQUE" in str(error):
        raise NombreDuplicado(_MENSAJE_NOMBRE_DUPLICADO) from error
