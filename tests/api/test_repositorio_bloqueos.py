"""Tests del esquema y repositorio SQLite de bloqueos (C-09)."""

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio_bloqueos import (
    crear_bloqueo,
    eliminar_bloqueo,
    listar_bloqueos,
    listar_bloqueos_de_recursos,
)
from app.db.repositorio_profesionales import crear_profesional
from app.db.repositorio_sillones import crear_sillon
from app.domain.errores import DatoInvalido
from app.domain.models import Bloqueo


def test_inicializar_esquema_crea_tabla_e_indice_bloqueo_idempotente(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "bloqueos_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        tabla = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'bloqueo'"
        ).fetchone()
        indice = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND name = 'idx_bloqueo_alcance_recurso_inicio'"
        ).fetchone()
        assert tabla == ("bloqueo",)
        assert indice == ("idx_bloqueo_alcance_recurso_inicio",)


def test_tabla_bloqueo_rechaza_alcance_o_intervalo_invalido(tmp_path: Path) -> None:
    ruta = tmp_path / "bloqueos_checks.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                """
                INSERT INTO bloqueo (alcance, recurso_id, inicio, fin, motivo)
                VALUES ('consultorio', 1, '2026-11-10T09:00:00', '2026-11-10T12:00:00', 'Feriado')
                """
            )
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                """
                INSERT INTO bloqueo (alcance, recurso_id, inicio, fin, motivo)
                VALUES ('profesional', 1, '2026-11-10T12:00:00', '2026-11-10T09:00:00', 'Error')
                """
            )


def test_crear_listar_y_eliminar_bloqueo_de_profesional(tmp_path: Path) -> None:
    ruta = tmp_path / "bloqueos_crud.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            prof = crear_profesional(
                conexion, nombre="Odontólogo", apellido="Ficticio A"
            )
            assert prof.id is not None
            creado = crear_bloqueo(
                conexion,
                Bloqueo(
                    alcance="profesional",
                    recurso_id=prof.id,
                    inicio=datetime(2026, 11, 10, 9, 0),
                    fin=datetime(2026, 11, 10, 13, 0),
                    motivo="Vacaciones",
                ),
            )

        assert creado == Bloqueo(
            id=1,
            alcance="profesional",
            recurso_id=prof.id,
            inicio=datetime(2026, 11, 10, 9, 0),
            fin=datetime(2026, 11, 10, 13, 0),
            motivo="Vacaciones",
        )
        assert listar_bloqueos(conexion) == [creado]

        with transaccion(conexion):
            assert eliminar_bloqueo(conexion, 1) is True
            assert eliminar_bloqueo(conexion, 1) is False

        assert listar_bloqueos(conexion) == []


def test_crear_bloqueo_con_profesional_inexistente_lanza_dato_invalido(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "bloqueos_inexistente.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with pytest.raises(DatoInvalido):
            with transaccion(conexion):
                crear_bloqueo(
                    conexion,
                    Bloqueo(
                        alcance="profesional",
                        recurso_id=999,
                        inicio=datetime(2026, 11, 10, 9, 0),
                        fin=datetime(2026, 11, 10, 13, 0),
                        motivo="Vacaciones",
                    ),
                )


# --- C-11: listar_bloqueos_de_recursos (design S7) ---

DIA_DESDE = datetime(2026, 1, 12, 0, 0)
DIA_HASTA = datetime(2026, 1, 13, 0, 0)


def _bloqueo(
    alcance: str, recurso_id: int, inicio: datetime, fin: datetime, motivo: str = "Ficticio"
) -> Bloqueo:
    return Bloqueo(
        alcance=alcance,  # type: ignore[arg-type]
        recurso_id=recurso_id,
        inicio=inicio,
        fin=fin,
        motivo=motivo,
    )


def _consultar(conexion: sqlite3.Connection) -> list[Bloqueo]:
    return listar_bloqueos_de_recursos(
        conexion, profesional_id=1, sillon_id=1, desde=DIA_DESDE, hasta=DIA_HASTA
    )


def _base_con_recursos(tmp_path: Path) -> sqlite3.Connection:
    ruta = tmp_path / "bloqueos_recursos.db"
    inicializar_esquema(ruta)
    conexion = abrir_conexion(ruta)
    with transaccion(conexion):
        crear_profesional(conexion, nombre="Ana", apellido="Ficticia")
        crear_profesional(conexion, nombre="Beto", apellido="Ficticio")
        crear_sillon(conexion, nombre="Sillón 1 (ficticio)")
        crear_sillon(conexion, nombre="Sillón 2 (ficticio)")
    return conexion


def test_listar_bloqueos_de_recursos_incluye_profesional_y_sillon_que_intersectan(
    tmp_path: Path,
) -> None:
    with closing(_base_con_recursos(tmp_path)) as conexion:
        with transaccion(conexion):
            de_profesional = crear_bloqueo(
                conexion, _bloqueo("profesional", 1, datetime(2026, 1, 12, 9, 0), datetime(2026, 1, 12, 11, 0))
            )
            de_sillon = crear_bloqueo(
                conexion, _bloqueo("sillon", 1, datetime(2026, 1, 12, 14, 0), datetime(2026, 1, 12, 15, 0))
            )

        assert _consultar(conexion) == [de_profesional, de_sillon]


def test_listar_bloqueos_de_recursos_incluye_un_bloqueo_de_varios_dias_que_cubre_la_ventana(
    tmp_path: Path,
) -> None:
    with closing(_base_con_recursos(tmp_path)) as conexion:
        with transaccion(conexion):
            vacaciones = crear_bloqueo(
                conexion, _bloqueo("profesional", 1, datetime(2026, 1, 5, 0, 0), datetime(2026, 1, 20, 0, 0))
            )
            termina_dentro = crear_bloqueo(
                conexion, _bloqueo("sillon", 1, datetime(2026, 1, 10, 0, 0), datetime(2026, 1, 12, 0, 1))
            )

        assert _consultar(conexion) == [vacaciones, termina_dentro]


def test_listar_bloqueos_de_recursos_excluye_otro_recurso_y_mismo_id_de_otro_alcance(
    tmp_path: Path,
) -> None:
    with closing(_base_con_recursos(tmp_path)) as conexion:
        inicio, fin = datetime(2026, 1, 12, 9, 0), datetime(2026, 1, 12, 11, 0)
        with transaccion(conexion):
            crear_bloqueo(conexion, _bloqueo("profesional", 2, inicio, fin))
            crear_bloqueo(conexion, _bloqueo("sillon", 2, inicio, fin))
            incluido = crear_bloqueo(conexion, _bloqueo("sillon", 1, inicio, fin))

        assert listar_bloqueos_de_recursos(
            conexion, profesional_id=2, sillon_id=1, desde=DIA_DESDE, hasta=DIA_HASTA
        )[-1] == incluido
        # profesional 1 / sillón 2: el bloqueo de sillón 1 no aparece y el del profesional 2 tampoco.
        assert [
            b.alcance + str(b.recurso_id)
            for b in listar_bloqueos_de_recursos(
                conexion, profesional_id=1, sillon_id=2, desde=DIA_DESDE, hasta=DIA_HASTA
            )
        ] == ["sillon2"]
        assert _consultar(conexion) == [incluido]


def test_listar_bloqueos_de_recursos_excluye_los_contiguos_a_la_ventana(tmp_path: Path) -> None:
    with closing(_base_con_recursos(tmp_path)) as conexion:
        with transaccion(conexion):
            crear_bloqueo(  # termina justo cuando empieza la ventana
                conexion, _bloqueo("profesional", 1, datetime(2026, 1, 11, 20, 0), DIA_DESDE)
            )
            crear_bloqueo(  # empieza justo cuando termina la ventana
                conexion, _bloqueo("sillon", 1, DIA_HASTA, datetime(2026, 1, 13, 8, 0))
            )

        assert _consultar(conexion) == []
