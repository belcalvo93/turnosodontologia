"""API de cancelación: POST /turnos/{id}/cancelar (C-12)."""

import json
from collections.abc import Callable
from contextlib import closing

from app.db.conexion import abrir_conexion
from tests.api.test_turnos import LUNES, ContextoTurnos, contexto_turnos  # noqa: F401
from app.domain.usuarios import Usuario
from tests.conftest import RelojFijo

# el reloj de los tests arranca el lunes anterior a las 09:00 hora local
UNA_SEMANA = 7 * 24 * 60


def _avanzar(
    ctx: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str], *, minutos: int
) -> None:
    """Adelanta el reloj y vuelve a emitir los tokens, que vencen a los 60 minutos."""
    reloj.avanzar(minutes=minutos)
    ctx.cabeceras_recepcion = {"Authorization": f"Bearer {token_de(ctx.recepcion)}"}
    ctx.cabeceras_admin = {"Authorization": f"Bearer {token_de(ctx.admin)}"}
    ctx.cabeceras_odontologo_a = {"Authorization": f"Bearer {token_de(ctx.odontologo_a)}"}


def _reservar_turno_de_las_10(ctx: ContextoTurnos) -> int:
    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:00:00"))
    assert respuesta.status_code == 201
    return int(respuesta.json()["id"])


def _cancelar(ctx: ContextoTurnos, turno_id: int, cabeceras: dict[str, str] | None = None):  # type: ignore[no-untyped-def]
    return ctx.cliente.post(f"/turnos/{turno_id}/cancelar", headers=cabeceras)


def _auditorias_cancelar(ctx: ContextoTurnos) -> list[tuple]:  # type: ignore[type-arg]
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        return con.execute(
            "SELECT turno_id, usuario_id, ocurrio_en, antes, despues FROM auditoria_turno "
            "WHERE accion = 'cancelar' ORDER BY id"
        ).fetchall()


def _estado(ctx: ContextoTurnos, turno_id: int) -> str:
    respuesta = ctx.cliente.get(f"/turnos/{turno_id}", headers=ctx.cabeceras_recepcion)
    return str(respuesta.json()["estado"])


# --- 3.1 cancelación de un turno futuro ---


def test_recepcion_cancela_turno_futuro_200_y_registra_auditoria(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA)  # lunes 09:00

    respuesta = _cancelar(ctx, turno_id, ctx.cabeceras_recepcion)

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "cancelado"
    assert respuesta.json()["id"] == turno_id
    auditorias = _auditorias_cancelar(ctx)
    assert len(auditorias) == 1
    turno_auditado, usuario_id, ocurrio_en, antes, despues = auditorias[0]
    assert (turno_auditado, usuario_id, ocurrio_en) == (turno_id, ctx.recepcion.id, f"{LUNES}T09:00:00")
    assert json.loads(antes)["estado"] == "reservado"
    assert json.loads(despues)["estado"] == "cancelado"


def test_administracion_tambien_puede_cancelar(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA)

    respuesta = _cancelar(ctx, turno_id, ctx.cabeceras_admin)

    assert respuesta.status_code == 200
    assert _auditorias_cancelar(ctx)[0][1] == ctx.admin.id


def test_turno_en_el_instante_exacto_de_inicio_409_y_sigue_reservado(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA + 60)  # lunes 10:00 justo

    respuesta = _cancelar(ctx, turno_id, ctx.cabeceras_recepcion)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "turno_no_modificable"
    assert _estado(ctx, turno_id) == "reservado"
    assert _auditorias_cancelar(ctx) == []


def test_turno_pasado_409_y_sigue_reservado(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA + 90)  # lunes 10:30

    respuesta = _cancelar(ctx, turno_id, ctx.cabeceras_recepcion)

    assert respuesta.status_code == 409
    assert _estado(ctx, turno_id) == "reservado"
    assert _auditorias_cancelar(ctx) == []


def test_segunda_cancelacion_409_sin_nueva_auditoria(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA)
    assert _cancelar(ctx, turno_id, ctx.cabeceras_recepcion).status_code == 200

    respuesta = _cancelar(ctx, turno_id, ctx.cabeceras_admin)

    assert respuesta.status_code == 409
    assert respuesta.json()["mensaje"] == "El turno ya está cancelado."
    assert len(_auditorias_cancelar(ctx)) == 1


def test_turno_inexistente_404(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos

    respuesta = _cancelar(ctx, 9999, ctx.cabeceras_recepcion)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


# --- 3.2 liberación del horario y control de acceso ---


def test_tras_cancelar_se_puede_reservar_el_mismo_hueco_201(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA)
    assert _cancelar(ctx, turno_id, ctx.cabeceras_recepcion).status_code == 200

    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:00:00"))

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "reservado"
    assert respuesta.json()["id"] != turno_id


def test_sin_cancelar_el_mismo_hueco_sigue_ocupado_409(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA)

    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:00:00"))

    assert respuesta.status_code == 409


def test_odontologo_no_puede_cancelar_403_y_sigue_reservado(
    contexto_turnos: ContextoTurnos, reloj: RelojFijo, token_de: Callable[[Usuario], str]
) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)
    _avanzar(ctx, reloj, token_de, minutos=UNA_SEMANA)

    respuesta = _cancelar(ctx, turno_id, ctx.cabeceras_odontologo_a)

    assert respuesta.status_code == 403
    assert _estado(ctx, turno_id) == "reservado"
    assert _auditorias_cancelar(ctx) == []


def test_sin_token_401(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno_id = _reservar_turno_de_las_10(ctx)

    respuesta = _cancelar(ctx, turno_id)

    assert respuesta.status_code == 401
