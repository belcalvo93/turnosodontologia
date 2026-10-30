"""API de turnos: alta con POST /turnos (C-11)."""

from collections.abc import Callable
from contextlib import closing
import json
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
from tests.conftest import RelojFijo

LUNES = "2026-01-12"


@dataclass
class ContextoTurnos:
    """Ids y cabeceras de un consultorio ficticio listo para reservar."""

    cliente: TestClient
    config: Config
    profesional_a: int
    profesional_b: int
    sillon_1: int
    sillon_2: int
    consulta: int  # 30 minutos
    limpieza: int  # 45 minutos
    paciente_1: int
    paciente_2: int
    recepcion: Usuario
    admin: Usuario
    odontologo_a: Usuario
    cabeceras_recepcion: dict[str, str]
    cabeceras_admin: dict[str, str]
    cabeceras_odontologo_a: dict[str, str]

    def cuerpo(self, inicio: str = f"{LUNES}T10:00:00", **cambios: object) -> dict[str, object]:
        """Cuerpo válido de POST /turnos (profesional A, sillón 1, consulta, paciente 1)."""
        base: dict[str, object] = {
            "paciente_id": self.paciente_1,
            "profesional_id": self.profesional_a,
            "sillon_id": self.sillon_1,
            "prestacion_id": self.consulta,
            "inicio": inicio,
        }
        base.update(cambios)
        return base

    def reservar(self, cuerpo: dict[str, object], cabeceras: dict[str, str] | None = None):  # type: ignore[no-untyped-def]
        return self.cliente.post(
            "/turnos", json=cuerpo, headers=cabeceras or self.cabeceras_recepcion
        )


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def contexto_turnos(
    cliente: TestClient,
    config: Config,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> ContextoTurnos:
    with closing(abrir_conexion(config.database_path)) as con:
        with transaccion(con):
            prof_a = crear_profesional(con, nombre="Odontólogo", apellido="Ficticio A")
            prof_b = crear_profesional(con, nombre="Odontóloga", apellido="Ficticia B")
            assert prof_a.id is not None and prof_b.id is not None
            for profesional_id in (prof_a.id, prof_b.id):
                crear_horario(
                    con,
                    HorarioAtencion(
                        profesional_id=profesional_id,
                        dia_semana=0,
                        hora_desde=time(9, 0),
                        hora_hasta=time(13, 0),
                    ),
                )
            sillon_1 = crear_sillon(con, nombre="Sillón 1")
            sillon_2 = crear_sillon(con, nombre="Sillón 2")
            consulta = crear_prestacion(con, nombre="Consulta ficticia", duracion_minutos=30)
            limpieza = crear_prestacion(con, nombre="Limpieza ficticia", duracion_minutos=45)
            pac_1 = crear_paciente(
                con, nombre="Paciente", apellido="Ficticio 1", dni="00000001 (ficticio)"
            )
            pac_2 = crear_paciente(
                con, nombre="Paciente", apellido="Ficticio 2", dni="00000002 (ficticio)"
            )
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    odontologo_a = crear_usuario(
        "odontologo_a_ficticio", rol=Rol.ODONTOLOGO, profesional_id=prof_a.id
    )
    return ContextoTurnos(
        cliente=cliente,
        config=config,
        profesional_a=prof_a.id,
        profesional_b=prof_b.id,
        sillon_1=sillon_1.id,  # type: ignore[arg-type]
        sillon_2=sillon_2.id,  # type: ignore[arg-type]
        consulta=consulta.id,
        limpieza=limpieza.id,
        paciente_1=pac_1.id,  # type: ignore[arg-type]
        paciente_2=pac_2.id,  # type: ignore[arg-type]
        recepcion=recepcion,
        admin=admin,
        odontologo_a=odontologo_a,
        cabeceras_recepcion=_headers(token_de(recepcion)),
        cabeceras_admin=_headers(token_de(admin)),
        cabeceras_odontologo_a=_headers(token_de(odontologo_a)),
    )


# --- 5.1 alta feliz ---


def test_post_turnos_recepcion_crea_turno_reservado_201(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo())

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id"] >= 1
    assert cuerpo == {
        "id": cuerpo["id"],
        "paciente_id": ctx.paciente_1,
        "profesional_id": ctx.profesional_a,
        "sillon_id": ctx.sillon_1,
        "prestacion_id": ctx.consulta,
        "inicio": f"{LUNES}T10:00:00",
        "fin": f"{LUNES}T10:30:00",
        "estado": "reservado",
    }


def _consultar(ctx: ContextoTurnos, sql: str, parametros: tuple[object, ...] = ()) -> list[tuple]:  # type: ignore[type-arg]
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        return con.execute(sql, parametros).fetchall()


def _cantidad(ctx: ContextoTurnos, tabla: str) -> int:
    consultas = {
        "turno": "SELECT COUNT(*) FROM turno",
        "auditoria": "SELECT COUNT(*) FROM auditoria_turno",
    }
    return int(_consultar(ctx, consultas[tabla])[0][0])


def test_post_turnos_con_limpieza_de_45_minutos_calcula_fin_10_45(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo(prestacion_id=ctx.limpieza))

    assert respuesta.status_code == 201
    assert respuesta.json()["fin"] == f"{LUNES}T10:45:00"


def test_post_turnos_administracion_tambien_crea_turno_201(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo(), ctx.cabeceras_admin)

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "reservado"


def test_post_turnos_el_turno_creado_queda_persistido_en_la_base(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    creado = ctx.reservar(ctx.cuerpo()).json()

    filas = _consultar(
        ctx,
        "SELECT id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado "
        "FROM turno WHERE id = ?",
        (creado["id"],),
    )
    assert filas == [tuple(creado.values())]


# --- 5.2 solapamientos ---


def _reservar_base(ctx: ContextoTurnos) -> None:
    """Turno de profesional A, sillón 1, paciente 1, 10:00-10:30."""
    assert ctx.reservar(ctx.cuerpo()).status_code == 201


@pytest.mark.parametrize(
    "cambios",
    [
        {"sillon_id": "sillon_2", "paciente_id": "paciente_2"},
        {"profesional_id": "profesional_b", "paciente_id": "paciente_2"},
        {"profesional_id": "profesional_b", "sillon_id": "sillon_2"},
    ],
    ids=["por_profesional", "por_sillon", "por_paciente"],
)
def test_post_turnos_solapado_por_un_recurso_compartido_responde_409_conflicto_agenda(
    contexto_turnos: ContextoTurnos, cambios: dict[str, str]
) -> None:
    ctx = contexto_turnos
    _reservar_base(ctx)
    ids = {campo: getattr(ctx, atributo) for campo, atributo in cambios.items()}

    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:15:00", **ids))

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "conflicto_agenda"
    assert respuesta.json()["mensaje"]
    assert _cantidad(ctx, "turno") == 1


@pytest.mark.parametrize("hora", ["10:30:00", "09:30:00"])
def test_post_turnos_contiguos_antes_y_despues_se_aceptan(
    contexto_turnos: ContextoTurnos, hora: str
) -> None:
    ctx = contexto_turnos
    _reservar_base(ctx)

    assert ctx.reservar(ctx.cuerpo(f"{LUNES}T{hora}")).status_code == 201


def test_post_turnos_con_un_minuto_de_superposicion_responde_409(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    _reservar_base(ctx)

    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:29:00"))

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "conflicto_agenda"


def test_post_turnos_en_el_hueco_de_un_turno_cancelado_responde_201(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    _reservar_base(ctx)
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        con.execute("UPDATE turno SET estado = 'cancelado'")

    assert ctx.reservar(ctx.cuerpo()).status_code == 201


# --- 5.3 fuera de horario y bloqueos ---


def test_post_turnos_que_cruza_el_fin_de_la_franja_responde_409_fuera_de_horario(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T12:45:00"))

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "fuera_de_horario"
    assert respuesta.json()["mensaje"]


def test_post_turnos_en_dia_sin_horario_responde_409_fuera_de_horario(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo("2026-01-13T10:00:00"))  # martes

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "fuera_de_horario"


def _bloquear(ctx: ContextoTurnos, alcance: str, recurso_id: int, desde: str, hasta: str) -> None:
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        with transaccion(con):
            crear_bloqueo(
                con,
                Bloqueo(
                    alcance=alcance,  # type: ignore[arg-type]
                    recurso_id=recurso_id,
                    inicio=datetime.fromisoformat(desde),
                    fin=datetime.fromisoformat(hasta),
                    motivo="Ficticio",
                ),
            )


def test_post_turnos_dentro_de_un_bloqueo_de_sillon_solo_afecta_a_ese_sillon_y_horario(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    _bloquear(ctx, "sillon", ctx.sillon_1, f"{LUNES}T10:00:00", f"{LUNES}T12:00:00")

    bloqueado = ctx.reservar(ctx.cuerpo(f"{LUNES}T11:00:00"))
    otro_sillon = ctx.reservar(ctx.cuerpo(f"{LUNES}T11:00:00", sillon_id=ctx.sillon_2))
    contiguo = ctx.reservar(ctx.cuerpo(f"{LUNES}T12:00:00"))

    assert bloqueado.status_code == 409
    assert bloqueado.json()["codigo"] == "dentro_de_bloqueo"
    assert otro_sillon.status_code == 201
    assert contiguo.status_code == 201


def test_post_turnos_dentro_de_un_bloqueo_de_profesional_de_todo_el_dia_responde_409(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    _bloquear(ctx, "profesional", ctx.profesional_a, f"{LUNES}T00:00:00", "2026-01-13T00:00:00")

    respuesta = ctx.reservar(ctx.cuerpo())

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "dentro_de_bloqueo"


# --- 5.4 dato inválido ---


def _assert_sin_escrituras(ctx: ContextoTurnos) -> None:
    assert _cantidad(ctx, "turno") == 0
    assert _cantidad(ctx, "auditoria") == 0


def test_post_turnos_sin_sillon_id_responde_422_con_detalle_del_campo(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    cuerpo = ctx.cuerpo()
    del cuerpo["sillon_id"]

    respuesta = ctx.reservar(cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert [d["campo"] for d in respuesta.json()["detalles"]] == ["sillon_id"]
    _assert_sin_escrituras(ctx)


@pytest.mark.parametrize(
    ("tabla", "campo", "atributo"),
    [
        ("sillon", "sillon_id", "sillon_2"),
        ("profesional", "profesional_id", "profesional_b"),
        ("prestacion", "prestacion_id", "limpieza"),
    ],
)
def test_post_turnos_con_recurso_inactivo_responde_422_y_no_escribe(
    contexto_turnos: ContextoTurnos, tabla: str, campo: str, atributo: str
) -> None:
    ctx = contexto_turnos
    bajas = {
        "sillon": "UPDATE sillon SET activo = 0 WHERE id = ?",
        "profesional": "UPDATE profesional SET activo = 0 WHERE id = ?",
        "prestacion": "UPDATE prestacion SET activa = 0 WHERE id = ?",
    }
    with closing(abrir_conexion(ctx.config.database_path)) as con:
        con.execute(bajas[tabla], (getattr(ctx, atributo),))

    respuesta = ctx.reservar(ctx.cuerpo(**{campo: getattr(ctx, atributo)}))

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert respuesta.json()["mensaje"]
    _assert_sin_escrituras(ctx)


@pytest.mark.parametrize("campo", ["paciente_id", "profesional_id", "sillon_id", "prestacion_id"])
def test_post_turnos_con_recurso_inexistente_responde_422_y_no_escribe(
    contexto_turnos: ContextoTurnos, campo: str
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo(**{campo: 9999}))

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    _assert_sin_escrituras(ctx)


@pytest.mark.parametrize("inicio", [f"{LUNES}T10:00:00-03:00", f"{LUNES}T10:00:00Z"])
def test_post_turnos_con_inicio_con_zona_horaria_responde_422_en_el_campo_inicio(
    contexto_turnos: ContextoTurnos, inicio: str
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo(inicio))

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert [d["campo"] for d in respuesta.json()["detalles"]] == ["inicio"]
    _assert_sin_escrituras(ctx)


# --- 5.5 doble reserva ---


def test_post_turnos_doble_reserva_del_mismo_hueco_la_segunda_responde_409(
    contexto_turnos: ContextoTurnos,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    ctx = contexto_turnos
    otra_recepcion = crear_usuario("recepcion_2_ficticia", rol=Rol.RECEPCION)
    cuerpo = ctx.cuerpo()

    primera = ctx.reservar(cuerpo)
    segunda = ctx.reservar(cuerpo, _headers(token_de(otra_recepcion)))

    assert primera.status_code == 201
    assert segunda.status_code == 409
    assert segunda.json()["codigo"] == "conflicto_agenda"
    assert _cantidad(ctx, "turno") == 1
    assert _cantidad(ctx, "auditoria") == 1


def test_post_turnos_administracion_tampoco_puede_superponer_un_turno(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    _reservar_base(ctx)

    respuesta = ctx.reservar(ctx.cuerpo(f"{LUNES}T10:15:00"), ctx.cabeceras_admin)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "conflicto_agenda"
    assert _cantidad(ctx, "turno") == 1


# --- 5.6 RBAC ---


def test_post_turnos_odontologo_responde_403_sin_permiso_y_no_escribe(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.reservar(ctx.cuerpo(), ctx.cabeceras_odontologo_a)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    _assert_sin_escrituras(ctx)


def test_post_turnos_sin_token_responde_401_no_autenticado(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.post("/turnos", json=ctx.cuerpo())

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
    _assert_sin_escrituras(ctx)


# --- 5.7 auditoría a nivel API ---

CLAVES_SNAPSHOT = [
    "id", "paciente_id", "profesional_id", "sillon_id",
    "prestacion_id", "inicio", "fin", "estado",
]  # fmt: skip


def _auditorias(ctx: ContextoTurnos) -> list[tuple]:  # type: ignore[type-arg]
    return _consultar(
        ctx,
        "SELECT turno_id, accion, usuario_id, ocurrio_en, antes, despues "
        "FROM auditoria_turno ORDER BY id",
    )


def test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos  # el reloj fijo marca 2026-01-05T12:00Z = 09:00 local

    creado = ctx.reservar(ctx.cuerpo()).json()

    turno_id, accion, usuario_id, ocurrio_en, antes, despues = _auditorias(ctx)[0]
    assert (turno_id, accion, usuario_id) == (creado["id"], "crear", ctx.recepcion.id)
    assert ocurrio_en == "2026-01-05T09:00:00"
    assert antes is None
    assert list(json.loads(despues)) == CLAVES_SNAPSHOT
    assert json.loads(despues) == creado
    assert _consultar(ctx, "SELECT creado_por, creado_en FROM turno") == [
        (ctx.recepcion.id, "2026-01-05T09:00:00")
    ]


def test_post_turnos_la_hora_local_cruza_de_dia_respecto_de_utc(
    contexto_turnos: ContextoTurnos,
    reloj: RelojFijo,
    token_de: Callable[[Usuario], str],
) -> None:
    ctx = contexto_turnos
    reloj.avanzar(minutes=14 * 60 + 30)  # 2026-01-06T02:30Z = 2026-01-05T23:30 local
    cabeceras = _headers(token_de(ctx.recepcion))  # el token anterior ya venció

    assert ctx.reservar(ctx.cuerpo(), cabeceras).status_code == 201

    assert _auditorias(ctx)[0][3] == "2026-01-05T23:30:00"
    assert _consultar(ctx, "SELECT creado_en FROM turno") == [("2026-01-05T23:30:00",)]


def test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    _reservar_base(ctx)

    assert ctx.reservar(ctx.cuerpo()).status_code == 409

    assert _cantidad(ctx, "turno") == 1
    assert _cantidad(ctx, "auditoria") == 1


# --- 6.1 GET /turnos/{id} ---


def test_get_turno_recepcion_existente_200(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    creado = ctx.reservar(ctx.cuerpo()).json()

    respuesta = ctx.cliente.get(f"/turnos/{creado['id']}", headers=ctx.cabeceras_recepcion)

    assert respuesta.status_code == 200
    assert respuesta.json() == creado


def test_get_turno_administracion_ve_el_turno_de_la_profesional_b_200(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    creado = ctx.reservar(ctx.cuerpo(profesional_id=ctx.profesional_b)).json()

    respuesta = ctx.cliente.get(f"/turnos/{creado['id']}", headers=ctx.cabeceras_admin)

    assert respuesta.status_code == 200
    assert respuesta.json()["profesional_id"] == ctx.profesional_b


def test_get_turno_inexistente_responde_404_no_encontrado(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/turnos/9999", headers=ctx.cabeceras_recepcion)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_get_turno_sin_token_responde_401_no_autenticado(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    creado = ctx.reservar(ctx.cuerpo()).json()

    respuesta = ctx.cliente.get(f"/turnos/{creado['id']}")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


# --- 6.2 RN-ACC-03 ---


def test_get_turno_odontologo_ve_su_propio_turno_200(contexto_turnos: ContextoTurnos) -> None:
    ctx = contexto_turnos
    creado = ctx.reservar(ctx.cuerpo()).json()  # profesional A

    respuesta = ctx.cliente.get(f"/turnos/{creado['id']}", headers=ctx.cabeceras_odontologo_a)

    assert respuesta.status_code == 200
    assert respuesta.json() == creado


def test_get_turno_odontologo_de_otro_profesional_responde_403_sin_datos_del_turno(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos
    creado = ctx.reservar(ctx.cuerpo(profesional_id=ctx.profesional_b)).json()

    respuesta = ctx.cliente.get(f"/turnos/{creado['id']}", headers=ctx.cabeceras_odontologo_a)

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    cuerpo = respuesta.text
    for dato in (creado["inicio"], creado["fin"], "paciente_id", "profesional_id", "reservado"):
        assert dato not in cuerpo


def test_get_turno_inexistente_responde_404_tambien_al_odontologo(
    contexto_turnos: ContextoTurnos,
) -> None:
    ctx = contexto_turnos

    respuesta = ctx.cliente.get("/turnos/9999", headers=ctx.cabeceras_odontologo_a)

    assert respuesta.status_code == 404  # 404 antes que 403 (design D7)


# --- 6.3 RN-AUD-02 a nivel API: sin rutas de escritura sobre turnos ni auditoría ---


@pytest.mark.parametrize("metodo", ["put", "patch", "delete"])
@pytest.mark.parametrize("ruta", ["/turnos/{id}", "/auditoria/turnos/{id}"])
def test_no_hay_rutas_para_modificar_o_borrar_turnos_ni_auditoria(
    contexto_turnos: ContextoTurnos, metodo: str, ruta: str
) -> None:
    ctx = contexto_turnos
    creado = ctx.reservar(ctx.cuerpo()).json()
    antes = _auditorias(ctx)

    respuesta = getattr(ctx.cliente, metodo)(
        ruta.format(id=creado["id"]), headers=ctx.cabeceras_admin
    )

    assert respuesta.status_code in (404, 405)
    assert _auditorias(ctx) == antes
    assert _cantidad(ctx, "turno") == 1
