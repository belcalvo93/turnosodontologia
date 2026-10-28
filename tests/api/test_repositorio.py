"""Tests del repositorio de usuarios sobre SQLite (C-03)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema
from app.db.repositorio import buscar_credenciales, buscar_usuario_por_id, insertar_usuario
from app.domain.usuarios import Rol, Usuario

# Datos ficticios (RN-PAC-03). El hash es un placeholder: el repositorio no lo interpreta.
HASH_FICTICIO = "$argon2id$hash-ficticio"


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    ruta = tmp_path / "repositorio.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_db:
        yield conexion_db


def test_insertar_usuario_devuelve_el_id(conexion: sqlite3.Connection) -> None:
    id_usuario = insertar_usuario(
        conexion, username="recepcion_ficticia", password_hash=HASH_FICTICIO, rol=Rol.RECEPCION
    )

    fila = conexion.execute("SELECT username FROM usuario WHERE id = ?", (id_usuario,)).fetchone()
    assert fila == ("recepcion_ficticia",)


def test_insertar_dos_usuarios_devuelve_ids_distintos(conexion: sqlite3.Connection) -> None:
    primero = insertar_usuario(
        conexion, username="admin_ficticio", password_hash=HASH_FICTICIO, rol=Rol.ADMINISTRACION
    )
    segundo = insertar_usuario(
        conexion, username="recepcion_ficticia", password_hash=HASH_FICTICIO, rol=Rol.RECEPCION
    )

    assert primero != segundo


def test_odontologo_inactivo_con_profesional_se_guarda_y_se_recupera(
    conexion: sqlite3.Connection,
) -> None:
    id_usuario = insertar_usuario(
        conexion,
        username="odontologo_ficticio",
        password_hash=HASH_FICTICIO,
        rol=Rol.ODONTOLOGO,
        profesional_id=7,
        activo=False,
    )

    assert buscar_usuario_por_id(conexion, id_usuario) == Usuario(
        id=id_usuario,
        username="odontologo_ficticio",
        rol=Rol.ODONTOLOGO,
        profesional_id=7,
        activo=False,
    )


def test_buscar_usuario_por_id_inexistente_devuelve_none(conexion: sqlite3.Connection) -> None:
    assert buscar_usuario_por_id(conexion, 999) is None


def test_username_con_comillas_se_trata_como_dato(conexion: sqlite3.Connection) -> None:
    insertar_usuario(
        conexion, username="recepcion_ficticia", password_hash=HASH_FICTICIO, rol=Rol.RECEPCION
    )

    assert buscar_credenciales(conexion, "' OR '1'='1") is None


def test_buscar_credenciales_devuelve_usuario_y_hash(conexion: sqlite3.Connection) -> None:
    id_usuario = insertar_usuario(
        conexion, username="recepcion_ficticia", password_hash=HASH_FICTICIO, rol=Rol.RECEPCION
    )

    assert buscar_credenciales(conexion, "recepcion_ficticia") == (
        Usuario(
            id=id_usuario,
            username="recepcion_ficticia",
            rol=Rol.RECEPCION,
            profesional_id=None,
            activo=True,
        ),
        HASH_FICTICIO,
    )


def test_buscar_credenciales_de_username_inexistente_devuelve_none(
    conexion: sqlite3.Connection,
) -> None:
    assert buscar_credenciales(conexion, "no_existe_ficticio") is None


def test_buscar_usuario_por_id_refleja_rol_y_activo_actuales(
    conexion: sqlite3.Connection,
) -> None:
    id_usuario = insertar_usuario(
        conexion, username="recepcion_ficticia", password_hash=HASH_FICTICIO, rol=Rol.RECEPCION
    )
    conexion.execute(
        "UPDATE usuario SET rol = ?, activo = ? WHERE id = ?", ("administracion", 0, id_usuario)
    )

    usuario = buscar_usuario_por_id(conexion, id_usuario)

    assert usuario is not None
    assert usuario.rol is Rol.ADMINISTRACION
    assert usuario.activo is False
