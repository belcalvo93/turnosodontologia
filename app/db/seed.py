"""Seed de desarrollo: el usuario `admin_demo` (C-03, design §9).

Recibe el hash ya calculado: `db` no importa nada de `api` (KB 08).
"""

import sqlite3

from app.db.conexion import transaccion
from app.domain.usuarios import Rol

USERNAME_ADMIN_DEMO = "admin_demo"

# ON CONFLICT ... DO NOTHING: idempotente y nunca pisa la contraseña de un admin_demo existente.
_INSERTAR_ADMIN_DEMO = """
    INSERT INTO usuario (username, password_hash, rol, profesional_id, activo)
    VALUES (?, ?, ?, NULL, 1)
    ON CONFLICT(username) DO NOTHING
"""


def sembrar_admin_demo(conexion: sqlite3.Connection, password_hash: str) -> None:
    """Crea `admin_demo` (administración, activo) con `password_hash` si todavía no existe."""
    with transaccion(conexion):
        conexion.execute(
            _INSERTAR_ADMIN_DEMO, (USERNAME_ADMIN_DEMO, password_hash, Rol.ADMINISTRACION.value)
        )
