"""Esquema y repositorio SQLite de turnos y su auditoría (C-11)."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio import insertar_usuario
from app.db.repositorio_pacientes import crear_paciente
from app.db.repositorio_prestaciones import crear_prestacion
from app.db.repositorio_profesionales import crear_profesional
from app.db.repositorio_sillones import crear_sillon
from app.db.repositorio_turnos import (
    COLUMNAS_TURNO,
    crear_turno,
    listar_turnos_activos_del_dia,
    obtener_turno,
    snapshot_turno,
    turno_desde_fila,
)
from app.domain.models import Turno
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


@pytest.fixture
def ruta_base(tmp_path: Path) -> Path:
    ruta = tmp_path / "turnos_repo.db"
    inicializar_esquema(ruta)
    return ruta


@pytest.fixture
def conexion(ruta_base: Path) -> Iterator[sqlite3.Connection]:
    """Conexión con un paciente, profesional, sillón, prestación y usuario (ids 1)."""
    with closing(abrir_conexion(ruta_base)) as con:
        with transaccion(con):
            crear_paciente(con, nombre="Juan", apellido="Ficticio", dni="30111222 (ficticio)")
            crear_profesional(con, nombre="Ana", apellido="Ficticia")
            crear_sillon(con, nombre="Sillón 1 (ficticio)")
            crear_prestacion(con, nombre="Consulta ficticia", duracion_minutos=30)
            insertar_usuario(con, username="recepcion_ficticia", password_hash="x", rol=Rol.RECEPCION)
        yield con


def _insertar_turno(
    con: sqlite3.Connection,
    *,
    paciente_id: int = 1,
    profesional_id: int = 1,
    sillon_id: int | None = 1,
    prestacion_id: int = 1,
    inicio: str = INICIO,
    fin: str = FIN,
    estado: str = "reservado",
    creado_por: int = 1,
) -> int:
    cursor = con.execute(
        _INSERTAR_TURNO,
        (paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado, creado_por, INICIO),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def _nombres(con: sqlite3.Connection, tipo: str) -> set[str]:
    filas = con.execute("SELECT name FROM sqlite_master WHERE type = ?", (tipo,)).fetchall()
    return {fila[0] for fila in filas}


# --- 3.1 esquema ---


def test_inicializar_esquema_crea_tablas_indices_y_triggers_de_turnos(ruta_base: Path) -> None:
    with closing(abrir_conexion(ruta_base)) as con:
        assert {"turno", "auditoria_turno"} <= _nombres(con, "table")
        assert {
            "idx_turno_profesional_inicio",
            "idx_turno_sillon_inicio",
            "idx_turno_paciente_inicio",
        } <= _nombres(con, "index")
        assert {"auditoria_turno_sin_update", "auditoria_turno_sin_delete"} <= _nombres(
            con, "trigger"
        )


def test_inicializar_esquema_de_turnos_es_idempotente(ruta_base: Path) -> None:
    inicializar_esquema(ruta_base)

    with closing(abrir_conexion(ruta_base)) as con:
        assert len([n for n in _nombres(con, "trigger") if n.startswith("auditoria_turno")]) == 2


# --- 3.2 restricciones ---


@pytest.mark.parametrize(
    "cambios",
    [
        {"inicio": FIN, "fin": INICIO},
        {"inicio": INICIO, "fin": INICIO},
        {"estado": "confirmado"},
        {"sillon_id": None},
    ],
    ids=["inicio_posterior_a_fin", "inicio_igual_a_fin", "estado_invalido", "sin_sillon"],
)
def test_tabla_turno_rechaza_filas_invalidas(
    conexion: sqlite3.Connection, cambios: dict[str, object]
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insertar_turno(conexion, **cambios)  # type: ignore[arg-type]

    assert conexion.execute("SELECT COUNT(*) FROM turno").fetchone() == (0,)


@pytest.mark.parametrize(
    "campo", ["profesional_id", "paciente_id", "sillon_id", "prestacion_id", "creado_por"]
)
def test_tabla_turno_rechaza_clave_foranea_inexistente(
    conexion: sqlite3.Connection, campo: str
) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        _insertar_turno(conexion, **{campo: 999})  # type: ignore[arg-type]


def test_tabla_turno_acepta_estados_reservado_y_cancelado(conexion: sqlite3.Connection) -> None:
    _insertar_turno(conexion, estado="reservado")
    _insertar_turno(conexion, estado="cancelado")

    assert conexion.execute("SELECT COUNT(*) FROM turno").fetchone() == (2,)


def test_tabla_auditoria_turno_rechaza_accion_invalida(conexion: sqlite3.Connection) -> None:
    turno_id = _insertar_turno(conexion)

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(_INSERTAR_AUDITORIA, (turno_id, "borrar", 1, INICIO, None, "{}"))


# --- 3.3 RN-AUD-02 ---


def test_auditoria_turno_rechaza_update_y_el_registro_queda_igual(
    conexion: sqlite3.Connection,
) -> None:
    turno_id = _insertar_turno(conexion)
    conexion.execute(_INSERTAR_AUDITORIA, (turno_id, "crear", 1, INICIO, None, '{"a": 1}'))
    antes = conexion.execute("SELECT * FROM auditoria_turno").fetchall()

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("UPDATE auditoria_turno SET despues = ? WHERE id = ?", ("{}", 1))

    assert conexion.execute("SELECT * FROM auditoria_turno").fetchall() == antes


def test_auditoria_turno_rechaza_delete_y_el_registro_queda_igual(
    conexion: sqlite3.Connection,
) -> None:
    turno_id = _insertar_turno(conexion)
    conexion.execute(_INSERTAR_AUDITORIA, (turno_id, "crear", 1, INICIO, None, '{"a": 1}'))
    antes = conexion.execute("SELECT * FROM auditoria_turno").fetchall()

    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute("DELETE FROM auditoria_turno WHERE id = ?", (1,))

    assert conexion.execute("SELECT * FROM auditoria_turno").fetchall() == antes


# --- 4.1 turno_desde_fila / obtener_turno ---

def test_obtener_turno_existente_devuelve_turno_con_datetime_naive(
    conexion: sqlite3.Connection,
) -> None:
    turno_id = _insertar_turno(conexion)

    turno = obtener_turno(conexion, turno_id)

    assert turno == Turno(
        id=turno_id,
        paciente_id=1,
        profesional_id=1,
        sillon_id=1,
        prestacion_id=1,
        inicio=datetime(2026, 1, 12, 10, 0),
        fin=datetime(2026, 1, 12, 10, 30),
        estado="reservado",
    )
    assert turno.inicio.tzinfo is None and turno.fin.tzinfo is None


def test_obtener_turno_inexistente_devuelve_none(conexion: sqlite3.Connection) -> None:
    assert obtener_turno(conexion, 9999) is None


def test_turno_desde_fila_respeta_el_orden_de_columnas_turno(conexion: sqlite3.Connection) -> None:
    turno_id = _insertar_turno(conexion, estado="cancelado", inicio="2026-01-13T15:00:00", fin="2026-01-13T15:45:00")

    fila = conexion.execute(
        "SELECT id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado "
        "FROM turno WHERE id = ?",
        (turno_id,),
    ).fetchone()

    turno = turno_desde_fila(fila)
    assert (turno.estado, turno.inicio, turno.fin) == (
        "cancelado",
        datetime(2026, 1, 13, 15, 0),
        datetime(2026, 1, 13, 15, 45),
    )


def test_columnas_turno_coincide_con_el_orden_que_espera_turno_desde_fila() -> None:
    assert COLUMNAS_TURNO == (
        "id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado"
    )


# --- 4.2 snapshot_turno ---


def test_snapshot_turno_tiene_exactamente_las_8_claves_en_orden_y_fechas_iso() -> None:
    turno = Turno(
        id=7,
        paciente_id=1,
        profesional_id=2,
        sillon_id=3,
        prestacion_id=4,
        inicio=datetime(2026, 1, 12, 10, 0),
        fin=datetime(2026, 1, 12, 10, 30),
    )

    texto = snapshot_turno(turno)

    assert list(json.loads(texto)) == [
        "id", "paciente_id", "profesional_id", "sillon_id",
        "prestacion_id", "inicio", "fin", "estado",
    ]  # fmt: skip
    assert json.loads(texto) == {
        "id": 7,
        "paciente_id": 1,
        "profesional_id": 2,
        "sillon_id": 3,
        "prestacion_id": 4,
        "inicio": "2026-01-12T10:00:00",
        "fin": "2026-01-12T10:30:00",
        "estado": "reservado",
    }


def test_snapshot_turno_cancelado_de_tarde_con_otros_ids() -> None:
    turno = Turno(
        id=12,
        paciente_id=5,
        profesional_id=6,
        sillon_id=7,
        prestacion_id=8,
        inicio=datetime(2026, 2, 3, 15, 15),
        fin=datetime(2026, 2, 3, 16, 0),
        estado="cancelado",
    )

    assert json.loads(snapshot_turno(turno)) == {
        "id": 12,
        "paciente_id": 5,
        "profesional_id": 6,
        "sillon_id": 7,
        "prestacion_id": 8,
        "inicio": "2026-02-03T15:15:00",
        "fin": "2026-02-03T16:00:00",
        "estado": "cancelado",
    }


# --- 4.3 crear_turno + auditoría ---


def _candidato(inicio: datetime = datetime(2026, 1, 12, 10, 0), minutos: int = 30) -> Turno:
    return Turno(
        paciente_id=1,
        profesional_id=1,
        sillon_id=1,
        prestacion_id=1,
        inicio=inicio,
        fin=inicio + timedelta(minutes=minutos),
    )


def test_crear_turno_guarda_turno_y_un_unico_registro_de_auditoria_crear(
    conexion: sqlite3.Connection,
) -> None:
    creado_en = datetime(2026, 1, 5, 9, 0)

    with transaccion(conexion):
        creado = crear_turno(conexion, _candidato(), creado_por=1, creado_en=creado_en)

    assert creado.id is not None
    assert creado == obtener_turno(conexion, creado.id)
    fila = conexion.execute(
        "SELECT creado_por, creado_en FROM turno WHERE id = ?", (creado.id,)
    ).fetchone()
    assert fila == (1, "2026-01-05T09:00:00")
    auditorias = conexion.execute(
        "SELECT turno_id, accion, usuario_id, ocurrio_en, antes, despues FROM auditoria_turno"
    ).fetchall()
    assert auditorias == [
        (creado.id, "crear", 1, "2026-01-05T09:00:00", None, snapshot_turno(creado))
    ]


def test_crear_turno_dos_altas_seguidas_generan_ids_y_auditorias_distintas(
    conexion: sqlite3.Connection,
) -> None:
    with transaccion(conexion):
        primero = crear_turno(
            conexion, _candidato(), creado_por=1, creado_en=datetime(2026, 1, 5, 9, 0)
        )
        segundo = crear_turno(
            conexion,
            _candidato(datetime(2026, 1, 12, 11, 0), minutos=45),
            creado_por=1,
            creado_en=datetime(2026, 1, 5, 9, 5),
        )

    assert primero.id != segundo.id
    filas = conexion.execute(
        "SELECT turno_id, despues FROM auditoria_turno ORDER BY id"
    ).fetchall()
    assert filas == [
        (primero.id, snapshot_turno(primero)),
        (segundo.id, snapshot_turno(segundo)),
    ]
    assert json.loads(filas[1][1])["fin"] == "2026-01-12T11:45:00"


# --- 4.4 RN-AUD-03 atomicidad ---


def _contar(ruta: Path, tabla: str) -> int:
    consultas = {
        "turno": "SELECT COUNT(*) FROM turno",
        "auditoria_turno": "SELECT COUNT(*) FROM auditoria_turno",
    }
    with closing(abrir_conexion(ruta)) as con:
        return int(con.execute(consultas[tabla]).fetchone()[0])


def test_crear_turno_con_creado_por_inexistente_no_deja_turno_ni_auditoria(
    ruta_base: Path, conexion: sqlite3.Connection
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        with transaccion(conexion):
            crear_turno(conexion, _candidato(), creado_por=999, creado_en=datetime(2026, 1, 5, 9, 0))

    assert _contar(ruta_base, "turno") == 0
    assert _contar(ruta_base, "auditoria_turno") == 0


def test_crear_turno_si_falla_la_auditoria_revierte_tambien_el_turno(
    ruta_base: Path, conexion: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    def auditoria_rota(*args: object, **kwargs: object) -> None:
        raise sqlite3.IntegrityError("fallo simulado de auditoría")

    monkeypatch.setattr("app.db.repositorio_turnos.registrar_auditoria", auditoria_rota)

    with pytest.raises(sqlite3.IntegrityError, match="simulado"):
        with transaccion(conexion):
            crear_turno(conexion, _candidato(), creado_por=1, creado_en=datetime(2026, 1, 5, 9, 0))

    assert _contar(ruta_base, "turno") == 0
    assert _contar(ruta_base, "auditoria_turno") == 0


# --- 4.5 listar_turnos_activos_del_dia ---

DIA = date(2026, 1, 12)


def _agregar_recursos_alternativos(con: sqlite3.Connection) -> None:
    """Segundo profesional, sillón y paciente (ids 2)."""
    with transaccion(con):
        crear_paciente(con, nombre="Luisa", apellido="Ficticia", dni="30333444 (ficticio)")
        crear_profesional(con, nombre="Beto", apellido="Ficticio")
        crear_sillon(con, nombre="Sillón 2 (ficticio)")


def _ids_activos(con: sqlite3.Connection, *, profesional_id: int = 1, sillon_id: int = 1, paciente_id: int = 1) -> set[int | None]:
    turnos = listar_turnos_activos_del_dia(
        con, dia=DIA, profesional_id=profesional_id, sillon_id=sillon_id, paciente_id=paciente_id
    )
    return {turno.id for turno in turnos}


def test_listar_turnos_activos_incluye_los_que_comparten_profesional_sillon_o_paciente(
    conexion: sqlite3.Connection,
) -> None:
    _agregar_recursos_alternativos(conexion)
    mismo_profesional = _insertar_turno(conexion, sillon_id=2, paciente_id=2)
    mismo_sillon = _insertar_turno(conexion, profesional_id=2, paciente_id=2)
    mismo_paciente = _insertar_turno(conexion, profesional_id=2, sillon_id=2)

    assert _ids_activos(conexion) == {mismo_profesional, mismo_sillon, mismo_paciente}


def test_listar_turnos_activos_excluye_cancelados_otro_dia_y_sin_recurso_compartido(
    conexion: sqlite3.Connection,
) -> None:
    _agregar_recursos_alternativos(conexion)
    _insertar_turno(conexion, estado="cancelado")
    _insertar_turno(conexion, inicio="2026-01-11T10:00:00", fin="2026-01-11T10:30:00")
    _insertar_turno(conexion, inicio="2026-01-13T00:00:00", fin="2026-01-13T00:30:00")
    _insertar_turno(conexion, profesional_id=2, sillon_id=2, paciente_id=2)
    incluido = _insertar_turno(conexion, inicio="2026-01-12T00:00:00", fin="2026-01-12T00:30:00")

    assert _ids_activos(conexion) == {incluido}


def test_listar_turnos_activos_devuelve_turnos_de_dominio_con_fechas_naive(
    conexion: sqlite3.Connection,
) -> None:
    turno_id = _insertar_turno(conexion)

    turnos = listar_turnos_activos_del_dia(
        conexion, dia=DIA, profesional_id=1, sillon_id=1, paciente_id=1
    )

    assert turnos == [obtener_turno(conexion, turno_id)]


# --- 5.8 SE-06 con concurrencia real (dos conexiones, sin hilos ni sleep) ---

BUSY_TIMEOUT_CORTO_MS = 50  # solo en este test: la conexión de producción conserva 5000 ms


def test_transaccion_de_otra_conexion_espera_el_lock_y_despues_ve_el_turno_confirmado(
    ruta_base: Path, conexion: sqlite3.Connection
) -> None:
    with closing(abrir_conexion(ruta_base)) as conexion_b:
        conexion_b.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_CORTO_MS}")
        with transaccion(conexion):  # A: toma el lock de escritura y reserva el hueco
            assert listar_turnos_activos_del_dia(
                conexion, dia=DIA, profesional_id=1, sillon_id=1, paciente_id=1
            ) == []
            crear_turno(conexion, _candidato(), creado_por=1, creado_en=datetime(2026, 1, 5, 9, 0))

            with pytest.raises(sqlite3.OperationalError, match="locked"):
                with transaccion(conexion_b):  # B no puede leer el contexto mientras A no confirma
                    pytest.fail("B no debería obtener el lock de escritura")

        # A confirmó: B toma el lock y ve el turno de A (una segunda alta daría ConflictoAgenda)
        with transaccion(conexion_b):
            vistos = listar_turnos_activos_del_dia(
                conexion_b, dia=DIA, profesional_id=1, sillon_id=1, paciente_id=1
            )
        assert [(t.profesional_id, t.inicio) for t in vistos] == [(1, datetime(2026, 1, 12, 10, 0))]


def test_transaccion_de_otra_conexion_toma_el_lock_cuando_a_revierte(
    ruta_base: Path, conexion: sqlite3.Connection
) -> None:
    with closing(abrir_conexion(ruta_base)) as conexion_b:
        conexion_b.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_CORTO_MS}")
        with pytest.raises(RuntimeError, match="aborta A"):
            with transaccion(conexion):
                crear_turno(
                    conexion, _candidato(), creado_por=1, creado_en=datetime(2026, 1, 5, 9, 0)
                )
                raise RuntimeError("aborta A")

        with transaccion(conexion_b):
            vistos = listar_turnos_activos_del_dia(
                conexion_b, dia=DIA, profesional_id=1, sillon_id=1, paciente_id=1
            )
        assert vistos == []
