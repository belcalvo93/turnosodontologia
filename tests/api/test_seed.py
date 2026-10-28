"""Tests del seed de desarrollo `sembrar_admin_demo` sobre una base temporal (C-03)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema
from app.db.repositorio import insertar_usuario
from app.db.seed import sembrar_admin_demo
from app.domain.usuarios import Rol

# Hashes placeholder: `sembrar_admin_demo` recibe el hash ya calculado y no lo interpreta.
HASH_FICTICIO = "$argon2id$hash-ficticio-1"
OTRO_HASH_FICTICIO = "$argon2id$hash-ficticio-2"

_SELECT_USUARIOS = (
    "SELECT username, password_hash, rol, profesional_id, activo FROM usuario ORDER BY id"
)


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    ruta = tmp_path / "seed.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_db:
        yield conexion_db


def test_la_primera_llamada_crea_un_unico_admin_demo_activo(
    conexion: sqlite3.Connection,
) -> None:
    sembrar_admin_demo(conexion, HASH_FICTICIO)

    assert conexion.execute(_SELECT_USUARIOS).fetchall() == [
        ("admin_demo", HASH_FICTICIO, "administracion", None, 1)
    ]


def test_la_segunda_llamada_no_duplica_ni_cambia_el_hash(conexion: sqlite3.Connection) -> None:
    sembrar_admin_demo(conexion, HASH_FICTICIO)

    sembrar_admin_demo(conexion, OTRO_HASH_FICTICIO)

    assert conexion.execute(_SELECT_USUARIOS).fetchall() == [
        ("admin_demo", HASH_FICTICIO, "administracion", None, 1)
    ]


def test_no_modifica_un_admin_demo_existente_aunque_este_inactivo_y_con_otro_rol(
    conexion: sqlite3.Connection,
) -> None:
    insertar_usuario(
        conexion,
        username="admin_demo",
        password_hash=HASH_FICTICIO,
        rol=Rol.RECEPCION,
        activo=False,
    )

    sembrar_admin_demo(conexion, OTRO_HASH_FICTICIO)

    assert conexion.execute(_SELECT_USUARIOS).fetchall() == [
        ("admin_demo", HASH_FICTICIO, "recepcion", None, 0)
    ]


def test_agrega_admin_demo_sin_tocar_a_los_demas_usuarios(conexion: sqlite3.Connection) -> None:
    insertar_usuario(
        conexion, username="recepcion_ficticia", password_hash=HASH_FICTICIO, rol=Rol.RECEPCION
    )

    sembrar_admin_demo(conexion, OTRO_HASH_FICTICIO)

    assert conexion.execute(_SELECT_USUARIOS).fetchall() == [
        ("recepcion_ficticia", HASH_FICTICIO, "recepcion", None, 1),
        ("admin_demo", OTRO_HASH_FICTICIO, "administracion", None, 1),
    ]


def test_el_seed_queda_confirmado_y_lo_ve_otra_conexion(tmp_path: Path) -> None:
    ruta = tmp_path / "seed_confirmado.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_seed:
        sembrar_admin_demo(conexion_seed, HASH_FICTICIO)

    with closing(abrir_conexion(ruta)) as otra_conexion:
        assert otra_conexion.execute("SELECT username FROM usuario").fetchall() == [
            ("admin_demo",)
        ]
