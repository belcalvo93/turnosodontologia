"""Tests de la tabla `usuario` en esquema.sql (C-03)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema

# Datos ficticios (RN-PAC-03). El hash es un placeholder: el esquema no lo interpreta.
HASH_FICTICIO = "$argon2id$hash-ficticio"

_INSERTAR = (
    "INSERT INTO usuario (username, password_hash, rol, profesional_id) VALUES (?, ?, ?, ?)"
)


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    ruta = tmp_path / "usuarios.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_db:
        yield conexion_db


def test_la_tabla_usuario_existe_despues_del_arranque(conexion: sqlite3.Connection) -> None:
    fila = conexion.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", ("usuario",)
    ).fetchone()

    assert fila == ("usuario",)


def test_username_duplicado_lanza_integrity_error(conexion: sqlite3.Connection) -> None:
    conexion.execute(_INSERTAR, ("recepcion_ficticia", HASH_FICTICIO, "recepcion", None))

    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        conexion.execute(_INSERTAR, ("recepcion_ficticia", HASH_FICTICIO, "administracion", None))


def test_rol_fuera_de_los_tres_roles_lanza_integrity_error(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        conexion.execute(_INSERTAR, ("paciente_ficticio", HASH_FICTICIO, "paciente", None))

    assert conexion.execute("SELECT COUNT(*) FROM usuario").fetchone() == (0,)


def test_administrador_sin_profesional_se_inserta(conexion: sqlite3.Connection) -> None:
    conexion.execute(_INSERTAR, ("admin_ficticio", HASH_FICTICIO, "administracion", None))

    fila = conexion.execute(
        "SELECT rol, profesional_id, activo FROM usuario WHERE username = ?", ("admin_ficticio",)
    ).fetchone()
    assert fila == ("administracion", None, 1)


def test_profesional_id_no_tiene_clave_foranea(conexion: sqlite3.Connection) -> None:
    # abrir_conexion activa foreign_keys; aun así se acepta un profesional inexistente
    # porque la validación queda en la aplicación (C-07).
    assert conexion.execute("PRAGMA foreign_keys").fetchone() == (1,)

    conexion.execute(_INSERTAR, ("odontologo_ficticio", HASH_FICTICIO, "odontologo", 999))

    assert conexion.execute("PRAGMA foreign_key_list(usuario)").fetchall() == []


def test_activo_solo_admite_cero_o_uno(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        conexion.execute(
            "INSERT INTO usuario (username, password_hash, rol, activo) VALUES (?, ?, ?, ?)",
            ("recepcion_ficticia", HASH_FICTICIO, "recepcion", 2),
        )


def test_aplicar_el_esquema_dos_veces_no_falla_ni_borra_usuarios(tmp_path: Path) -> None:
    ruta = tmp_path / "dos_veces.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_db:
        conexion_db.execute(_INSERTAR, ("admin_ficticio", HASH_FICTICIO, "administracion", None))

    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion_db:
        assert conexion_db.execute("SELECT COUNT(*) FROM usuario").fetchone() == (1,)
