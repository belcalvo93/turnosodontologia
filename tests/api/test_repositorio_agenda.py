"""Tests para el repositorio de agenda (C-14).

Verifica la consulta de turnos activos y bloqueos por profesional y por sillón
en un rango semiabierto [desde, hasta), con exclusión de cancelados y orden cronológico.
"""

from collections.abc import Iterator
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio import insertar_usuario
from app.db.repositorio_agenda import (
    consultar_agenda_profesional,
    consultar_agenda_sillon,
)
from app.db.repositorio_bloqueos import crear_bloqueo
from app.db.repositorio_pacientes import crear_paciente
from app.db.repositorio_prestaciones import crear_prestacion
from app.db.repositorio_profesionales import crear_profesional
from app.db.repositorio_sillones import crear_sillon
from app.domain.models import Bloqueo
from app.domain.usuarios import Rol

_INSERTAR_TURNO = """
    INSERT INTO turno (paciente_id, profesional_id, sillon_id, prestacion_id,
                       inicio, fin, estado, creado_por, creado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


@pytest.fixture
def ruta_base(tmp_path: Path) -> Path:
    ruta = tmp_path / "agenda_test.db"
    inicializar_esquema(ruta)
    return ruta


@pytest.fixture
def conexion(ruta_base: Path) -> Iterator[sqlite3.Connection]:
    with closing(abrir_conexion(ruta_base)) as con:
        with transaccion(con):
            crear_paciente(con, nombre="Juan", apellido="Ficticio", dni="30111222 (ficticio)")
            crear_profesional(con, nombre="Dra. Ana", apellido="Ficticia")
            crear_profesional(con, nombre="Dr. Bruno", apellido="Ficticio")
            crear_sillon(con, nombre="Sillón 1 (ficticio)")
            crear_sillon(con, nombre="Sillón 2 (ficticio)")
            crear_prestacion(con, nombre="Consulta ficticia", duracion_minutos=30)
            insertar_usuario(con, username="recepcion_demo", password_hash="x", rol=Rol.RECEPCION)
        yield con


def _insertar_turno(
    con: sqlite3.Connection,
    *,
    paciente_id: int = 1,
    profesional_id: int = 1,
    sillon_id: int = 1,
    prestacion_id: int = 1,
    inicio: str,
    fin: str,
    estado: str = "reservado",
) -> int:
    cursor = con.execute(
        _INSERTAR_TURNO,
        (paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado, 1, inicio),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def test_consultar_agenda_profesional_devuelve_turnos_activos_y_bloqueos_en_orden(
    conexion: sqlite3.Connection,
) -> None:
    # 2026-11-16
    # Turno 1: 09:00 - 09:30
    _insertar_turno(conexion, profesional_id=1, inicio="2026-11-16T09:00:00", fin="2026-11-16T09:30:00")
    # Turno 2: 10:00 - 10:30
    _insertar_turno(conexion, profesional_id=1, inicio="2026-11-16T10:00:00", fin="2026-11-16T10:30:00")
    # Bloqueo profesional 1: 11:00 - 12:00
    crear_bloqueo(
        conexion,
        Bloqueo(
            alcance="profesional",
            recurso_id=1,
            inicio=datetime(2026, 11, 16, 11, 0),
            fin=datetime(2026, 11, 16, 12, 0),
            motivo="Capacitación ficticia",
        ),
    )

    desde = datetime(2026, 11, 16, 0, 0)
    hasta = datetime(2026, 11, 16, 23, 59, 59)

    turnos, bloqueos = consultar_agenda_profesional(conexion, profesional_id=1, desde=desde, hasta=hasta)

    assert len(turnos) == 2
    assert len(bloqueos) == 1
    assert [t.inicio.isoformat(timespec="seconds") for t in turnos] == [
        "2026-11-16T09:00:00",
        "2026-11-16T10:00:00",
    ]
    assert bloqueos[0].inicio.isoformat(timespec="seconds") == "2026-11-16T11:00:00"


def test_consultar_agenda_profesional_excluye_cancelados(conexion: sqlite3.Connection) -> None:
    _insertar_turno(
        conexion,
        profesional_id=1,
        inicio="2026-11-16T09:00:00",
        fin="2026-11-16T09:30:00",
        estado="reservado",
    )
    _insertar_turno(
        conexion,
        profesional_id=1,
        inicio="2026-11-16T10:00:00",
        fin="2026-11-16T10:30:00",
        estado="cancelado",
    )

    desde = datetime(2026, 11, 16, 0, 0)
    hasta = datetime(2026, 11, 16, 23, 59, 59)

    turnos, bloqueos = consultar_agenda_profesional(conexion, profesional_id=1, desde=desde, hasta=hasta)

    assert len(turnos) == 1
    assert turnos[0].inicio.isoformat(timespec="seconds") == "2026-11-16T09:00:00"
    assert turnos[0].estado == "reservado"


def test_consultar_agenda_profesional_excluye_otros_profesionales_y_fuera_de_rango(
    conexion: sqlite3.Connection,
) -> None:
    # Turno del profesional 2
    _insertar_turno(conexion, profesional_id=2, inicio="2026-11-16T09:00:00", fin="2026-11-16T09:30:00")
    # Turno del profesional 1 pero otro día
    _insertar_turno(conexion, profesional_id=1, inicio="2026-11-17T09:00:00", fin="2026-11-17T09:30:00")
    # Turno del profesional 1 en el día
    _insertar_turno(conexion, profesional_id=1, inicio="2026-11-16T14:00:00", fin="2026-11-16T14:30:00")

    desde = datetime(2026, 11, 16, 0, 0)
    hasta = datetime(2026, 11, 16, 23, 59, 59)

    turnos, _ = consultar_agenda_profesional(conexion, profesional_id=1, desde=desde, hasta=hasta)

    assert len(turnos) == 1
    assert turnos[0].inicio.isoformat(timespec="seconds") == "2026-11-16T14:00:00"


def test_consultar_agenda_sillon_devuelve_turnos_y_bloqueos_del_sillon(
    conexion: sqlite3.Connection,
) -> None:
    # Turno en sillón 1
    _insertar_turno(conexion, sillon_id=1, inicio="2026-11-16T14:00:00", fin="2026-11-16T14:45:00")
    # Turno en sillón 2 (debe excluirse)
    _insertar_turno(conexion, sillon_id=2, inicio="2026-11-16T14:00:00", fin="2026-11-16T14:45:00")
    # Bloqueo en sillón 1
    crear_bloqueo(
        conexion,
        Bloqueo(
            alcance="sillon",
            recurso_id=1,
            inicio=datetime(2026, 11, 16, 15, 0),
            fin=datetime(2026, 11, 16, 16, 0),
            motivo="Mantenimiento de sillón",
        ),
    )

    desde = datetime(2026, 11, 16, 0, 0)
    hasta = datetime(2026, 11, 16, 23, 59, 59)

    turnos, bloqueos = consultar_agenda_sillon(conexion, sillon_id=1, desde=desde, hasta=hasta)

    assert len(turnos) == 1
    assert turnos[0].sillon_id == 1
    assert len(bloqueos) == 1
    assert bloqueos[0].alcance == "sillon"
    assert bloqueos[0].recurso_id == 1

def test_consultar_agenda_bordes_semiabiertos(conexion: sqlite3.Connection) -> None:
    # Turno que termina exactamente en `desde` (10:00) -> NO debe incluirse
    _insertar_turno(conexion, profesional_id=1, inicio="2026-11-16T09:30:00", fin="2026-11-16T10:00:00")
    # Turno que empieza exactamente en `hasta` (11:00) -> NO debe incluirse
    _insertar_turno(conexion, profesional_id=1, inicio="2026-11-16T11:00:00", fin="2026-11-16T11:30:00")
    # Turno que intersecta la ventana (10:15 - 10:45) -> SÍ debe incluirse
    _insertar_turno(conexion, profesional_id=1, inicio="2026-11-16T10:15:00", fin="2026-11-16T10:45:00")

    desde = datetime(2026, 11, 16, 10, 0)
    hasta = datetime(2026, 11, 16, 11, 0)

    turnos, _ = consultar_agenda_profesional(conexion, profesional_id=1, desde=desde, hasta=hasta)
    assert len(turnos) == 1
    assert turnos[0].inicio == datetime(2026, 11, 16, 10, 15)


def test_consultar_agenda_bloqueo_multidia_que_atraviesa_el_rango(
    conexion: sqlite3.Connection,
) -> None:
    # Bloqueo del 15 al 20 de noviembre
    crear_bloqueo(
        conexion,
        Bloqueo(
            alcance="profesional",
            recurso_id=1,
            inicio=datetime(2026, 11, 15, 8, 0),
            fin=datetime(2026, 11, 20, 18, 0),
            motivo="Congreso ficticio",
        ),
    )

    # Consulta solo para el 16 de noviembre
    desde = datetime(2026, 11, 16, 0, 0)
    hasta = datetime(2026, 11, 16, 23, 59, 59)

    _, bloqueos = consultar_agenda_profesional(conexion, profesional_id=1, desde=desde, hasta=hasta)
    assert len(bloqueos) == 1
    assert bloqueos[0].motivo == "Congreso ficticio"
