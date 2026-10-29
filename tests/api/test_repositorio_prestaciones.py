"""Tests del esquema SQLite de prestaciones (C-05)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """Conexión a una base temporal por test con el esquema ya aplicado."""
    ruta = tmp_path / "prestaciones.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_abierta:
        yield conexion_abierta


def test_inicializar_esquema_crea_tabla_prestacion_idempotente(tmp_path: Path) -> None:
    ruta = tmp_path / "prestaciones_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion_abierta:
        fila = conexion_abierta.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'prestacion'"
        ).fetchone()
        assert fila == ("prestacion",)


def test_tabla_prestacion_rechaza_nombre_vacio(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos) VALUES ('', 30)"
        )


def test_tabla_prestacion_rechaza_nombre_solo_espacios(
    conexion: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos) VALUES ('   ', 30)"
        )


def test_tabla_prestacion_rechaza_nombre_duplicado(conexion: sqlite3.Connection) -> None:
    conexion.execute(
        "INSERT INTO prestacion (nombre, duracion_minutos) VALUES ('Consulta ficticia', 30)"
    )

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos)"
            " VALUES ('Consulta ficticia', 45)"
        )


@pytest.mark.parametrize("activa_invalida", [-1, 2])
def test_tabla_prestacion_rechaza_activa_fuera_de_cero_y_uno(
    conexion: sqlite3.Connection, activa_invalida: int
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos, activa)"
            " VALUES (?, ?, ?)",
            ("Consulta ficticia", 30, activa_invalida),
        )


def test_tabla_prestacion_rechaza_duracion_cero(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos)"
            " VALUES ('Consulta ficticia', 0)"
        )


@pytest.mark.parametrize("duracion_negativa", [-1, -30])
def test_tabla_prestacion_rechaza_duracion_negativa(
    conexion: sqlite3.Connection, duracion_negativa: int
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos) VALUES (?, ?)",
            ("Consulta ficticia", duracion_negativa),
        )


def test_tabla_prestacion_asigna_activa_uno_por_defecto(
    conexion: sqlite3.Connection,
) -> None:
    cursor = conexion.execute(
        "INSERT INTO prestacion (nombre, duracion_minutos)"
        " VALUES ('Consulta ficticia', 30)"
    )

    assert cursor.lastrowid is not None
    fila = conexion.execute(
        "SELECT activa FROM prestacion WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    assert fila == (1,)
