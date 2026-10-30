"""API de reprogramación: POST /turnos/{id}/reprogramar (C-13, US-008, RN-TUR-07..10, RN-AUD-03)."""

import json
import sqlite3
import threading
from collections.abc import Callable
from contextlib import closing

import pytest

from app.db.conexion import abrir_conexion, transaccion
from app.db.repositorio_turnos import reprogramar_turno as reprogramar_turno_real
from app.domain.usuarios import Usuario
from tests.api.test_turnos import (  # noqa: F401  (contexto_turnos es una fixture)
    CLAVES_SNAPSHOT,
    LUNES,
    ContextoTurnos,
    _auditorias,
    _bloquear,
    _cantidad,
    _consultar,
    _headers,
    contexto_turnos,
)
from tests.conftest import RelojFijo

# 10:00 del lunes es futuro respecto del reloj fijo (2026-01-05 09:00 local).
INICIO_ORIGINAL = f"{LUNES}T10:00:00"


def _reservar(ctx: ContextoTurnos, **cambios: object) -> dict[str, object]:
    respuesta = ctx.reservar(ctx.cuerpo(INICIO_ORIGINAL, **cambios))
    assert respuesta.status_code == 201
    return respuesta.json()  # type: ignore[no-any-return]


def _reprogramar(
    ctx: ContextoTurnos,
    turno_id: object,
    nuevo_inicio: str,
    cabeceras: dict[str, str] | None = None,
    **extra: object,
):  # type: ignore[no-untyped-def]
    return ctx.cliente.post(
        f"/turnos/{turno_id}/reprogramar",
        json={"nuevo_inicio": nuevo_inicio, **extra},
        headers=cabeceras or ctx.cabeceras_recepcion,
    )


def _fila_turno(ctx: ContextoTurnos, turno_id: object) -> tuple:  # type: ignore[type-arg]
    return _consultar(
        ctx,
        "SELECT id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado "
        "FROM turno WHERE id = ?",
        (turno_id,),
    )[0]


def _assert_rechazo_sin_cambios(
    ctx: ContextoTurnos, turno: dict[str, object], auditorias_antes: int
) -> None:
    assert _fila_turno(ctx, turno["id"]) == tuple(turno.values())
    assert _cantidad(ctx, "auditoria") == auditorias_antes


# --- éxito ---


def test_reprogramar_recepcion_mueve_el_turno_200_conservando_el_id(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        **turno,
        "inicio": f"{LUNES}T11:00:00",
        "fin": f"{LUNES}T11:30:00",
    }
    assert _fila_turno(ctx, turno["id"]) == tuple(respuesta.json().values())


