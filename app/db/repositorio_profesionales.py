"""Acceso a la tabla `profesional` (C-04). Solo consultas parametrizadas (regla dura 4)."""

import sqlite3
from typing import Final

from app.domain.models import Profesional

_INSERTAR_PROFESIONAL: Final = """
    INSERT INTO profesional (nombre, apellido, matricula, activo)
    VALUES (?, ?, ?, ?)
"""
_SELECT_POR_ID: Final = """
    SELECT id, nombre, apellido, matricula, activo
    FROM profesional
    WHERE id = ?
"""
_SELECT_TODOS: Final = """
    SELECT id, nombre, apellido, matricula, activo
    FROM profesional
    ORDER BY id ASC
"""
_UPDATE_PROFESIONAL: Final = """
    UPDATE profesional
    SET nombre = ?, apellido = ?, matricula = ?, activo = ?
    WHERE id = ?
"""

_SIN_CAMBIO: Final = object()
_FilaProfesional = tuple[int, str, str, str | None, int]


def crear_profesional(
    conexion: sqlite3.Connection,
    *,
    nombre: str,
    apellido: str,
    matricula: str | None = None,
    activo: bool = True,
) -> Profesional:
    """Inserta un profesional y devuelve la entidad con su id asignado."""
    cursor = conexion.execute(
        _INSERTAR_PROFESIONAL, (nombre, apellido, matricula, int(activo))
    )
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id del profesional insertado.")
    return Profesional(
        id=cursor.lastrowid,
        nombre=nombre,
        apellido=apellido,
        matricula=matricula,
        activo=activo,
    )


def obtener_profesional_por_id(
    conexion: sqlite3.Connection, id_profesional: int
) -> Profesional | None:
    """Devuelve el profesional por id o None si no existe."""
    fila = conexion.execute(_SELECT_POR_ID, (id_profesional,)).fetchone()
    return None if fila is None else _profesional_desde_fila(fila)


def listar_profesionales(conexion: sqlite3.Connection) -> list[Profesional]:
    """Devuelve todos los profesionales (activos e inactivos) ordenados por id."""
    filas = conexion.execute(_SELECT_TODOS).fetchall()
    return [_profesional_desde_fila(fila) for fila in filas]


def actualizar_profesional(
    conexion: sqlite3.Connection,
    id_profesional: int,
    *,
    nombre: str | object = _SIN_CAMBIO,
    apellido: str | object = _SIN_CAMBIO,
    matricula: str | None | object = _SIN_CAMBIO,
    activo: bool | object = _SIN_CAMBIO,
) -> Profesional | None:
    """Actualiza los campos provistos del profesional y lo devuelve, o None si no existe."""
    actual = obtener_profesional_por_id(conexion, id_profesional)
    if actual is None:
        return None
    nuevo_nombre = actual.nombre if nombre is _SIN_CAMBIO else str(nombre)
    nuevo_apellido = actual.apellido if apellido is _SIN_CAMBIO else str(apellido)
    nueva_matricula = (
        actual.matricula
        if matricula is _SIN_CAMBIO
        else (None if matricula is None else str(matricula))
    )
    nuevo_activo = actual.activo if activo is _SIN_CAMBIO else bool(activo)
    conexion.execute(
        _UPDATE_PROFESIONAL,
        (nuevo_nombre, nuevo_apellido, nueva_matricula, int(nuevo_activo), id_profesional),
    )
    return Profesional(
        id=id_profesional,
        nombre=nuevo_nombre,
        apellido=nuevo_apellido,
        matricula=nueva_matricula,
        activo=nuevo_activo,
    )


def _profesional_desde_fila(fila: _FilaProfesional) -> Profesional:
    id_prof, nombre, apellido, matricula, activo = fila
    return Profesional(
        id=id_prof,
        nombre=nombre,
        apellido=apellido,
        matricula=matricula,
        activo=bool(activo),
    )
