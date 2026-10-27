"""Tests de la conexión SQLite: PRAGMAs, transacciones y esquema (C-01)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion


def test_abrir_conexion_hace_cumplir_las_claves_foraneas(tmp_path: Path) -> None:
    ruta = tmp_path / "turnos_test.db"

    with closing(abrir_conexion(ruta)) as conexion:
        # El test crea sus propias tablas: en C-01 esquema.sql solo tiene comentarios.
        conexion.executescript(
            """
            CREATE TABLE padre (id INTEGER PRIMARY KEY);
            CREATE TABLE hija (
                id INTEGER PRIMARY KEY,
                padre_id INTEGER NOT NULL REFERENCES padre (id)
            );
            """
        )
        conexion.execute("INSERT INTO padre (id) VALUES (1)")
        conexion.execute("INSERT INTO hija (id, padre_id) VALUES (1, 1)")

        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute("INSERT INTO hija (id, padre_id) VALUES (2, 99)")

        assert conexion.execute("SELECT COUNT(*) FROM hija").fetchone()[0] == 1


def test_transaccion_confirma_al_salir_sin_excepcion(tmp_path: Path) -> None:
    ruta = tmp_path / "commit.db"

    with closing(abrir_conexion(ruta)) as conexion:
        conexion.execute("CREATE TABLE prueba (id INTEGER PRIMARY KEY)")

        with transaccion(conexion):
            conexion.execute("INSERT INTO prueba (id) VALUES (1)")

    with closing(abrir_conexion(ruta)) as nueva:
        assert nueva.execute("SELECT COUNT(*) FROM prueba").fetchone()[0] == 1


def test_transaccion_revierte_ante_excepcion_y_propaga(tmp_path: Path) -> None:
    ruta = tmp_path / "rollback.db"

    with closing(abrir_conexion(ruta)) as conexion:
        conexion.execute("CREATE TABLE prueba (id INTEGER PRIMARY KEY)")

        with pytest.raises(RuntimeError, match="falla simulada"):
            with transaccion(conexion):
                conexion.execute("INSERT INTO prueba (id) VALUES (1)")
                raise RuntimeError("falla simulada")

        assert conexion.execute("SELECT COUNT(*) FROM prueba").fetchone()[0] == 0


def test_inicializar_esquema_se_puede_aplicar_dos_veces(tmp_path: Path) -> None:
    ruta = tmp_path / "esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)


def test_inicializar_esquema_deja_la_base_usable(tmp_path: Path) -> None:
    ruta = tmp_path / "esquema.db"

    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        assert conexion.execute("SELECT 1").fetchone()[0] == 1
