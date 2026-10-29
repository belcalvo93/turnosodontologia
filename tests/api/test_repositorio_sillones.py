"""Tests del esquema SQLite de sillones (C-05)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio_sillones import (
    actualizar_sillon,
    crear_sillon,
    listar_sillones,
    obtener_sillon_por_id,
)
from app.domain.errores import NombreDuplicado
from app.domain.models import Sillon


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """Conexión a una base temporal por test con el esquema ya aplicado."""
    ruta = tmp_path / "sillones.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_abierta:
        yield conexion_abierta


def test_inicializar_esquema_crea_tabla_sillon_idempotente(tmp_path: Path) -> None:
    ruta = tmp_path / "sillones_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion_abierta:
        fila = conexion_abierta.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sillon'"
        ).fetchone()
        assert fila == ("sillon",)


def test_tabla_sillon_rechaza_nombre_vacio(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO sillon (nombre) VALUES ('')")


def test_tabla_sillon_rechaza_nombre_solo_espacios(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO sillon (nombre) VALUES ('   ')")


def test_tabla_sillon_rechaza_nombre_duplicado(conexion: sqlite3.Connection) -> None:
    conexion.execute("INSERT INTO sillon (nombre) VALUES ('Sillón 1 (ficticio)')")

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("INSERT INTO sillon (nombre) VALUES ('Sillón 1 (ficticio)')")


@pytest.mark.parametrize("activo_invalido", [-1, 2])
def test_tabla_sillon_rechaza_activo_fuera_de_cero_y_uno(
    conexion: sqlite3.Connection, activo_invalido: int
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO sillon (nombre, activo) VALUES (?, ?)",
            ("Sillón 1 (ficticio)", activo_invalido),
        )


def test_tabla_sillon_asigna_activo_uno_por_defecto(conexion: sqlite3.Connection) -> None:
    cursor = conexion.execute(
        "INSERT INTO sillon (nombre) VALUES ('Sillón 1 (ficticio)')"
    )

    assert cursor.lastrowid is not None
    fila = conexion.execute(
        "SELECT activo FROM sillon WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    assert fila == (1,)


def test_crear_y_obtener_sillon_por_id(conexion: sqlite3.Connection) -> None:
    with transaccion(conexion):
        creado = crear_sillon(conexion, nombre="Sillón 1 (ficticio)")

    assert creado == Sillon(id=1, nombre="Sillón 1 (ficticio)", activo=True)
    assert obtener_sillon_por_id(conexion, 1) == creado
    assert obtener_sillon_por_id(conexion, 999) is None


def test_listar_sillones_devuelve_activos_e_inactivos_ordenados_por_id(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        primero = crear_sillon(conexion, nombre="Sillón 1 (ficticio)")
        segundo = crear_sillon(conexion, nombre="Sillón 2 (ficticio)")
        assert segundo.id is not None
        desactivado = actualizar_sillon(conexion, segundo.id, activo=False)

    assert desactivado == Sillon(
        id=segundo.id, nombre="Sillón 2 (ficticio)", activo=False
    )
    assert listar_sillones(conexion) == [primero, desactivado]


def test_actualizar_sillon_modifica_campos(conexion: sqlite3.Connection) -> None:
    with transaccion(conexion):
        creado = crear_sillon(conexion, nombre="Box 1 (ficticio)")
        assert creado.id is not None
        actualizado = actualizar_sillon(
            conexion, creado.id, nombre="Box 1 bis (ficticio)"
        )

    assert actualizado == Sillon(
        id=creado.id, nombre="Box 1 bis (ficticio)", activo=True
    )


def test_actualizar_sillon_inexistente_devuelve_none(
    conexion: sqlite3.Connection,
) -> None:
    assert actualizar_sillon(conexion, 9999, activo=False) is None


def test_obtener_sillon_por_id_inexistente_devuelve_none(
    conexion: sqlite3.Connection,
) -> None:
    assert obtener_sillon_por_id(conexion, 999) is None


def test_baja_logica_de_sillon_conserva_la_fila(conexion: sqlite3.Connection) -> None:
    with transaccion(conexion):
        creado = crear_sillon(conexion, nombre="Sillón 1 (ficticio)")
        assert creado.id is not None
        actualizar_sillon(conexion, creado.id, activo=False)

    fila = conexion.execute(
        "SELECT activo FROM sillon WHERE id = ?", (creado.id,)
    ).fetchone()
    assert fila == (0,)
    assert len(listar_sillones(conexion)) == 1


def test_crear_sillon_con_nombre_duplicado_lanza_nombre_duplicado(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        crear_sillon(conexion, nombre="Sillón 1 (ficticio)")

    with pytest.raises(NombreDuplicado):
        with transaccion(conexion):
            crear_sillon(conexion, nombre="Sillón 1 (ficticio)")


def test_crear_sillon_con_nombre_en_blanco_no_traduce_el_integrity_error(
    conexion: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError) as error:
        with transaccion(conexion):
            crear_sillon(conexion, nombre="   ")

    assert not isinstance(error.value, NombreDuplicado)
    assert conexion.execute("SELECT COUNT(*) FROM sillon").fetchone() == (0,)


def test_actualizar_sillon_a_nombre_existente_lanza_nombre_duplicado(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        primero = crear_sillon(conexion, nombre="Sillón 1 (ficticio)")
        segundo = crear_sillon(conexion, nombre="Sillón 2 (ficticio)")
        assert primero.id is not None
        assert segundo.id is not None

    with pytest.raises(NombreDuplicado):
        with transaccion(conexion):
            actualizar_sillon(conexion, segundo.id, nombre="Sillón 1 (ficticio)")

    assert obtener_sillon_por_id(conexion, segundo.id) == segundo
