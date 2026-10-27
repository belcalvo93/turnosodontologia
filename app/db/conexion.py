"""Conexión SQLite y transacciones (C-01)."""

import sqlite3

from app.config import Config

# Los PRAGMA no aceptan parámetros ligados; se usan literales fijos (sin interpolar SQL).
_PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys=ON"
_PRAGMA_BUSY_TIMEOUT = "PRAGMA busy_timeout=5000"


def abrir_conexion(config: Config) -> sqlite3.Connection:
    """Abre una conexión con claves foráneas activas y espera ante locks de escritura.

    `isolation_level=None` deja la conexión en autocommit: sqlite3 no abre
    transacciones implícitas y las controla `transaccion()` con BEGIN IMMEDIATE.
    """
    conexion = sqlite3.connect(config.database_path, isolation_level=None)
    conexion.execute(_PRAGMA_FOREIGN_KEYS)
    conexion.execute(_PRAGMA_BUSY_TIMEOUT)
    return conexion