def test_reprogramar_administracion_tambien_puede_200(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T12:00:00", ctx.cabeceras_admin)

    assert respuesta.status_code == 200
    assert respuesta.json()["inicio"] == f"{LUNES}T12:00:00"
    assert respuesta.json()["estado"] == "reservado"


def test_reprogramar_sobre_su_propio_horario_previo_200(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)  # 10:00-10:30

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T10:15:00")

    assert respuesta.status_code == 200
    assert respuesta.json()["inicio"] == f"{LUNES}T10:15:00"
    assert respuesta.json()["fin"] == f"{LUNES}T10:45:00"


def test_reprogramar_con_otro_profesional_y_sillon_los_persiste_200(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = _reprogramar(
        ctx,
        turno["id"],
        f"{LUNES}T11:00:00",
        nuevo_profesional_id=ctx.profesional_b,
        nuevo_sillon_id=ctx.sillon_2,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["profesional_id"] == ctx.profesional_b
    assert respuesta.json()["sillon_id"] == ctx.sillon_2
    assert _fila_turno(ctx, turno["id"]) == tuple(respuesta.json().values())


def test_reprogramar_registra_auditoria_reprogramar_con_antes_y_despues(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos  # el reloj fijo marca 2026-01-05T12:00Z = 09:00 local
    turno = _reservar(ctx)

    nuevo = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00").json()

    auditorias = _auditorias(ctx)
    assert len(auditorias) == 2
    turno_id, accion, usuario_id, ocurrio_en, antes, despues = auditorias[1]
    assert (turno_id, accion, usuario_id) == (turno["id"], "reprogramar", ctx.recepcion.id)
    assert ocurrio_en == "2026-01-05T09:00:00"
    assert list(json.loads(antes)) == CLAVES_SNAPSHOT
    assert json.loads(antes) == turno
    assert json.loads(despues) == nuevo


# --- RBAC y 404 ---


def test_reprogramar_odontologo_403_sin_permiso_y_no_cambia_nada(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00", ctx.cabeceras_odontologo_a)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    _assert_rechazo_sin_cambios(ctx, turno, 1)


def test_reprogramar_sin_token_401_no_autenticado(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = ctx.cliente.post(
        f"/turnos/{turno['id']}/reprogramar", json={"nuevo_inicio": f"{LUNES}T11:00:00"}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
    _assert_rechazo_sin_cambios(ctx, turno, 1)


def test_reprogramar_turno_inexistente_404_no_encontrado(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = _reprogramar(ctx, 9999, f"{LUNES}T11:00:00")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"
    assert _cantidad(ctx, "auditoria") == 0


def test_reprogramar_odontologo_sobre_turno_inexistente_responde_403_antes_que_404(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = _reprogramar(ctx, 9999, f"{LUNES}T11:00:00", ctx.cabeceras_odontologo_a)

    assert respuesta.status_code == 403


# --- recursos nuevos (422) y orden de rechazo ---


def _desactivar(ctx: ContextoTurnos, tabla: str, recurso_id: int) -> None:
    sentencias = {
        "profesional": "UPDATE profesional SET activo = 0 WHERE id = ?",
        "sillon": "UPDATE sillon SET activo = 0 WHERE id = ?",
    }
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        con.execute(sentencias[tabla], (recurso_id,))


@pytest.mark.parametrize(
    ("campo", "mensaje"),
    [
        ("nuevo_profesional_id", "El profesional indicado no existe."),
        ("nuevo_sillon_id", "El sillón indicado no existe."),
    ],
)
def test_reprogramar_con_recurso_nuevo_inexistente_422_dato_invalido(
    contexto_turnos: ContextoTurnos, campo: str, mensaje: str
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00", **{campo: 99})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert respuesta.json()["mensaje"] == mensaje
    _assert_rechazo_sin_cambios(ctx, turno, 1)


@pytest.mark.parametrize(
    ("tabla", "campo", "atributo", "mensaje"),
    [
        ("profesional", "nuevo_profesional_id", "profesional_b", "El profesional indicado está inactivo."),
        ("sillon", "nuevo_sillon_id", "sillon_2", "El sillón indicado está inactivo."),
    ],
)
def test_reprogramar_con_recurso_nuevo_inactivo_422_dato_invalido(
    contexto_turnos: ContextoTurnos, tabla: str, campo: str, atributo: str, mensaje: str
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    _desactivar(ctx, tabla, getattr(ctx, atributo))

    respuesta = _reprogramar(
        ctx, turno["id"], f"{LUNES}T11:00:00", **{campo: getattr(ctx, atributo)}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert respuesta.json()["mensaje"] == mensaje
    _assert_rechazo_sin_cambios(ctx, turno, 1)


def test_reprogramar_recurso_nuevo_inactivo_con_conflicto_responde_422_antes_que_409(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    # Otro paciente ocupa el sillón 2 a las 11:00: el sillón 2 conflictúa y además está inactivo.
    otro = ctx.reservar(
        ctx.cuerpo(
            f"{LUNES}T11:00:00",
            paciente_id=ctx.paciente_2,
            profesional_id=ctx.profesional_b,
            sillon_id=ctx.sillon_2,
        )
    )
    assert otro.status_code == 201
    _desactivar(ctx, "sillon", ctx.sillon_2)

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00", nuevo_sillon_id=ctx.sillon_2)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    _assert_rechazo_sin_cambios(ctx, turno, 2)


def test_reprogramar_con_sillon_vigente_inactivo_que_no_se_envia_200(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    _desactivar(ctx, "sillon", ctx.sillon_1)  # el sillón actual del turno

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00")

    assert respuesta.status_code == 200
    assert respuesta.json()["sillon_id"] == ctx.sillon_1


def _cancelar(ctx: ContextoTurnos, turno_id: object) -> None:
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        con.execute("UPDATE turno SET estado = 'cancelado' WHERE id = ?", (turno_id,))


def test_reprogramar_turno_cancelado_con_nuevo_sillon_inactivo_409_y_sin_auditoria(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    _cancelar(ctx, turno["id"])
    _desactivar(ctx, "sillon", ctx.sillon_2)
    cancelado = {**turno, "estado": "cancelado"}

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00", nuevo_sillon_id=ctx.sillon_2)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "turno_no_modificable"
    _assert_rechazo_sin_cambios(ctx, cancelado, 1)


def test_reprogramar_turno_cancelado_409_turno_no_modificable(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    _cancelar(ctx, turno["id"])

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:00:00")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "turno_no_modificable"
    assert _fila_turno(ctx, turno["id"])[7] == "cancelado"


# --- forma de la entrada ---


@pytest.mark.parametrize("valor", [f"{LUNES}T11:00:00-03:00", f"{LUNES}T11:00:00Z"])
def test_reprogramar_con_nuevo_inicio_con_zona_422_en_el_campo(
    contexto_turnos: ContextoTurnos, valor: str
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = _reprogramar(ctx, turno["id"], valor)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert [d["campo"] for d in respuesta.json()["detalles"]] == ["nuevo_inicio"]
    _assert_rechazo_sin_cambios(ctx, turno, 1)


def test_reprogramar_sin_nuevo_inicio_422_en_el_campo(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = ctx.cliente.post(
        f"/turnos/{turno['id']}/reprogramar", json={}, headers=ctx.cabeceras_recepcion
    )

    assert respuesta.status_code == 422
    assert [d["campo"] for d in respuesta.json()["detalles"]] == ["nuevo_inicio"]


# --- reloj: hora local frente a UTC (C-11 D3) ---


def test_reprogramar_turno_futuro_en_hora_local_aunque_en_utc_ya_pasaria_200(
    contexto_turnos: ContextoTurnos,
    reloj: RelojFijo,
    token_de: Callable[[Usuario], str],
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)  # lunes 10:00 local
    reloj.avanzar(minutes=10020)  # lunes 11:00Z = 08:00 local: el turno aún es futuro
    cabeceras = _headers(token_de(ctx.recepcion))

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T12:00:00", cabeceras)

    assert respuesta.status_code == 200


def test_reprogramar_turno_pasado_en_hora_local_409(
    contexto_turnos: ContextoTurnos,
    reloj: RelojFijo,
    token_de: Callable[[Usuario], str],
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    reloj.avanzar(minutes=10170)  # lunes 13:30Z = 10:30 local: el turno de 10:00 ya empezó
    cabeceras = _headers(token_de(ctx.recepcion))

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T12:00:00", cabeceras)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "turno_no_modificable"
    _assert_rechazo_sin_cambios(ctx, turno, 1)


# --- agenda: 409 sin tocar la auditoría ---


def test_reprogramar_sobre_otro_turno_del_profesional_409_conflicto_agenda(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)  # 10:00-10:30
    otro = ctx.reservar(
        ctx.cuerpo(f"{LUNES}T11:00:00", paciente_id=ctx.paciente_2, sillon_id=ctx.sillon_2)
    )
    assert otro.status_code == 201

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:15:00")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "conflicto_agenda"
    _assert_rechazo_sin_cambios(ctx, turno, 2)


def test_reprogramar_contiguo_a_otro_turno_200(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    ctx.reservar(
        ctx.cuerpo(f"{LUNES}T11:00:00", paciente_id=ctx.paciente_2, sillon_id=ctx.sillon_2)
    )

    assert _reprogramar(ctx, turno["id"], f"{LUNES}T11:30:00").status_code == 200


def test_reprogramar_dentro_de_un_bloqueo_409_dentro_de_bloqueo(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)
    _bloquear(ctx, "sillon", ctx.sillon_1, f"{LUNES}T11:00:00", f"{LUNES}T12:00:00")

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:30:00")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "dentro_de_bloqueo"
    _assert_rechazo_sin_cambios(ctx, turno, 1)


def test_reprogramar_fuera_de_horario_409_fuera_de_horario(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T12:45:00")  # la franja termina 13:00

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "fuera_de_horario"
    _assert_rechazo_sin_cambios(ctx, turno, 1)


def test_reprogramar_a_otro_profesional_valida_el_horario_de_ese_profesional(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)

    # Martes: el profesional B no atiende ese día (solo los lunes).
    respuesta = _reprogramar(
        ctx, turno["id"], "2026-01-13T10:00:00", nuevo_profesional_id=ctx.profesional_b
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "fuera_de_horario"
    _assert_rechazo_sin_cambios(ctx, turno, 1)


# --- RN-TUR-11: nadie fuerza solapamientos (C-13 3.5) ---


def test_reprogramar_como_administracion_a_un_hueco_ocupado_409_conflicto_agenda(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    turno = _reservar(ctx)  # 10:00-10:30
    ocupante = ctx.reservar(
        ctx.cuerpo(f"{LUNES}T11:00:00", paciente_id=ctx.paciente_2, sillon_id=ctx.sillon_2)
    )
    assert ocupante.status_code == 201

    respuesta = _reprogramar(ctx, turno["id"], f"{LUNES}T11:15:00", ctx.cabeceras_admin)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "conflicto_agenda"
    _assert_rechazo_sin_cambios(ctx, turno, 2)


# --- SE-06 / C-11 D1: dos reprogramaciones concurrentes al mismo hueco (C-13 3.6) ---

ESPERA_MAXIMA_S = 10  # solo evita colgar la suite si algo falla; no hay esperas por tiempo


def test_dos_reprogramaciones_concurrentes_al_mismo_hueco_una_200_y_la_otra_409(
    contexto_turnos: ContextoTurnos, monkeypatch: pytest.MonkeyPatch
) -> None:
    """La conexión de B espera el lock de A y, al obtenerlo, ve la reprogramación ya confirmada.

    Determinista y sin `sleep`: A queda detenida dentro de su transacción (ya escribió, no
    confirmó) con un `Event`; B se lanza recién entonces y avisa con otro `Event` cuando su
    conexión ejecuta `BEGIN IMMEDIATE`. Solo después A continúa y confirma.
    Si el router validara fuera de la transacción, B habría leído el contexto antes de ese
    aviso, sin ver a A, y ambas reprogramaciones se aplicarían.
    """
    ctx = contexto_turnos
    turno_a = _reservar(ctx)  # 10:00-10:30, paciente 1
    turno_b = ctx.reservar(ctx.cuerpo(f"{LUNES}T09:00:00", paciente_id=ctx.paciente_2)).json()
    hueco = f"{LUNES}T11:00:00"

    a_escribio = threading.Event()  # A ya hizo el UPDATE y sigue sin confirmar
    a_continua = threading.Event()
    b_habilitada = threading.Event()  # desde acá se vigila el BEGIN IMMEDIATE de B
    b_pide_el_lock = threading.Event()
    primera_escritura = threading.Event()

    def reprogramar_pausando(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        resultado = reprogramar_turno_real(*args, **kwargs)  # type: ignore[arg-type]
        if not primera_escritura.is_set():  # solo A se detiene; B (si llegara) sigue de largo
            primera_escritura.set()
            a_escribio.set()
            assert a_continua.wait(ESPERA_MAXIMA_S)
        return resultado

    def abrir_con_aviso(ruta):  # type: ignore[no-untyped-def]
        conexion = abrir_conexion(ruta)

        def al_ejecutar(sentencia: str) -> None:
            if b_habilitada.is_set() and sentencia.startswith("BEGIN IMMEDIATE"):
                b_pide_el_lock.set()

        conexion.set_trace_callback(al_ejecutar)
        return conexion

    monkeypatch.setattr("app.api.turnos.reprogramar_turno", reprogramar_pausando)
    monkeypatch.setattr("app.api.dependencias.abrir_conexion", abrir_con_aviso)

    respuestas: dict[str, object] = {}

    def lanzar(nombre: str, turno_id: object) -> None:
        respuestas[nombre] = _reprogramar(ctx, turno_id, hueco)

    hilo_a = threading.Thread(target=lanzar, args=("a", turno_a["id"]))
    hilo_b = threading.Thread(target=lanzar, args=("b", turno_b["id"]))
    hilo_a.start()
    try:
        assert a_escribio.wait(ESPERA_MAXIMA_S)
        # A conserva el lock de escritura: una tercera conexión no puede tomarlo.
        with closing(abrir_conexion(ctx.config.database_path)) as sonda:
            sonda.execute("PRAGMA busy_timeout = 50")  # solo en este test
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                with transaccion(sonda):
                    pytest.fail("A debería conservar el lock de escritura")
        b_habilitada.set()
        hilo_b.start()
        assert b_pide_el_lock.wait(ESPERA_MAXIMA_S)
    finally:
        a_continua.set()  # A confirma; B toma el lock y ve la reprogramación de A
        hilo_a.join(ESPERA_MAXIMA_S)
        if hilo_b.ident is not None:  # B puede no haberse lanzado si falló una espera anterior
            hilo_b.join(ESPERA_MAXIMA_S)

    assert not hilo_a.is_alive() and not hilo_b.is_alive()
    respuesta_a, respuesta_b = respuestas["a"], respuestas["b"]
    assert respuesta_a.status_code == 200  # type: ignore[attr-defined]
    assert respuesta_b.status_code == 409  # type: ignore[attr-defined]
    assert respuesta_b.json()["codigo"] == "conflicto_agenda"  # type: ignore[attr-defined]
    assert _fila_turno(ctx, turno_a["id"])[5] == hueco
    assert _fila_turno(ctx, turno_b["id"]) == tuple(turno_b.values())  # B quedó como estaba
    reprogramaciones = _consultar(
        ctx, "SELECT turno_id FROM auditoria_turno WHERE accion = 'reprogramar'"
    )
    assert reprogramaciones == [(turno_a["id"],)]
