"""Acceso a la tabla `usuario` para la gestión administrativa (C-07).

Solo consultas parametrizadas (regla dura 4). No abre transacciones: escribir
dentro de `transaccion()` lo decide quien llama. El login y el seed siguen viviendo
en `app/db/repositorio.py`, que este módulo no modifica.
"""

import sqlite3
from typing import Final

from app.db.repositorio import buscar_usuario_por_id, insertar_usuario
from app.domain.errores import UsernameDuplicado
from app.domain.usuarios import Rol, Usuario

_SELECT_TODOS: Final = """
    SELECT id, username, rol, profesional_id, activo
    FROM usuario
    ORDER BY id ASC
"""
# Dos UPDATE literales para no leer ni reescribir el hash cuando no se resetea.
_UPDATE_CON_HASH: Final = """
    UPDATE usuario
    SET password_hash = ?, rol = ?, profesional_id = ?, activo = ?
    WHERE id = ?
"""
_UPDATE_SIN_HASH: Final = """
    UPDATE usuario
    SET rol = ?, profesional_id = ?, activo = ?
    WHERE id = ?
"""

_SIN_CAMBIO: Final = object()
_FilaUsuario = tuple[int, str, str, int | None, int]
_MENSAJE_USERNAME_DUPLICADO = "Ya existe un usuario con ese nombre de usuario."


def crear_usuario(
    conexion: sqlite3.Connection,
    *,
    username: str,
    password_hash: str,
    rol: Rol,
    profesional_id: int | None = None,
    activo: bool = True,
) -> Usuario:
    """Inserta un usuario y devuelve la entidad con su id asignado.

    Reutiliza `insertar_usuario` de `repositorio.py` para no duplicar el SQL del
    alta y traduce la violación de `UNIQUE(username)` a `UsernameDuplicado`.
    """
    try:
        id_usuario = insertar_usuario(
            conexion,
            username=username,
            password_hash=password_hash,
            rol=rol,
            profesional_id=profesional_id,
            activo=activo,
        )
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    return Usuario(
        id=id_usuario,
        username=username,
        rol=rol,
        profesional_id=profesional_id,
        activo=activo,
    )


def listar_usuarios(conexion: sqlite3.Connection) -> list[Usuario]:
    """Devuelve todos los usuarios (activos e inactivos) ordenados por id."""
    filas = conexion.execute(_SELECT_TODOS).fetchall()
    return [_usuario_desde_fila(fila) for fila in filas]


def actualizar_usuario(
    conexion: sqlite3.Connection,
    id_usuario: int,
    *,
    password_hash: str | object = _SIN_CAMBIO,
    rol: Rol | object = _SIN_CAMBIO,
    profesional_id: int | None | object = _SIN_CAMBIO,
    activo: bool | object = _SIN_CAMBIO,
) -> Usuario | None:
    """Actualiza los campos provistos del usuario y lo devuelve, o None si no existe.

    El hash se conserva sin leerlo cuando `password_hash` se omite: por eso hay dos
    UPDATE literales en lugar de uno que reescriba todas las columnas.
    """
    actual = buscar_usuario_por_id(conexion, id_usuario)
    if actual is None:
        return None
    nuevo_rol = actual.rol if rol is _SIN_CAMBIO else _validar_rol(rol)
    nuevo_profesional_id = _resolver_opcional(actual.profesional_id, profesional_id)
    nuevo_activo = actual.activo if activo is _SIN_CAMBIO else bool(activo)
    try:
        if password_hash is _SIN_CAMBIO:
            conexion.execute(
                _UPDATE_SIN_HASH,
                (nuevo_rol.value, nuevo_profesional_id, int(nuevo_activo), id_usuario),
            )
        else:
            conexion.execute(
                _UPDATE_CON_HASH,
                (
                    str(password_hash),
                    nuevo_rol.value,
                    nuevo_profesional_id,
                    int(nuevo_activo),
                    id_usuario,
                ),
            )
    except sqlite3.IntegrityError as error:
        _traducir_integridad(error)
        raise
    return Usuario(
        id=id_usuario,
        username=actual.username,
        rol=nuevo_rol,
        profesional_id=nuevo_profesional_id,
        activo=nuevo_activo,
    )


def _resolver_opcional(actual: int | None, cambio: int | None | object) -> int | None:
    if cambio is _SIN_CAMBIO:
        return actual
    return None if cambio is None else int(cambio)  # type: ignore[arg-type]


def _validar_rol(rol: Rol | object) -> Rol:
    if not isinstance(rol, Rol):
        raise TypeError("rol debe ser un valor de Rol.")
    return rol


def _usuario_desde_fila(fila: _FilaUsuario) -> Usuario:
    id_usuario, username, rol, profesional_id, activo = fila
    return Usuario(
        id=id_usuario,
        username=username,
        rol=Rol(rol),
        profesional_id=profesional_id,
        activo=bool(activo),
    )


def _traducir_integridad(error: sqlite3.IntegrityError) -> None:
    """Convierte la violación de UNIQUE(username) en UsernameDuplicado; deja pasar el resto."""
    if "UNIQUE" in str(error):
        raise UsernameDuplicado(_MENSAJE_USERNAME_DUPLICADO) from error
