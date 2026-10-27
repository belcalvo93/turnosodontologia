"""Conexión SQLite y transacciones (C-01)."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.config import Config

# Los PRAGMA no aceptan parámetros ligados; se usan literales fijos (sin interpolar SQL).
_PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys=ON"
_PRAGMA_BUSY_TIMEOUT = "PRAGMA busy_timeout=5000"
_ESQUEMA_POR_DEFECTO = Path(__file__).with_name("esquema.sql")


def abrir_conexion(config: Config) -> sqlite3.Connection:
    """Abre una conexión con claves foráneas activas y espera ante locks de escritura.

    `isolation_level=None` deja la conexión en autocommit: sqlite3 no abre
    transacciones implícitas y las controla `transaccion()` con BEGIN IMMEDIATE.
    """
    conexion = sqlite3.connect(config.database_path, isolation_level=None)
    conexion.execute(_PRAGMA_FOREIGN_KEYS)
    conexion.execute(_PRAGMA_BUSY_TIMEOUT)
    return conexion


@contextmanager
def transaccion(conexion: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Transacción de escritura atómica sobre una conexión en autocommit.

    Emite BEGIN IMMEDIATE (toma el lock de escritura al inicio), confirma al
    salir sin excepción y revierte re-lanzando si el bloque falla.
    """
    conexion.execute("BEGIN IMMEDIATE")
    try:
        yield conexion
    except BaseException:
        conexion.rollback()
        raise
    else:
        conexion.commit()


def inicializar_esquema(config: Config, ruta: Path | None = None) -> None:
    """Aplica el esquema sobre la base configurada, en su propia conexión.

    `executescript` confirma implícitamente, por eso no se ejecuta dentro de una
    transacción de request. El script debe ser idempotente (CREATE TABLE IF NOT EXISTS).
    """
    sentencias = (ruta or _ESQUEMA_POR_DEFECTO).read_text(encoding="utf-8")
    conexion = abrir_conexion(config)
    try:
        conexion.executescript(sentencias)
    finally:
        conexion.close()
