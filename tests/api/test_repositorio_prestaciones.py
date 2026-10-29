"""Tests del esquema SQLite de prestaciones (C-05)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio_prestaciones import (
    actualizar_prestacion,
    crear_prestacion,
    listar_prestaciones,
    obtener_prestacion_por_id,
)
from app.domain.errores import NombreDuplicado
from app.domain.models import Prestacion


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """Conexión a una base temporal por test con el esquema ya aplicado."""
    ruta = tmp_path / "prestaciones.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conexion_abierta:
        yield conexion_abierta


def test_inicializar_esquema_crea_tabla_prestacion_idempotente(tmp_path: Path) -> None:
    ruta = tmp_path / "prestaciones_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion_abierta:
        fila = conexion_abierta.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'prestacion'"
        ).fetchone()
        assert fila == ("prestacion",)


def test_tabla_prestacion_rechaza_nombre_vacio(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos) VALUES ('', 30)"
        )


def test_tabla_prestacion_rechaza_nombre_solo_espacios(
    conexion: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos) VALUES ('   ', 30)"
        )


def test_tabla_prestacion_rechaza_nombre_duplicado(conexion: sqlite3.Connection) -> None:
    conexion.execute(
        "INSERT INTO prestacion (nombre, duracion_minutos) VALUES ('Consulta ficticia', 30)"
    )

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos)"
            " VALUES ('Consulta ficticia', 45)"
        )


@pytest.mark.parametrize("activa_invalida", [-1, 2])
def test_tabla_prestacion_rechaza_activa_fuera_de_cero_y_uno(
    conexion: sqlite3.Connection, activa_invalida: int
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos, activa)"
            " VALUES (?, ?, ?)",
            ("Consulta ficticia", 30, activa_invalida),
        )


def test_tabla_prestacion_rechaza_duracion_cero(conexion: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos)"
            " VALUES ('Consulta ficticia', 0)"
        )


@pytest.mark.parametrize("duracion_negativa", [-1, -30])
def test_tabla_prestacion_rechaza_duracion_negativa(
    conexion: sqlite3.Connection, duracion_negativa: int
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO prestacion (nombre, duracion_minutos) VALUES (?, ?)",
            ("Consulta ficticia", duracion_negativa),
        )


def test_tabla_prestacion_asigna_activa_uno_por_defecto(
    conexion: sqlite3.Connection,
) -> None:
    cursor = conexion.execute(
        "INSERT INTO prestacion (nombre, duracion_minutos)"
        " VALUES ('Consulta ficticia', 30)"
    )

    assert cursor.lastrowid is not None
    fila = conexion.execute(
        "SELECT activa FROM prestacion WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    assert fila == (1,)


def test_crear_y_obtener_prestacion_por_id(conexion: sqlite3.Connection) -> None:
    with transaccion(conexion):
        creada = crear_prestacion(
            conexion, nombre="Consulta ficticia", duracion_minutos=45
        )

    assert creada == Prestacion(
        id=1, nombre="Consulta ficticia", duracion_minutos=45, activa=True
    )
    assert obtener_prestacion_por_id(conexion, 1) == creada


def test_obtener_prestacion_por_id_inexistente_devuelve_none(
    conexion: sqlite3.Connection,
) -> None:
    assert obtener_prestacion_por_id(conexion, 999) is None


def test_listar_prestaciones_devuelve_activas_e_inactivas_ordenadas_por_id(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        primera = crear_prestacion(
            conexion, nombre="Consulta ficticia", duracion_minutos=45
        )
        segunda = crear_prestacion(
            conexion, nombre="Limpieza ficticia", duracion_minutos=30
        )
        assert segunda.id is not None
        desactivada = actualizar_prestacion(conexion, segunda.id, activa=False)

    assert desactivada == Prestacion(
        id=segunda.id,
        nombre="Limpieza ficticia",
        duracion_minutos=30,
        activa=False,
    )
    assert listar_prestaciones(conexion) == [primera, desactivada]


def test_actualizar_prestacion_modifica_campos(conexion: sqlite3.Connection) -> None:
    with transaccion(conexion):
        creada = crear_prestacion(
            conexion, nombre="Consulta ficticia", duracion_minutos=45
        )
        assert creada.id is not None
        actualizada = actualizar_prestacion(
            conexion, creada.id, nombre="Consulta ficticia bis"
        )

    assert actualizada == Prestacion(
        id=creada.id,
        nombre="Consulta ficticia bis",
        duracion_minutos=45,
        activa=True,
    )


def test_actualizar_prestacion_modifica_duracion_minutos(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        creada = crear_prestacion(
            conexion, nombre="Consulta ficticia", duracion_minutos=30
        )
        assert creada.id is not None
        actualizada = actualizar_prestacion(conexion, creada.id, duracion_minutos=60)

    assert actualizada == Prestacion(
        id=creada.id,
        nombre="Consulta ficticia",
        duracion_minutos=60,
        activa=True,
    )
    assert obtener_prestacion_por_id(conexion, creada.id) == actualizada


def test_actualizar_prestacion_inexistente_devuelve_none(
    conexion: sqlite3.Connection,
) -> None:
    assert actualizar_prestacion(conexion, 9999, activa=False) is None


def test_baja_logica_de_prestacion_conserva_la_fila(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        creada = crear_prestacion(
            conexion, nombre="Consulta ficticia", duracion_minutos=45
        )
        assert creada.id is not None
        actualizar_prestacion(conexion, creada.id, activa=False)

    fila = conexion.execute(
        "SELECT activa FROM prestacion WHERE id = ?", (creada.id,)
    ).fetchone()
    assert fila == (0,)
    assert len(listar_prestaciones(conexion)) == 1


def test_crear_prestacion_con_nombre_duplicado_lanza_nombre_duplicado(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        crear_prestacion(conexion, nombre="Consulta ficticia", duracion_minutos=45)

    with pytest.raises(NombreDuplicado):
        with transaccion(conexion):
            crear_prestacion(
                conexion, nombre="Consulta ficticia", duracion_minutos=30
            )


def test_crear_prestacion_con_nombre_en_blanco_no_traduce_el_integrity_error(
    conexion: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError) as error:
        with transaccion(conexion):
            crear_prestacion(conexion, nombre="   ", duracion_minutos=30)

    assert not isinstance(error.value, NombreDuplicado)
    assert conexion.execute("SELECT COUNT(*) FROM prestacion").fetchone() == (0,)


def test_actualizar_prestacion_a_nombre_existente_lanza_nombre_duplicado(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        primera = crear_prestacion(
            conexion, nombre="Consulta ficticia", duracion_minutos=45
        )
        segunda = crear_prestacion(
            conexion, nombre="Limpieza ficticia", duracion_minutos=30
        )
        assert primera.id is not None
        assert segunda.id is not None

    with pytest.raises(NombreDuplicado):
        with transaccion(conexion):
            actualizar_prestacion(
                conexion, segunda.id, nombre="Consulta ficticia"
            )

    assert obtener_prestacion_por_id(conexion, segunda.id) == segunda


def test_actualizar_prestacion_con_duracion_invalida_propaga_integrity_error_sin_traducir(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        creada = crear_prestacion(
            conexion, nombre="Consulta ficticia", duracion_minutos=30
        )
        assert creada.id is not None

    with pytest.raises(sqlite3.IntegrityError) as error:
        with transaccion(conexion):
            actualizar_prestacion(conexion, creada.id, duracion_minutos=0)

    assert not isinstance(error.value, NombreDuplicado)
    assert obtener_prestacion_por_id(conexion, creada.id) == creada
