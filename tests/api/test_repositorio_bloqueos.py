"""Tests del esquema y repositorio SQLite de bloqueos (C-09)."""

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio_bloqueos import (
    crear_bloqueo,
    eliminar_bloqueo,
    listar_bloqueos,
)
from app.db.repositorio_profesionales import crear_profesional
from app.domain.errores import DatoInvalido
from app.domain.models import Bloqueo


def test_inicializar_esquema_crea_tabla_e_indice_bloqueo_idempotente(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "bloqueos_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        tabla = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'bloqueo'"
        ).fetchone()
        indice = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'idx_bloqueo_alcance_recurso_inicio'"
        ).fetchone()
        assert tabla == ("bloqueo",)
        assert indice == ("idx_bloqueo_alcance_recurso_inicio",)


def test_tabla_bloqueo_rechaza_alcance_o_intervalo_invalido(tmp_path: Path) -> None:
    ruta = tmp_path / "bloqueos_checks.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                """
                INSERT INTO bloqueo (alcance, recurso_id, inicio, fin, motivo)
                VALUES ('consultorio', 1, '2026-11-10T09:00:00', '2026-11-10T12:00:00', 'Feriado')
                """
            )
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                """
                INSERT INTO bloqueo (alcance, recurso_id, inicio, fin, motivo)
                VALUES ('profesional', 1, '2026-11-10T12:00:00', '2026-11-10T09:00:00', 'Error')
                """
            )


def test_crear_listar_y_eliminar_bloqueo_de_profesional(tmp_path: Path) -> None:
    ruta = tmp_path / "bloqueos_crud.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            prof = crear_profesional(
                conexion, nombre="Odontólogo", apellido="Ficticio A"
            )
            assert prof.id is not None
            creado = crear_bloqueo(
                conexion,
                Bloqueo(
                    alcance="profesional",
                    recurso_id=prof.id,
                    inicio=datetime(2026, 11, 10, 9, 0),
                    fin=datetime(2026, 11, 10, 13, 0),
                    motivo="Vacaciones",
                ),
            )

        assert creado == Bloqueo(
            id=1,
            alcance="profesional",
            recurso_id=prof.id,
            inicio=datetime(2026, 11, 10, 9, 0),
            fin=datetime(2026, 11, 10, 13, 0),
            motivo="Vacaciones",
        )
        assert listar_bloqueos(conexion) == [creado]

        with transaccion(conexion):
            assert eliminar_bloqueo(conexion, 1) is True
            assert eliminar_bloqueo(conexion, 1) is False

        assert listar_bloqueos(conexion) == []


def test_crear_bloqueo_con_profesional_inexistente_lanza_dato_invalido(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "bloqueos_inexistente.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with pytest.raises(DatoInvalido):
            with transaccion(conexion):
                crear_bloqueo(
                    conexion,
                    Bloqueo(
                        alcance="profesional",
                        recurso_id=999,
                        inicio=datetime(2026, 11, 10, 9, 0),
                        fin=datetime(2026, 11, 10, 13, 0),
                        motivo="Vacaciones",
                    ),
                )
