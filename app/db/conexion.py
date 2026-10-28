"""Conexión SQLite, transacciones y esquema (C-01).

Esta capa no conoce la configuración de la aplicación: recibe rutas explícitas.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Los PRAGMA no aceptan parámetros ligados; se usan literales fijos (sin interpolar SQL).
_PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys=ON"
_PRAGMA_BUSY_TIMEOUT = "PRAGMA busy_timeout=5000"
_ESQUEMA_POR_DEFECTO = Path(__file__).with_name("esquema.sql")


def abrir_conexion(ruta: Path) -> sqlite3.Connection:
    """Abre una conexión con claves foráneas activas y espera ante locks de escritura.

    `isolation_level=None` deja la conexión en autocommit: sqlite3 no abre
    transacciones implícitas y las controla `transaccion()` con BEGIN IMMEDIATE.

    `check_same_thread=False` permite usar la conexión desde el hilo del pool que
    atiende el endpoint síncrono de FastAPI. Es seguro porque cada request abre
    su propia conexión y no se comparte entre requests.
    """
    conexion = sqlite3.connect(ruta, isolation_level=None, check_same_thread=False)
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


def inicializar_esquema(ruta_base: Path, ruta_esquema: Path | None = None) -> None:
    """Aplica el esquema sobre la base indicada, en su propia conexión.

    `executescript` confirma implícitamente, por eso no se ejecuta dentro de una
    transacción de request. El script debe ser idempotente (CREATE TABLE IF NOT EXISTS).
    """
    sentencias = (ruta_esquema or _ESQUEMA_POR_DEFECTO).read_text(encoding="utf-8")
    conexion = abrir_conexion(ruta_base)
    try:
        conexion.executescript(sentencias)
    finally:
        conexion.close()
