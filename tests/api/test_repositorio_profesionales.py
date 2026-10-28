"""Tests del esquema y repositorio SQLite de profesionales (C-04)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio_profesionales import (
    actualizar_profesional,
    crear_profesional,
    listar_profesionales,
    obtener_profesional_por_id,
)
from app.domain.models import Profesional


def test_inicializar_esquema_crea_tabla_profesional_idempotente(tmp_path: Path) -> None:
    ruta = tmp_path / "profesionales_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        fila = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'profesional'"
        ).fetchone()
        assert fila == ("profesional",)


def test_tabla_profesional_rechaza_nombre_o_apellido_vacios_y_activo_invalido(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "profesionales_check.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO profesional (nombre, apellido) VALUES ('   ', 'Pérez')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO profesional (nombre, apellido) VALUES ('Juan', '')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO profesional (nombre, apellido, activo) VALUES ('Juan', 'Pérez', 2)"
            )


def test_crear_y_obtener_profesional_por_id(tmp_path: Path) -> None:
    ruta = tmp_path / "profesionales_crud.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_profesional(
                conexion,
                nombre="Odontólogo",
                apellido="Ficticio A",
                matricula="0001 (ficticia)",
            )

        assert creado == Profesional(
            id=1,
            nombre="Odontólogo",
            apellido="Ficticio A",
            matricula="0001 (ficticia)",
            activo=True,
        )
        assert obtener_profesional_por_id(conexion, 1) == creado
        assert obtener_profesional_por_id(conexion, 999) is None


def test_listar_profesionales_devuelve_activos_e_inactivos_ordenados_por_id(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "profesionales_lista.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            primero = crear_profesional(
                conexion, nombre="Juan", apellido="Pérez", matricula=None
            )
            segundo = crear_profesional(
                conexion,
                nombre="María",
                apellido="Gómez",
                matricula="0002 (ficticia)",
            )
            assert segundo.id is not None
            desactivado = actualizar_profesional(
                conexion, segundo.id, activo=False
            )

        assert desactivado == Profesional(
            id=segundo.id,
            nombre="María",
            apellido="Gómez",
            matricula="0002 (ficticia)",
            activo=False,
        )
        lista = listar_profesionales(conexion)
        assert lista == [primero, desactivado]


def test_actualizar_profesional_modifica_campos_y_devuelve_none_si_no_existe(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "profesionales_update.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_profesional(
                conexion,
                nombre="Carlos",
                apellido="López",
                matricula="0003 (ficticia)",
            )
            assert creado.id is not None
            actualizado = actualizar_profesional(
                conexion,
                creado.id,
                nombre="Carlos Alberto",
                apellido="López",
                matricula=None,
                activo=True,
            )

        assert actualizado == Profesional(
            id=creado.id,
            nombre="Carlos Alberto",
            apellido="López",
            matricula=None,
            activo=True,
        )
        assert actualizar_profesional(conexion, 9999, activo=False) is None
