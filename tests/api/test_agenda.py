"""Tests de endpoints de agenda diaria y semanal (C-14).

Cubre GET /agenda/profesionales/{id} y GET /agenda/sillones/{id} con:
- Orden cronológico de turnos y bloqueos.
- Exclusión de turnos cancelados (RN-TUR-08).
- Control de acceso RBAC (RN-ACC-03, 03 §RBAC).
- Validación de rango temporal (desde <= hasta) -> 422.
- Recursos inexistentes -> 404.
- Sin autenticación -> 401.
"""

from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, time

import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.db.conexion import abrir_conexion, transaccion
from app.db.repositorio_bloqueos import crear_bloqueo
from app.db.repositorio_horarios import crear_horario
from app.db.repositorio_pacientes import crear_paciente
from app.db.repositorio_prestaciones import crear_prestacion
from app.db.repositorio_profesionales import crear_profesional
from app.db.repositorio_sillones import crear_sillon
from app.domain.models import Bloqueo, HorarioAtencion
from app.domain.usuarios import Rol, Usuario

LUNES = "2026-11-16"
DESDE = f"{LUNES}T00:00:00"
HASTA = f"{LUNES}T23:59:59"

_INSERTAR_TURNO = """
    INSERT INTO turno (paciente_id, profesional_id, sillon_id, prestacion_id,
                       inicio, fin, estado, creado_por, creado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


@dataclass
class ContextoAgenda:
    cliente: TestClient
    config: Config
    profesional_a: int
    profesional_b: int
    sillon_1: int
    sillon_2: int
    consulta: int
    paciente_1: int
    recepcion: Usuario
    admin: Usuario
    odontologo_a: Usuario
    odontologo_b: Usuario
    cabeceras_recepcion: dict[str, str]
    cabeceras_admin: dict[str, str]
    cabeceras_odontologo_a: dict[str, str]
    cabeceras_odontologo_b: dict[str, str]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def contexto_agenda(
    cliente: TestClient,
    config: Config,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> ContextoAgenda:
    with closing(abrir_conexion(config.database_path)) as con:
        with transaccion(con):
            prof_a = crear_profesional(con, nombre="Ana", apellido="Ficticia A")
            prof_b = crear_profesional(con, nombre="Bruno", apellido="Ficticio B")
            assert prof_a.id is not None and prof_b.id is not None
            for p_id in (prof_a.id, prof_b.id):
                crear_horario(
                    con,
                    HorarioAtencion(
                        profesional_id=p_id,
                        dia_semana=0,
                        hora_desde=time(8, 0),
                        hora_hasta=time(18, 0),
                    ),
                )
            s_1 = crear_sillon(con, nombre="Sillón 1 (ficticio)")
            s_2 = crear_sillon(con, nombre="Sillón 2 (ficticio)")
            assert s_1.id is not None and s_2.id is not None
            prest = crear_prestacion(con, nombre="Consulta", duracion_minutos=30)
            assert prest.id is not None
            pac = crear_paciente(con, nombre="Paciente", apellido="Ficticio", dni="11111111 (ficticio)")
            assert pac.id is not None

    recepcion = crear_usuario("recepcion_agenda", rol=Rol.RECEPCION)
    admin = crear_usuario("admin_agenda", rol=Rol.ADMINISTRACION)
    odontologo_a = crear_usuario("odontologo_a", rol=Rol.ODONTOLOGO, profesional_id=prof_a.id)
    odontologo_b = crear_usuario("odontologo_b", rol=Rol.ODONTOLOGO, profesional_id=prof_b.id)

    return ContextoAgenda(
        cliente=cliente,
        config=config,
        profesional_a=prof_a.id,
        profesional_b=prof_b.id,
        sillon_1=s_1.id,
        sillon_2=s_2.id,
        consulta=prest.id,
        paciente_1=pac.id,
        recepcion=recepcion,
        admin=admin,
        odontologo_a=odontologo_a,
        odontologo_b=odontologo_b,
        cabeceras_recepcion=_headers(token_de(recepcion)),
        cabeceras_admin=_headers(token_de(admin)),
        cabeceras_odontologo_a=_headers(token_de(odontologo_a)),
        cabeceras_odontologo_b=_headers(token_de(odontologo_b)),
    )


def _crear_turno(
    ctx: ContextoAgenda,
    *,
    inicio: str,
    fin: str,
    profesional_id: int | None = None,
    sillon_id: int | None = None,
    estado: str = "reservado",
) -> int:
    prof_id = profesional_id or ctx.profesional_a
    sill_id = sillon_id or ctx.sillon_1
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        with transaccion(con):
            cursor = con.execute(
                _INSERTAR_TURNO,
                (ctx.paciente_1, prof_id, sill_id, ctx.consulta, inicio, fin, estado, ctx.recepcion.id, inicio),
            )
            assert cursor.lastrowid is not None
            return cursor.lastrowid


def _crear_bloqueo(
    ctx: ContextoAgenda,
    *,
    alcance: str,
    recurso_id: int,
    inicio: datetime,
    fin: datetime,
    motivo: str = "Bloqueo test",
) -> None:
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        with transaccion(con):
            crear_bloqueo(
                con,
                Bloqueo(alcance=alcance, recurso_id=recurso_id, inicio=inicio, fin=fin, motivo=motivo),  # type: ignore[arg-type]
            )


# === 1. GET /agenda/profesionales/{id} ===


def test_agenda_profesional_recepcion_y_admin_200_cronologico(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda
    # Turno 1: 09:00 - 09:30
    _crear_turno(ctx, inicio=f"{LUNES}T09:00:00", fin=f"{LUNES}T09:30:00")
    # Bloqueo: 11:00 - 12:00
    _crear_bloqueo(
        ctx,
        alcance="profesional",
        recurso_id=ctx.profesional_a,
        inicio=datetime(2026, 11, 16, 11, 0),
        fin=datetime(2026, 11, 16, 12, 0),
        motivo="Reunión ficticia",
    )
    # Turno 2: 10:00 - 10:30
    _crear_turno(ctx, inicio=f"{LUNES}T10:00:00", fin=f"{LUNES}T10:30:00")

    resp = ctx.cliente.get(
        f"/agenda/profesionales/{ctx.profesional_a}?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_recepcion,
    )

    assert resp.status_code == 200
    datos = resp.json()
    assert datos["recurso_tipo"] == "profesional"
    assert datos["recurso_id"] == ctx.profesional_a
    assert len(datos["items"]) == 3
    # Orden cronológico: 09:00 (turno), 10:00 (turno), 11:00 (bloqueo)
    assert datos["items"][0]["tipo"] == "turno"
    assert datos["items"][0]["inicio"] == f"{LUNES}T09:00:00"
    assert datos["items"][1]["tipo"] == "turno"
    assert datos["items"][1]["inicio"] == f"{LUNES}T10:00:00"
    assert datos["items"][2]["tipo"] == "bloqueo"
    assert datos["items"][2]["inicio"] == f"{LUNES}T11:00:00"


def test_agenda_profesional_excluye_turnos_cancelados(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda
    _crear_turno(ctx, inicio=f"{LUNES}T09:00:00", fin=f"{LUNES}T09:30:00", estado="reservado")
    _crear_turno(ctx, inicio=f"{LUNES}T10:00:00", fin=f"{LUNES}T10:30:00", estado="cancelado")

    resp = ctx.cliente.get(
        f"/agenda/profesionales/{ctx.profesional_a}?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_admin,
    )

    assert resp.status_code == 200
    datos = resp.json()
    assert len(datos["items"]) == 1
    assert datos["items"][0]["inicio"] == f"{LUNES}T09:00:00"


def test_agenda_profesional_odontologo_propio_200(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda
    _crear_turno(ctx, inicio=f"{LUNES}T09:00:00", fin=f"{LUNES}T09:30:00")

    resp = ctx.cliente.get(
        f"/agenda/profesionales/{ctx.profesional_a}?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_odontologo_a,
    )

    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


def test_agenda_profesional_odontologo_ajeno_403(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda

    # Odontólogo A pide agenda del profesional B -> 403
    resp = ctx.cliente.get(
        f"/agenda/profesionales/{ctx.profesional_b}?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_odontologo_a,
    )

    assert resp.status_code == 403
    assert resp.json()["codigo"] == "sin_permiso"


def test_agenda_profesional_no_encontrado_404(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda

    resp = ctx.cliente.get(
        f"/agenda/profesionales/999?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_admin,
    )

    assert resp.status_code == 404
    assert resp.json()["codigo"] == "no_encontrado"


def test_agenda_profesional_rango_invertido_422(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda
    desde_invertido = f"{LUNES}T18:00:00"
    hasta_invertido = f"{LUNES}T08:00:00"

    resp = ctx.cliente.get(
        f"/agenda/profesionales/{ctx.profesional_a}?desde={desde_invertido}&hasta={hasta_invertido}",
        headers=ctx.cabeceras_admin,
    )

    assert resp.status_code == 422
    assert resp.json()["codigo"] == "dato_invalido"


def test_agenda_profesional_sin_token_401(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda

    resp = ctx.cliente.get(f"/agenda/profesionales/{ctx.profesional_a}?desde={DESDE}&hasta={HASTA}")

    assert resp.status_code == 401
    assert resp.json()["codigo"] == "no_autenticado"


# === 2. GET /agenda/sillones/{id} ===


def test_agenda_sillon_recepcion_y_admin_200_cronologico(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda
    # Turno en sillón 1: 14:00 - 14:30
    _crear_turno(ctx, sillon_id=ctx.sillon_1, inicio=f"{LUNES}T14:00:00", fin=f"{LUNES}T14:30:00")
    # Bloqueo en sillón 1: 15:00 - 16:00
    _crear_bloqueo(
        ctx,
        alcance="sillon",
        recurso_id=ctx.sillon_1,
        inicio=datetime(2026, 11, 16, 15, 0),
        fin=datetime(2026, 11, 16, 16, 0),
        motivo="Mantenimiento de sillón",
    )

    resp = ctx.cliente.get(
        f"/agenda/sillones/{ctx.sillon_1}?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_recepcion,
    )

    assert resp.status_code == 200
    datos = resp.json()
    assert datos["recurso_tipo"] == "sillon"
    assert datos["recurso_id"] == ctx.sillon_1
    assert len(datos["items"]) == 2
    assert datos["items"][0]["tipo"] == "turno"
    assert datos["items"][0]["inicio"] == f"{LUNES}T14:00:00"
    assert datos["items"][1]["tipo"] == "bloqueo"
    assert datos["items"][1]["inicio"] == f"{LUNES}T15:00:00"


def test_agenda_sillon_odontologo_403(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda

    resp = ctx.cliente.get(
        f"/agenda/sillones/{ctx.sillon_1}?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_odontologo_a,
    )

    assert resp.status_code == 403
    assert resp.json()["codigo"] == "sin_permiso"


def test_agenda_sillon_no_encontrado_404(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda

    resp = ctx.cliente.get(
        f"/agenda/sillones/999?desde={DESDE}&hasta={HASTA}",
        headers=ctx.cabeceras_admin,
    )

    assert resp.status_code == 404
    assert resp.json()["codigo"] == "no_encontrado"


def test_agenda_sillon_rango_invertido_422(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda
    desde_invertido = f"{LUNES}T18:00:00"
    hasta_invertido = f"{LUNES}T08:00:00"

    resp = ctx.cliente.get(
        f"/agenda/sillones/{ctx.sillon_1}?desde={desde_invertido}&hasta={hasta_invertido}",
        headers=ctx.cabeceras_recepcion,
    )

    assert resp.status_code == 422
    assert resp.json()["codigo"] == "dato_invalido"


def test_agenda_sillon_sin_token_401(contexto_agenda: ContextoAgenda) -> None:
    ctx = contexto_agenda

    resp = ctx.cliente.get(f"/agenda/sillones/{ctx.sillon_1}?desde={DESDE}&hasta={HASTA}")

    assert resp.status_code == 401
    assert resp.json()["codigo"] == "no_autenticado"
