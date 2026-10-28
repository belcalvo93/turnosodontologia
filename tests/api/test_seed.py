"""Tests del seed de desarrollo `sembrar_admin_demo` sobre una base temporal (C-03)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Config, cargar_config
from app.db.conexion import abrir_conexion, inicializar_esquema
from app.db.repositorio import insertar_usuario
from app.db.seed import sembrar_admin_demo
from app.domain.usuarios import Rol
from app.main import create_app

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


# --- Seed en el arranque (lifespan de create_app) ---

CLAVE_DEMO_FICTICIA = "clave-demo-ficticia"


def _config_de_arranque(ruta_base: Path, entorno: dict[str, str]) -> Config:
    return cargar_config(entorno={"DATABASE_URL": str(ruta_base), **entorno})


def _arrancar(config: Config) -> None:
    """Arranca y apaga la app: el `with` dispara el lifespan."""
    with TestClient(create_app(config)):
        pass


def _usuarios_en(ruta_base: Path) -> list[tuple[object, ...]]:
    with closing(abrir_conexion(ruta_base)) as conexion_db:
        return conexion_db.execute(_SELECT_USUARIOS).fetchall()


def test_en_development_con_la_variable_crea_admin_demo_y_permite_el_login(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "arranque.db"
    config = _config_de_arranque(
        ruta, {"APP_ENV": "development", "SEED_ADMIN_PASSWORD": CLAVE_DEMO_FICTICIA}
    )

    with TestClient(create_app(config)) as cliente:
        respuesta = cliente.post(
            "/auth/login", json={"username": "admin_demo", "password": CLAVE_DEMO_FICTICIA}
        )

    assert respuesta.status_code == 200
    [(username, password_hash, rol, profesional_id, activo)] = _usuarios_en(ruta)
    assert (username, rol, profesional_id, activo) == ("admin_demo", "administracion", None, 1)
    assert password_hash.startswith("$argon2id$")


def test_dos_arranques_sobre_la_misma_base_dejan_un_solo_admin_demo(tmp_path: Path) -> None:
    ruta = tmp_path / "arranque.db"
    config = _config_de_arranque(
        ruta, {"APP_ENV": "development", "SEED_ADMIN_PASSWORD": CLAVE_DEMO_FICTICIA}
    )
    _arrancar(config)
    despues_del_primero = _usuarios_en(ruta)

    _arrancar(config)

    assert len(despues_del_primero) == 1
    assert _usuarios_en(ruta) == despues_del_primero


def test_en_test_con_la_variable_no_crea_usuarios(tmp_path: Path) -> None:
    ruta = tmp_path / "arranque.db"

    _arrancar(
        _config_de_arranque(ruta, {"APP_ENV": "test", "SEED_ADMIN_PASSWORD": CLAVE_DEMO_FICTICIA})
    )

    assert _usuarios_en(ruta) == []


def test_en_development_sin_la_variable_arranca_y_no_crea_usuarios(tmp_path: Path) -> None:
    ruta = tmp_path / "arranque.db"

    _arrancar(_config_de_arranque(ruta, {"APP_ENV": "development"}))

    assert _usuarios_en(ruta) == []


def test_en_production_con_la_variable_no_crea_usuarios(tmp_path: Path) -> None:
    ruta = tmp_path / "arranque.db"
    entorno = {
        "APP_ENV": "production",
        "JWT_SECRET": "secreto-ficticio-de-test-con-32-caracteres-o-mas",
        "SEED_ADMIN_PASSWORD": CLAVE_DEMO_FICTICIA,
    }

    _arrancar(_config_de_arranque(ruta, entorno))

    assert _usuarios_en(ruta) == []


def test_la_contrasena_del_seed_no_queda_en_el_archivo_de_la_base(tmp_path: Path) -> None:
    ruta = tmp_path / "arranque.db"

    _arrancar(
        _config_de_arranque(
            ruta, {"APP_ENV": "development", "SEED_ADMIN_PASSWORD": CLAVE_DEMO_FICTICIA}
        )
    )

    assert CLAVE_DEMO_FICTICIA.encode() not in ruta.read_bytes()


def test_rearrancar_con_otra_contrasena_no_cambia_la_de_admin_demo(tmp_path: Path) -> None:
    ruta = tmp_path / "arranque.db"
    _arrancar(
        _config_de_arranque(
            ruta, {"APP_ENV": "development", "SEED_ADMIN_PASSWORD": CLAVE_DEMO_FICTICIA}
        )
    )
    otra_config = _config_de_arranque(
        ruta, {"APP_ENV": "development", "SEED_ADMIN_PASSWORD": "otra-clave-demo-ficticia"}
    )

    with TestClient(create_app(otra_config)) as cliente:
        con_la_original = cliente.post(
            "/auth/login", json={"username": "admin_demo", "password": CLAVE_DEMO_FICTICIA}
        )
        con_la_nueva = cliente.post(
            "/auth/login", json={"username": "admin_demo", "password": "otra-clave-demo-ficticia"}
        )

    assert con_la_original.status_code == 200
    assert con_la_nueva.status_code == 401
