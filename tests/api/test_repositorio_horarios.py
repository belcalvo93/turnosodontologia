from collections.abc import Iterator
from contextlib import closing
from datetime import time
from pathlib import Path
import sqlite3
import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio_profesionales import crear_profesional
from app.db.repositorio_horarios import (
    crear_horario,
    listar_horarios_por_profesional,
    listar_horarios_por_profesional_y_dia,
)
from app.domain.errores import DatoInvalido
from app.domain.models import HorarioAtencion


@pytest.fixture
def conexion(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    ruta = tmp_path / "horarios_test.db"
    inicializar_esquema(ruta)
    with closing(abrir_conexion(ruta)) as conn:
        yield conn


@pytest.fixture
def conexion_con_profesional(conexion: sqlite3.Connection) -> tuple[sqlite3.Connection, int]:
    with transaccion(conexion):
        prof = crear_profesional(conexion, nombre="Doctor", apellido="Ficticio")
    assert prof.id is not None
    return conexion, prof.id


def test_crear_horario_e_inserta_con_id(
    conexion_con_profesional: tuple[sqlite3.Connection, int],
) -> None:
    conexion, prof_id = conexion_con_profesional
    horario = HorarioAtencion(
        profesional_id=prof_id,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    with transaccion(conexion):
        creado = crear_horario(conexion, horario)
    assert creado.id is not None
    assert creado.profesional_id == prof_id
    assert creado.dia_semana == 0
    assert creado.hora_desde == time(9, 0)
    assert creado.hora_hasta == time(13, 0)


def test_crear_horario_con_profesional_inexistente_lanza_dato_invalido(
    conexion: sqlite3.Connection,
) -> None:
    horario = HorarioAtencion(
        profesional_id=9999,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    with pytest.raises(DatoInvalido, match="profesional"):
        crear_horario(conexion, horario)


def test_listar_horarios_por_profesional_devuelve_ordenados(
    conexion_con_profesional: tuple[sqlite3.Connection, int],
) -> None:
    conexion, prof_id = conexion_con_profesional
    h_martes = HorarioAtencion(
        profesional_id=prof_id,
        dia_semana=1,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    h_lunes_tarde = HorarioAtencion(
        profesional_id=prof_id,
        dia_semana=0,
        hora_desde=time(14, 0),
        hora_hasta=time(18, 0),
    )
    h_lunes_manana = HorarioAtencion(
        profesional_id=prof_id,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    with transaccion(conexion):
        crear_horario(conexion, h_martes)
        crear_horario(conexion, h_lunes_tarde)
        crear_horario(conexion, h_lunes_manana)

    horarios = listar_horarios_por_profesional(conexion, prof_id)
    assert len(horarios) == 3
    # Lunes mañana, lunes tarde, martes mañana
    assert [(h.dia_semana, h.hora_desde) for h in horarios] == [
        (0, time(9, 0)),
        (0, time(14, 0)),
        (1, time(9, 0)),
    ]


def test_listar_horarios_por_profesional_y_dia(
    conexion_con_profesional: tuple[sqlite3.Connection, int],
) -> None:
    conexion, prof_id = conexion_con_profesional
    h_lunes = HorarioAtencion(
        profesional_id=prof_id,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    h_martes = HorarioAtencion(
        profesional_id=prof_id,
        dia_semana=1,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    with transaccion(conexion):
        crear_horario(conexion, h_lunes)
        crear_horario(conexion, h_martes)

    lunes_horarios = listar_horarios_por_profesional_y_dia(conexion, prof_id, 0)
    assert len(lunes_horarios) == 1
    assert lunes_horarios[0].dia_semana == 0
