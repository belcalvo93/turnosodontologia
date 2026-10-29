"""Tests del esquema y repositorio SQLite de pacientes (C-06)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema


def test_inicializar_esquema_crea_tabla_paciente_idempotente(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        fila = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'paciente'"
        ).fetchone()
        assert fila == ("paciente",)


def test_tabla_paciente_rechaza_nombre_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_nombre_vacio.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("", "Pérez", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_nombre_solo_espacios(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_nombre_espacios.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("   ", "Pérez", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_apellido_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_apellido_vacio.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_apellido_solo_espacios(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_apellido_espacios.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "   ", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_dni_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_vacio.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", ""),
        )


def test_tabla_paciente_rechaza_dni_solo_espacios(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_espacios.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", "   "),
        )


def test_tabla_paciente_rechaza_dni_duplicado(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_duplicado.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", "30111222 (ficticio)"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
                ("Luis", "Gómez", "30111222 (ficticio)"),
            )


def test_tabla_paciente_rechaza_dni_null(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_null.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", None),
        )


def test_tabla_paciente_acepta_opcionales_null(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_opcionales_null.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", "30111222 (ficticio)"),
        )
        fila = conexion.execute(
            "SELECT nombre, apellido, dni, telefono, obra_social, nro_afiliado "
            "FROM paciente WHERE id = ?",
            (1,),
        ).fetchone()
        assert fila == ("Ana", "Pérez", "30111222 (ficticio)", None, None, None)
