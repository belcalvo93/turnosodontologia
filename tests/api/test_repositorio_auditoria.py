"""Repositorio de lectura de auditoría de turnos (C-15)."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio import insertar_usuario
from app.db.repositorio_auditoria import listar_auditoria_por_turno
from app.db.repositorio_pacientes import crear_paciente
from app.db.repositorio_prestaciones import crear_prestacion
from app.db.repositorio_profesionales import crear_profesional
from app.db.repositorio_sillones import crear_sillon
from app.domain.usuarios import Rol

INICIO = "2026-01-12T10:00:00"
FIN = "2026-01-12T10:30:00"

_INSERTAR_TURNO = """
    INSERT INTO turno (paciente_id, profesional_id, sillon_id, prestacion_id,
                       inicio, fin, estado, creado_por, creado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
_INSERTAR_AUDITORIA = """
    INSERT INTO auditoria_turno (turno_id, accion, usuario_id, ocurrio_en, antes, despues)
    VALUES (?, ?, ?, ?, ?, ?)
"""


def _snapshot(turno_id: int, *, inicio: str = INICIO, fin: str = FIN, estado: str = "reservado") -> str:
    """Snapshot canónico de 8 claves, igual al que escribe `snapshot_turno`."""
    return json.dumps(
        {
            "id": turno_id,
            "paciente_id": 1,
            "profesional_id": 1,
            "sillon_id": 1,
            "prestacion_id": 1,
            "inicio": inicio,
            "fin": fin,
            "estado": estado,
        },
        ensure_ascii=False,
    )


@pytest.fixture
def ruta_base(tmp_path: Path) -> Path:
    ruta = tmp_path / "auditoria_repo.db"
    inicializar_esquema(ruta)
    return ruta


@pytest.fixture
def conexion(ruta_base: Path) -> Iterator[sqlite3.Connection]:
    """Conexión con paciente, profesional, sillón, prestación y usuario (ids 1)."""
    with closing(abrir_conexion(ruta_base)) as con:
        with transaccion(con):
            crear_paciente(con, nombre="Juan", apellido="Ficticio", dni="30111222 (ficticio)")
            crear_profesional(con, nombre="Ana", apellido="Ficticia")
            crear_sillon(con, nombre="Sillón 1 (ficticio)")
            crear_prestacion(con, nombre="Consulta ficticia", duracion_minutos=30)
            insertar_usuario(
                con, username="admin_ficticio", password_hash="x", rol=Rol.ADMINISTRACION
            )
        yield con


def _crear_turno(con: sqlite3.Connection, *, inicio: str = INICIO, fin: str = FIN) -> int:
    cursor = con.execute(
        _INSERTAR_TURNO,
        (1, 1, 1, 1, inicio, fin, "reservado", 1, INICIO),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def _insertar_auditoria(
    con: sqlite3.Connection,
    *,
    turno_id: int,
    accion: str = "crear",
    usuario_id: int = 1,
    ocurrio_en: str = INICIO,
    antes: str | None = None,
    despues: str | None = None,
) -> int:
    cursor = con.execute(
        _INSERTAR_AUDITORIA,
        (turno_id, accion, usuario_id, ocurrio_en, antes, despues or _snapshot(turno_id)),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def test_listar_auditoria_devuelve_solo_los_registros_del_turno(conexion: sqlite3.Connection) -> None:
    turno_1 = _crear_turno(conexion)
    turno_2 = _crear_turno(
        conexion, inicio="2026-01-12T11:00:00", fin="2026-01-12T11:30:00"
    )
    _insertar_auditoria(conexion, turno_id=turno_1)
    _insertar_auditoria(conexion, turno_id=turno_2)
    _insertar_auditoria(
        conexion, turno_id=turno_1, accion="cancelar", ocurrio_en="2026-01-12T12:00:00"
    )

    registros = listar_auditoria_por_turno(conexion, turno_1)

    assert [registro.turno_id for registro in registros] == [turno_1, turno_1]
    assert [registro.accion for registro in registros] == ["crear", "cancelar"]


def test_listar_auditoria_ordena_por_ocurrio_en_y_desempata_por_id(
    conexion: sqlite3.Connection,
) -> None:
    turno_id = _crear_turno(conexion)
    tarde = _insertar_auditoria(conexion, turno_id=turno_id, ocurrio_en="2026-01-12T12:00:00")
    primero = _insertar_auditoria(conexion, turno_id=turno_id, ocurrio_en="2026-01-12T10:00:00")
    segundo = _insertar_auditoria(conexion, turno_id=turno_id, ocurrio_en="2026-01-12T10:00:00")

    registros = listar_auditoria_por_turno(conexion, turno_id)

    assert [registro.id for registro in registros] == [primero, segundo, tarde]


def test_listar_auditoria_parsea_antes_y_despues_a_objetos(conexion: sqlite3.Connection) -> None:
    turno_id = _crear_turno(conexion)
    antes = _snapshot(turno_id)
    despues = _snapshot(turno_id, estado="cancelado")
    _insertar_auditoria(
        conexion, turno_id=turno_id, accion="cancelar", antes=antes, despues=despues
    )

    registro = listar_auditoria_por_turno(conexion, turno_id)[0]

    assert isinstance(registro.antes, dict)
    assert isinstance(registro.despues, dict)
    assert registro.antes["estado"] == "reservado"
    assert registro.despues["estado"] == "cancelado"
    assert set(registro.despues) == {
        "id",
        "paciente_id",
        "profesional_id",
        "sillon_id",
        "prestacion_id",
        "inicio",
        "fin",
        "estado",
    }


def test_listar_auditoria_devuelve_el_username_del_usuario(conexion: sqlite3.Connection) -> None:
    turno_id = _crear_turno(conexion)
    _insertar_auditoria(conexion, turno_id=turno_id)

    registro = listar_auditoria_por_turno(conexion, turno_id)[0]

    assert registro.usuario_id == 1
    assert registro.username == "admin_ficticio"


def test_listar_auditoria_deja_antes_en_none_para_el_alta(conexion: sqlite3.Connection) -> None:
    turno_id = _crear_turno(conexion)
    _insertar_auditoria(conexion, turno_id=turno_id, accion="crear", antes=None)

    registro = listar_auditoria_por_turno(conexion, turno_id)[0]

    assert registro.antes is None
    assert registro.despues is not None


def test_listar_auditoria_sin_registros_devuelve_lista_vacia(conexion: sqlite3.Connection) -> None:
    turno_id = _crear_turno(conexion)

    assert listar_auditoria_por_turno(conexion, turno_id) == []
