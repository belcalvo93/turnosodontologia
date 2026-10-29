"""Acceso a la tabla `sillon` (C-05). Solo consultas parametrizadas (regla dura 4)."""

import sqlite3
from typing import Final

from app.domain.errores import NombreDuplicado
from app.domain.models import Sillon

_INSERTAR_SILLON: Final = """
    INSERT INTO sillon (nombre, activo)
    VALUES (?, ?)
"""
_SELECT_POR_ID: Final = """
    SELECT id, nombre, activo
    FROM sillon
    WHERE id = ?
"""
_SELECT_TODOS: Final = """
    SELECT id, nombre, activo
    FROM sillon
    ORDER BY id ASC
"""
_UPDATE_SILLON: Final = """
    UPDATE sillon
    SET nombre = ?, activo = ?
    WHERE id = ?
"""

_SIN_CAMBIO: Final = object()
_FilaSillon = tuple[int, str, int]
_MENSAJE_NOMBRE_DUPLICADO = "Ya existe un sillón con ese nombre."


def crear_sillon(
    conexion: sqlite3.Connection,
    *,
    nombre: str,
    activo: bool = True,
) -> Sillon:
    """Inserta un sillón y devuelve la entidad con su id asignado."""
    try:
        cursor = conexion.execute(_INSERTAR_SILLON, (nombre, int(activo)))
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id del sillón insertado.")
    return Sillon(id=cursor.lastrowid, nombre=nombre, activo=activo)


def obtener_sillon_por_id(
    conexion: sqlite3.Connection, id_sillon: int
) -> Sillon | None:
    """Devuelve el sillón por id o None si no existe."""
    fila = conexion.execute(_SELECT_POR_ID, (id_sillon,)).fetchone()
    return None if fila is None else _sillon_desde_fila(fila)


def listar_sillones(conexion: sqlite3.Connection) -> list[Sillon]:
    """Devuelve todos los sillones (activos e inactivos) ordenados por id."""
    filas = conexion.execute(_SELECT_TODOS).fetchall()
    return [_sillon_desde_fila(fila) for fila in filas]


def actualizar_sillon(
    conexion: sqlite3.Connection,
    id_sillon: int,
    *,
    nombre: str | object = _SIN_CAMBIO,
    activo: bool | object = _SIN_CAMBIO,
) -> Sillon | None:
    """Actualiza los campos provistos del sillón y lo devuelve, o None si no existe."""
    actual = obtener_sillon_por_id(conexion, id_sillon)
    if actual is None:
        return None
    nuevo_nombre = actual.nombre if nombre is _SIN_CAMBIO else str(nombre)
    nuevo_activo = actual.activo if activo is _SIN_CAMBIO else bool(activo)
    try:
        conexion.execute(
            _UPDATE_SILLON, (nuevo_nombre, int(nuevo_activo), id_sillon)
        )
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    return Sillon(id=id_sillon, nombre=nuevo_nombre, activo=nuevo_activo)


def _sillon_desde_fila(fila: _FilaSillon) -> Sillon:
    id_sillon, nombre, activo = fila
    return Sillon(id=id_sillon, nombre=nombre, activo=bool(activo))


def _traducir_integridad(error: sqlite3.IntegrityError) -> None:
    """Convierte la violación de UNIQUE(nombre) en NombreDuplicado; deja pasar el resto."""
    if "UNIQUE" in str(error):
        raise NombreDuplicado(_MENSAJE_NOMBRE_DUPLICADO) from error
