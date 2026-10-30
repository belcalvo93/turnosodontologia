"""Tests de API para bloqueos horarios y permisos RBAC (C-09, US-005, RN-REC-02, RN-ACC-01/02)."""

from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.db.conexion import abrir_conexion, transaccion
from app.db.repositorio_horarios import crear_horario
from app.db.repositorio_pacientes import crear_paciente
from app.db.repositorio_prestaciones import crear_prestacion
from app.db.repositorio_profesionales import crear_profesional
from app.db.repositorio_sillones import crear_sillon
from app.domain.models import HorarioAtencion
from app.domain.usuarios import Rol, Usuario


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_post_bloqueos_para_profesional_y_sillon_responde_201(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    profesional = cliente.post(
        "/profesionales",
        json={"nombre": "Odontólogo", "apellido": "Ficticio A"},
        headers=cabeceras,
    ).json()
    sillon = cliente.post(
        "/sillones",
        json={"nombre": "Sillón 1"},
        headers=cabeceras,
    ).json()

    resp_prof = cliente.post(
        "/bloqueos",
        json={
            "alcance": "profesional",
            "recurso_id": profesional["id"],
            "inicio": "2026-11-10T09:00:00",
            "fin": "2026-11-10T13:00:00",
            "motivo": "  Vacaciones  ",
        },
        headers=cabeceras,
    )
    assert resp_prof.status_code == 201
    assert resp_prof.json() == {
        "id": 1,
        "alcance": "profesional",
        "recurso_id": profesional["id"],
        "inicio": "2026-11-10T09:00:00",
        "fin": "2026-11-10T13:00:00",
        "motivo": "Vacaciones",
        "turnos_afectados": [],
    }

    resp_sillon = cliente.post(
        "/bloqueos",
        json={
            "alcance": "sillon",
            "recurso_id": sillon["id"],
            "inicio": "2026-11-11T14:00:00",
            "fin": "2026-11-11T16:00:00",
            "motivo": "Mantenimiento",
        },
        headers=cabeceras,
    )
    assert resp_sillon.status_code == 201
    assert resp_sillon.json()["alcance"] == "sillon"


@pytest.mark.parametrize(
    ("inicio", "fin"),
    [
        ("2026-11-10T10:00:00", "2026-11-10T10:00:00"),
        ("2026-11-10T12:00:00", "2026-11-10T10:00:00"),
    ],
)
def test_post_bloqueos_con_inicio_mayor_o_igual_que_fin_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    inicio: str,
    fin: str,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    profesional = cliente.post(
        "/profesionales",
        json={"nombre": "Odontólogo", "apellido": "Ficticio A"},
        headers=cabeceras,
    ).json()

    respuesta = cliente.post(
        "/bloqueos",
        json={
            "alcance": "profesional",
            "recurso_id": profesional["id"],
            "inicio": inicio,
            "fin": fin,
            "motivo": "Feriado",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/bloqueos", headers=cabeceras).json() == []


@pytest.mark.parametrize("alcance", ["profesional", "sillon"])
def test_post_bloqueos_con_recurso_inexistente_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    alcance: str,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post(
        "/bloqueos",
        json={
            "alcance": alcance,
            "recurso_id": 9999,
            "inicio": "2026-11-10T09:00:00",
            "fin": "2026-11-10T13:00:00",
            "motivo": "Vacaciones",
        },
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_delete_bloqueo_elimina_registro_y_404_si_no_existe(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    profesional = cliente.post(
        "/profesionales",
        json={"nombre": "Odontólogo", "apellido": "Ficticio A"},
        headers=cabeceras,
    ).json()
    bloqueo = cliente.post(
        "/bloqueos",
        json={
            "alcance": "profesional",
            "recurso_id": profesional["id"],
            "inicio": "2026-11-10T09:00:00",
            "fin": "2026-11-10T13:00:00",
            "motivo": "Vacaciones",
        },
        headers=cabeceras,
    ).json()

    eliminado = cliente.delete(f"/bloqueos/{bloqueo['id']}", headers=cabeceras)
    assert eliminado.status_code in (200, 204)
    assert cliente.get("/bloqueos", headers=cabeceras).json() == []

    inexistente = cliente.delete("/bloqueos/9999", headers=cabeceras)
    assert inexistente.status_code == 404
    assert inexistente.json()["codigo"] == "no_encontrado"


@pytest.mark.parametrize("rol_sin_escritura", [Rol.RECEPCION, Rol.ODONTOLOGO])
def test_recepcion_y_odontologo_reciben_403_al_crear_o_eliminar_y_200_al_listar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    rol_sin_escritura: Rol,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras_admin = _headers(token_de(admin))
    profesional = cliente.post(
        "/profesionales",
        json={"nombre": "Odontólogo", "apellido": "Ficticio A"},
        headers=cabeceras_admin,
    ).json()
    bloqueo = cliente.post(
        "/bloqueos",
        json={
            "alcance": "profesional",
            "recurso_id": profesional["id"],
            "inicio": "2026-11-10T09:00:00",
            "fin": "2026-11-10T13:00:00",
            "motivo": "Vacaciones",
        },
        headers=cabeceras_admin,
    ).json()

    usuario_lectura = crear_usuario("usuario_lectura_ficticio", rol=rol_sin_escritura)
    cabeceras_lectura = _headers(token_de(usuario_lectura))

    intento_alta = cliente.post(
        "/bloqueos",
        json={
            "alcance": "profesional",
            "recurso_id": profesional["id"],
            "inicio": "2026-11-12T09:00:00",
            "fin": "2026-11-12T13:00:00",
            "motivo": "Otro",
        },
        headers=cabeceras_lectura,
    )
    assert intento_alta.status_code == 403
    assert intento_alta.json()["codigo"] == "sin_permiso"

    intento_borrado = cliente.delete(
        f"/bloqueos/{bloqueo['id']}", headers=cabeceras_lectura
    )
    assert intento_borrado.status_code == 403
    assert intento_borrado.json()["codigo"] == "sin_permiso"

    listado = cliente.get("/bloqueos", headers=cabeceras_lectura)
    assert listado.status_code == 200
    assert listado.json() == [
        {k: v for k, v in bloqueo.items() if k != "turnos_afectados"}
    ]


def test_rutas_bloqueos_sin_token_responden_401(cliente: TestClient) -> None:
    assert cliente.get("/bloqueos").status_code == 401
    assert (
        cliente.post(
            "/bloqueos",
            json={
                "alcance": "profesional",
                "recurso_id": 1,
                "inicio": "2026-11-10T09:00:00",
                "fin": "2026-11-10T13:00:00",
                "motivo": "Vacaciones",
            },
        ).status_code
        == 401
    )
    assert cliente.delete("/bloqueos/1").status_code == 401


# --- C-16 turnos_afectados en POST /bloqueos (D-A1, D-A2, D-A3) ---

LUNES = "2026-01-12"  # un lunes con horario de atención 09:00–13:00


@dataclass
class ContextoBloqueos:
    """Ids y cabeceras de un consultorio ficticio con agenda lista para bloquear."""

    cliente: TestClient
    config: Config
    profesional_a: int
    profesional_b: int
    sillon_1: int
    sillon_2: int
    consulta: int
    paciente_1: int
    paciente_2: int
    cabeceras_recepcion: dict[str, str]
    cabeceras_admin: dict[str, str]

    def reservar(
        self,
        inicio: str,
        *,
        paciente_id: int | None = None,
        profesional_id: int | None = None,
        sillon_id: int | None = None,
    ) -> int:
        """Reserva un turno por API con la prestación ficticia de 30 minutos y devuelve su id."""
        respuesta = self.cliente.post(
            "/turnos",
            json={
                "paciente_id": paciente_id or self.paciente_1,
                "profesional_id": profesional_id or self.profesional_a,
                "sillon_id": sillon_id or self.sillon_1,
                "prestacion_id": self.consulta,
                "inicio": inicio,
            },
            headers=self.cabeceras_recepcion,
        )
        assert respuesta.status_code == 201, respuesta.json()
        return respuesta.json()["id"]

    def cancelar(self, turno_id: int) -> None:
        respuesta = self.cliente.post(
            f"/turnos/{turno_id}/cancelar", headers=self.cabeceras_recepcion
        )
        assert respuesta.status_code == 200, respuesta.json()

    def get_turno(self, turno_id: int) -> dict[str, object]:
        respuesta = self.cliente.get(f"/turnos/{turno_id}", headers=self.cabeceras_recepcion)
        assert respuesta.status_code == 200
        return respuesta.json()

    def crear_bloqueo(self, alcance: str, recurso_id: int, inicio: str, fin: str) -> httpx.Response:
        return self.cliente.post(
            "/bloqueos",
            json={
                "alcance": alcance,
                "recurso_id": recurso_id,
                "inicio": inicio,
                "fin": fin,
                "motivo": "Urgencia ficticia",
            },
            headers=self.cabeceras_admin,
        )


@pytest.fixture
def contexto_bloqueos(
    cliente: TestClient,
    config: Config,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> ContextoBloqueos:
    """Consultorio ficticio: dos profesionales con horario lunes 09:00–13:00, dos sillones."""
    with closing(abrir_conexion(config.database_path)) as con:
        with transaccion(con):
            prof_a = crear_profesional(con, nombre="Odontólogo", apellido="Ficticio A")
            prof_b = crear_profesional(con, nombre="Odontóloga", apellido="Ficticia B")
            for profesional_id in (prof_a.id, prof_b.id):  # type: ignore[arg-type]
                crear_horario(
                    con,
                    HorarioAtencion(
                        profesional_id=profesional_id,
                        dia_semana=0,
                        hora_desde=time(9, 0),
                        hora_hasta=time(13, 0),
                    ),
                )
            sillon_1 = crear_sillon(con, nombre="Sillón 1 (ficticio)")
            sillon_2 = crear_sillon(con, nombre="Sillón 2 (ficticio)")
            consulta = crear_prestacion(con, nombre="Consulta ficticia", duracion_minutos=30)
            pac_1 = crear_paciente(
                con, nombre="Paciente", apellido="Ficticio 1", dni="00000001 (ficticio)"
            )
            pac_2 = crear_paciente(
                con, nombre="Paciente", apellido="Ficticio 2", dni="00000002 (ficticio)"
            )
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    return ContextoBloqueos(
        cliente=cliente,
        config=config,
        profesional_a=prof_a.id,  # type: ignore[arg-type]
        profesional_b=prof_b.id,  # type: ignore[arg-type]
        sillon_1=sillon_1.id,  # type: ignore[arg-type]
        sillon_2=sillon_2.id,  # type: ignore[arg-type]
        consulta=consulta.id,  # type: ignore[arg-type]
        paciente_1=pac_1.id,  # type: ignore[arg-type]
        paciente_2=pac_2.id,  # type: ignore[arg-type]
        cabeceras_recepcion=_headers(token_de(recepcion)),
        cabeceras_admin=_headers(token_de(admin)),
    )


def _auditorias(config: Config) -> int:
    with closing(abrir_conexion(config.database_path)) as con:
        return int(con.execute("SELECT COUNT(*) FROM auditoria_turno").fetchone()[0])


def test_post_bloqueos_profesional_lista_los_reservados_en_rango_ordenados_sin_auditoria(
    contexto_bloqueos: ContextoBloqueos,
) -> None:
    contexto = contexto_bloqueos
    parcial = contexto.reservar(f"{LUNES}T09:15:00", paciente_id=contexto.paciente_1)  # 09:15–09:45
    interno = contexto.reservar(f"{LUNES}T09:45:00", paciente_id=contexto.paciente_2)  # 09:45–10:15
    a_cancelar = contexto.reservar(f"{LUNES}T10:15:00")  # 10:15–10:45, queda cancelado
    contexto.cancelar(a_cancelar)
    auditorias_antes = _auditorias(contexto.config)

    respuesta = contexto.crear_bloqueo(
        "profesional", contexto.profesional_a, f"{LUNES}T09:30:00", f"{LUNES}T10:30:00"
    )

    assert respuesta.status_code == 201, respuesta.json()
    # D-A2: contrato plano, con `turnos_afectados` en la raíz (solo los 2 reservado,
    # ordenados por inicio ASC, sin el cancelado).
    assert respuesta.json() == {
        "id": 1,
        "alcance": "profesional",
        "recurso_id": contexto.profesional_a,
        "inicio": "2026-01-12T09:30:00",
        "fin": "2026-01-12T10:30:00",
        "motivo": "Urgencia ficticia",
        "turnos_afectados": [
            {
                "id": parcial,
                "paciente_id": contexto.paciente_1,
                "profesional_id": contexto.profesional_a,
                "sillon_id": contexto.sillon_1,
                "prestacion_id": contexto.consulta,
                "inicio": "2026-01-12T09:15:00",
                "fin": "2026-01-12T09:45:00",
                "estado": "reservado",
            },
            {
                "id": interno,
                "paciente_id": contexto.paciente_2,
                "profesional_id": contexto.profesional_a,
                "sillon_id": contexto.sillon_1,
                "prestacion_id": contexto.consulta,
                "inicio": "2026-01-12T09:45:00",
                "fin": "2026-01-12T10:15:00",
                "estado": "reservado",
            },
        ],
    }
    # El bloqueo no escribe auditoría (IF-06, D-A1) y no toca los turnos reportados (D-A1).
    assert _auditorias(contexto.config) == auditorias_antes
    assert contexto.get_turno(parcial)["estado"] == "reservado"
    assert contexto.get_turno(interno)["estado"] == "reservado"


def test_post_bloqueos_profesional_con_intervalo_vacio_responde_turnos_afectados_vacio(
    contexto_bloqueos: ContextoBloqueos,
) -> None:
    contexto = contexto_bloqueos

    respuesta = contexto.crear_bloqueo(
        "profesional", contexto.profesional_a, f"{LUNES}T11:00:00", f"{LUNES}T13:00:00"
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["turnos_afectados"] == []


def test_post_bloqueos_sillon_lista_solo_los_turnos_de_ese_sillon(
    contexto_bloqueos: ContextoBloqueos,
) -> None:
    contexto = contexto_bloqueos
    del_sillon_1 = contexto.reservar(f"{LUNES}T10:00:00")  # 10:00–10:30, prof A, sillón 1
    del_sillon_2 = contexto.reservar(
        f"{LUNES}T09:30:00",
        profesional_id=contexto.profesional_b,
        sillon_id=contexto.sillon_2,
        paciente_id=contexto.paciente_2,
    )  # 09:30–10:00 en otro sillón

    respuesta = contexto.crear_bloqueo(
        "sillon", contexto.sillon_1, f"{LUNES}T09:30:00", f"{LUNES}T10:30:00"
    )

    assert respuesta.status_code == 201
    afectados = respuesta.json()["turnos_afectados"]
    assert afectados == [
        {
            "id": del_sillon_1,
            "paciente_id": contexto.paciente_1,
            "profesional_id": contexto.profesional_a,
            "sillon_id": contexto.sillon_1,
            "prestacion_id": contexto.consulta,
            "inicio": "2026-01-12T10:00:00",
            "fin": "2026-01-12T10:30:00",
            "estado": "reservado",
        }
    ]
    assert del_sillon_2 not in [turno["id"] for turno in afectados]


def test_get_bloqueos_no_incluye_turnos_afectados(contexto_bloqueos: ContextoBloqueos) -> None:
    contexto = contexto_bloqueos
    contexto.reservar(f"{LUNES}T10:00:00")  # un turno en rango para que el reporte exista
    creada = contexto.crear_bloqueo(
        "profesional", contexto.profesional_a, f"{LUNES}T09:30:00", f"{LUNES}T10:30:00"
    )
    assert creada.status_code == 201

    listado = contexto.cliente.get("/bloqueos", headers=contexto.cabeceras_admin).json()

    assert len(listado) == 1
    assert set(listado[0]) == {"id", "alcance", "recurso_id", "inicio", "fin", "motivo"}
