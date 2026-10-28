"""Dependencias de FastAPI compartidas por los routers (C-03)."""

import sqlite3
from collections.abc import Iterator

from fastapi import Request

from app.db.conexion import abrir_conexion


def obtener_conexion(request: Request) -> Iterator[sqlite3.Connection]:
    """Abre una conexión propia del request y la cierra al terminar, aunque el endpoint falle.

    FastAPI puede abrirla y cerrarla en hilos distintos del threadpool; por eso
    `abrir_conexion` usa `check_same_thread=False` (design §5).
    """
    conexion = abrir_conexion(request.app.state.config.database_path)
    try:
        yield conexion
    finally:
        conexion.close()
