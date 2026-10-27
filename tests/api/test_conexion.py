"""Tests de la conexión SQLite: PRAGMAs y claves foráneas (C-01)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.config import Config, cargar_config
from app.db.conexion import abrir_conexion


def _config_temporal(ruta: Path) -> Config:
    return cargar_config(entorno={"DATABASE_URL": str(ruta)})


def test_abrir_conexion_hace_cumplir_las_claves_foraneas(tmp_path: Path) -> None:
    config = _config_temporal(tmp_path / "turnos_test.db")

    with closing(abrir_conexion(config)) as conexion:
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
