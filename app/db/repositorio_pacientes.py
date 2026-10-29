"""Acceso a la tabla `paciente` (C-06). Solo consultas parametrizadas (regla dura 4)."""

import sqlite3
from typing import Final

from app.domain.errores import DniDuplicado
from app.domain.models import Paciente

_INSERTAR_PACIENTE: Final = """
    INSERT INTO paciente (nombre, apellido, dni, telefono, obra_social, nro_afiliado)
    VALUES (?, ?, ?, ?, ?, ?)
"""
_SELECT_POR_ID: Final = """
    SELECT id, nombre, apellido, dni, telefono, obra_social, nro_afiliado
    FROM paciente
    WHERE id = ?
"""
_SELECT_TODOS: Final = """
    SELECT id, nombre, apellido, dni, telefono, obra_social, nro_afiliado
    FROM paciente
    ORDER BY id ASC
"""
_UPDATE_PACIENTE: Final = """
    UPDATE paciente
    SET nombre = ?, apellido = ?, dni = ?, telefono = ?, obra_social = ?, nro_afiliado = ?
    WHERE id = ?
"""

_SIN_CAMBIO: Final = object()
_FilaPaciente = tuple[int, str, str, str, str | None, str | None, str | None]
_MENSAJE_DNI_DUPLICADO = "Ya existe un paciente con ese DNI."


def crear_paciente(
    conexion: sqlite3.Connection,
    *,
    nombre: str,
    apellido: str,
    dni: str,
    telefono: str | None = None,
    obra_social: str | None = None,
    nro_afiliado: str | None = None,
) -> Paciente:
    """Inserta un paciente y devuelve la entidad con su id asignado."""
    try:
        cursor = conexion.execute(
            _INSERTAR_PACIENTE,
            (nombre, apellido, dni, telefono, obra_social, nro_afiliado),
        )
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id del paciente insertado.")
    return Paciente(
        id=cursor.lastrowid,
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        obra_social=obra_social,
        nro_afiliado=nro_afiliado,
    )


def obtener_paciente_por_id(
    conexion: sqlite3.Connection, id_paciente: int
) -> Paciente | None:
    """Devuelve el paciente por id o None si no existe."""
    fila = conexion.execute(_SELECT_POR_ID, (id_paciente,)).fetchone()
    return None if fila is None else _paciente_desde_fila(fila)


def listar_pacientes(conexion: sqlite3.Connection) -> list[Paciente]:
    """Devuelve todos los pacientes ordenados por id."""
    filas = conexion.execute(_SELECT_TODOS).fetchall()
    return [_paciente_desde_fila(fila) for fila in filas]


def actualizar_paciente(
    conexion: sqlite3.Connection,
    id_paciente: int,
    *,
    nombre: str | object = _SIN_CAMBIO,
    apellido: str | object = _SIN_CAMBIO,
    dni: str | object = _SIN_CAMBIO,
    telefono: str | None | object = _SIN_CAMBIO,
    obra_social: str | None | object = _SIN_CAMBIO,
    nro_afiliado: str | None | object = _SIN_CAMBIO,
) -> Paciente | None:
    """Actualiza los campos provistos del paciente y lo devuelve, o None si no existe."""
    actual = obtener_paciente_por_id(conexion, id_paciente)
    if actual is None:
        return None
    nuevo_nombre = actual.nombre if nombre is _SIN_CAMBIO else str(nombre)
    nuevo_apellido = actual.apellido if apellido is _SIN_CAMBIO else str(apellido)
    nuevo_dni = actual.dni if dni is _SIN_CAMBIO else str(dni)
    nuevo_telefono = _resolver_opcional(actual.telefono, telefono)
    nueva_obra_social = _resolver_opcional(actual.obra_social, obra_social)
    nuevo_nro_afiliado = _resolver_opcional(actual.nro_afiliado, nro_afiliado)
    try:
        conexion.execute(
            _UPDATE_PACIENTE,
            (
                nuevo_nombre,
                nuevo_apellido,
                nuevo_dni,
                nuevo_telefono,
                nueva_obra_social,
                nuevo_nro_afiliado,
                id_paciente,
            ),
        )
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    return Paciente(
        id=id_paciente,
        nombre=nuevo_nombre,
        apellido=nuevo_apellido,
        dni=nuevo_dni,
        telefono=nuevo_telefono,
        obra_social=nueva_obra_social,
        nro_afiliado=nuevo_nro_afiliado,
    )


def _resolver_opcional(actual: str | None, cambio: str | None | object) -> str | None:
    if cambio is _SIN_CAMBIO:
        return actual
    return None if cambio is None else str(cambio)


def _paciente_desde_fila(fila: _FilaPaciente) -> Paciente:
    id_paciente, nombre, apellido, dni, telefono, obra_social, nro_afiliado = fila
    return Paciente(
        id=id_paciente,
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        obra_social=obra_social,
        nro_afiliado=nro_afiliado,
    )


def _traducir_integridad(error: sqlite3.IntegrityError) -> None:
    """Convierte la violación de UNIQUE(dni) en DniDuplicado; deja pasar el resto."""
    if "UNIQUE" in str(error):
        raise DniDuplicado(_MENSAJE_DNI_DUPLICADO) from error
