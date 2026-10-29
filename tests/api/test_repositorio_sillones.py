"""Tests del esquema SQLite de sillones (C-05)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """Conexión a una base temporal por test con el esquema ya aplicado."""
    ruta = tmp_path / "sillones.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_abierta:
        yield conexion_abierta


def test_inicializar_esquema_crea_tabla_sillon_idempotente(tmp_path: Path) -> None:
    ruta = tmp_path / "sillones_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion_abierta:
        fila = conexion_abierta.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sillon'"
        ).fetchone()
        assert fila == ("sillon",)


def test_tabla_sillon_rechaza_nombre_vacio(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO sillon (nombre) VALUES ('')")


def test_tabla_sillon_rechaza_nombre_solo_espacios(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO sillon (nombre) VALUES ('   ')")


def test_tabla_sillon_rechaza_nombre_duplicado(conexion: sqlite3.Connection) -> None:
    conexion.execute("INSERT INTO sillon (nombre) VALUES ('Sillón 1 (ficticio)')")

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO sillon (nombre) VALUES ('Sillón 1 (ficticio)')")


@pytest.mark.parametrize("activo_invalido", [-1, 2])
def test_tabla_sillon_rechaza_activo_fuera_de_cero_y_uno(
    conexion: sqlite3.Connection, activo_invalido: int
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO sillon (nombre, activo) VALUES (?, ?)",
            ("Sillón 1 (ficticio)", activo_invalido),
        )


def test_tabla_sillon_asigna_activo_uno_por_defecto(conexion: sqlite3.Connection) -> None:
    cursor = conexion.execute(
        "INSERT INTO sillon (nombre) VALUES ('Sillón 1 (ficticio)')"
    )

    assert cursor.lastrowid is not None
    fila = conexion.execute(
        "SELECT activo FROM sillon WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    assert fila == (1,)
