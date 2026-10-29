"""Acceso a la tabla `usuario` (C-03). Solo consultas parametrizadas (regla dura 4).

Las funciones no abren transacciones: escribir dentro de `transaccion()` lo decide
quien llama. El hash de la contraseña nunca viaja dentro de `Usuario`.
"""

import sqlite3

from app.domain.usuarios import Rol, Usuario

# Consultas literales completas: ni interpolación ni concatenación (regla dura 4).
_INSERTAR_USUARIO = """
    INSERT INTO usuario (username, password_hash, rol, profesional_id, activo)
    VALUES (?, ?, ?, ?, ?)
"""
_SELECT_CREDENCIALES = """
    SELECT id, username, rol, profesional_id, activo, password_hash
    FROM usuario
    WHERE username = ?
"""
_SELECT_POR_ID = """
    SELECT id, username, rol, profesional_id, activo
    FROM usuario
    WHERE id = ?
"""

# (id, username, rol, profesional_id, activo) tal como los devuelve SQLite.
_FilaUsuario = tuple[int, str, str, int | None, int]


def insertar_usuario(
    conexion: sqlite3.Connection,
    *,
    username: str,
    password_hash: str,
    rol: Rol,
    profesional_id: int | None = None,
    activo: bool = True,
) -> int:
    """Guarda un usuario y devuelve su id."""
    cursor = conexion.execute(
        _INSERTAR_USUARIO, (username, password_hash, rol.value, profesional_id, int(activo))
    )
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id del usuario insertado.")
    return cursor.lastrowid


def buscar_credenciales(
    conexion: sqlite3.Connection, username: str
) -> tuple[Usuario, str] | None:
    """Devuelve el usuario y su hash para el login, o None si el username no existe.

    Incluye usuarios inactivos: el login decide qué hacer con ellos.
    """
    fila = conexion.execute(_SELECT_CREDENCIALES, (username,)).fetchone()
    if fila is None:
        return None
    id_usuario, username, rol, profesional_id, activo, password_hash = fila
    return _usuario_desde_fila((id_usuario, username, rol, profesional_id, activo)), password_hash


def buscar_usuario_por_id(conexion: sqlite3.Connection, id_usuario: int) -> Usuario | None:
    """Devuelve el usuario con su rol y su `activo` actuales, o None si no existe."""
    fila = conexion.execute(_SELECT_POR_ID, (id_usuario,)).fetchone()
    return None if fila is None else _usuario_desde_fila(fila)


def _usuario_desde_fila(fila: _FilaUsuario) -> Usuario:
    id_usuario, username, rol, profesional_id, activo = fila
    return Usuario(
        id=id_usuario,
        username=username,
        rol=Rol(rol),
        profesional_id=profesional_id,
        activo=bool(activo),
    )
