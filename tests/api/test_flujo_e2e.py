"""Test de aceptación extremo a extremo del flujo de 6 pasos con el seed demo (C-17)."""

from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Config, cargar_config
from app.db.conexion import abrir_conexion
from app.main import create_app
from tests.conftest import RelojFijo

# El reloj fijo arranca en 2026-01-05 12:00 UTC = lunes 2026-01-05 09:00 en Buenos Aires.
LUNES_DEMO = "2026-01-05"


@dataclass(frozen=True)
class IdsDemo:
    """Identificadores del catálogo demo leídos directamente de la base sembrada."""

    profesional_a: int
    profesional_b: int
    sillon_1: int
    sillon_2: int
    consulta: int
    limpieza: int
    tratamiento: int
    paciente_1: int
    paciente_2: int


@dataclass(frozen=True)
class ContextoE2E:
    """Cliente HTTP y configuración de desarrollo para el flujo extremo a extremo."""

    cliente: TestClient
    config: Config

    def login(self, username: str, password: str | None):  # type: ignore[no-untyped-def]
        assert password is not None
        return self.cliente.post(
            "/auth/login",
            json={"username": username, "password": password},
        )

    def leer_ids_demo(self) -> IdsDemo:
        with closing(abrir_conexion(self.config.database_path)) as conexion:
            profesionales = dict(
                conexion.execute("SELECT apellido, id FROM profesional").fetchall()
            )
            sillones = dict(conexion.execute("SELECT nombre, id FROM sillon").fetchall())
            prestaciones = dict(
                conexion.execute("SELECT nombre, id FROM prestacion").fetchall()
            )
            pacientes = dict(conexion.execute("SELECT dni, id FROM paciente").fetchall())
        return IdsDemo(
            profesional_a=int(profesionales["Ficticio A"]),
            profesional_b=int(profesionales["Ficticia B"]),
            sillon_1=int(sillones["Sillón 1"]),
            sillon_2=int(sillones["Sillón 2"]),
            consulta=int(prestaciones["Consulta ficticia"]),
            limpieza=int(prestaciones["Limpieza ficticia"]),
            tratamiento=int(prestaciones["Tratamiento ficticio"]),
            paciente_1=int(pacientes["00000001 (ficticio)"]),
            paciente_2=int(pacientes["00000002 (ficticio)"]),
        )


def _cabeceras(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def contexto_e2e(tmp_path: Path, reloj: RelojFijo) -> Iterator[ContextoE2E]:
    """Arranca `create_app` en development con las tres contraseñas demo y reloj fijo."""
    entorno = {
        "APP_ENV": "development",
        "DATABASE_URL": str(tmp_path / "e2e_demo.db"),
        "CLINIC_TIMEZONE": "America/Argentina/Buenos_Aires",
        "SEED_ADMIN_PASSWORD": "clave-admin-demo-ficticia",
        "SEED_RECEPCION_PASSWORD": "clave-recepcion-demo-ficticia",
        "SEED_ODONTOLOGO_PASSWORD": "clave-odontologo-demo-ficticia",
    }
    config = cargar_config(entorno=entorno)
    with TestClient(create_app(config, reloj=reloj)) as cliente_http:
        yield ContextoE2E(cliente=cliente_http, config=config)


def test_flujo_e2e_seis_pasos_login_alta_reprogramar_cancelar_y_auditoria(
    contexto_e2e: ContextoE2E,
) -> None:
    # Paso 1: login recepción
    login_recepcion = contexto_e2e.login(
        "recepcion_demo", contexto_e2e.config.seed_recepcion_password
    )
    assert login_recepcion.status_code == 200
    cabeceras_recepcion = _cabeceras(login_recepcion.json()["access_token"])

    ids = contexto_e2e.leer_ids_demo()

    # Paso 2: crear turno (lunes 10:00, consulta de 30 minutos -> fin 10:30)
    alta = contexto_e2e.cliente.post(
        "/turnos",
        json={
            "paciente_id": ids.paciente_1,
            "profesional_id": ids.profesional_a,
            "sillon_id": ids.sillon_1,
            "prestacion_id": ids.consulta,
            "inicio": f"{LUNES_DEMO}T10:00:00",
        },
        headers=cabeceras_recepcion,
    )
    assert alta.status_code == 201
    turno_creado = alta.json()
    turno_id = turno_creado["id"]
    assert turno_creado == {
        "id": turno_id,
        "paciente_id": ids.paciente_1,
        "profesional_id": ids.profesional_a,
        "sillon_id": ids.sillon_1,
        "prestacion_id": ids.consulta,
        "inicio": f"{LUNES_DEMO}T10:00:00",
        "fin": f"{LUNES_DEMO}T10:30:00",
        "estado": "reservado",
    }

    # Paso 3: reprogramar a las 11:00 del mismo día
    reprogramacion = contexto_e2e.cliente.post(
        f"/turnos/{turno_id}/reprogramar",
        json={"nuevo_inicio": f"{LUNES_DEMO}T11:00:00"},
        headers=cabeceras_recepcion,
    )
    assert reprogramacion.status_code == 200
    assert reprogramacion.json() == {
        **turno_creado,
        "inicio": f"{LUNES_DEMO}T11:00:00",
        "fin": f"{LUNES_DEMO}T11:30:00",
    }

    # Paso 4: cancelar el turno
    cancelacion = contexto_e2e.cliente.post(
        f"/turnos/{turno_id}/cancelar",
        headers=cabeceras_recepcion,
    )
    assert cancelacion.status_code == 200
    assert cancelacion.json() == {
        **reprogramacion.json(),
        "estado": "cancelado",
    }

    # Paso 5: login administración
    login_admin = contexto_e2e.login("admin_demo", contexto_e2e.config.seed_admin_password)
    assert login_admin.status_code == 200
    cabeceras_admin = _cabeceras(login_admin.json()["access_token"])

    # Paso 6: consultar auditoría del turno
    auditoria = contexto_e2e.cliente.get(
        f"/auditoria?turno_id={turno_id}",
        headers=cabeceras_admin,
    )
    assert auditoria.status_code == 200
    cuerpo_auditoria = auditoria.json()
    assert cuerpo_auditoria["turno_id"] == turno_id
    registros = cuerpo_auditoria["registros"]
    assert [r["accion"] for r in registros] == ["crear", "reprogramar", "cancelar"]
    assert [r["username"] for r in registros] == [
        "recepcion_demo",
        "recepcion_demo",
        "recepcion_demo",
    ]
    assert registros[0]["antes"] is None
    assert registros[0]["despues"]["inicio"] == f"{LUNES_DEMO}T10:00:00"
    assert registros[1]["antes"]["inicio"] == f"{LUNES_DEMO}T10:00:00"
    assert registros[1]["despues"]["inicio"] == f"{LUNES_DEMO}T11:00:00"
    assert registros[2]["antes"]["estado"] == "reservado"
    assert registros[2]["despues"]["estado"] == "cancelado"


def test_flujo_e2e_hueco_liberado_por_cancelacion_se_puede_volver_a_reservar(
    contexto_e2e: ContextoE2E,
) -> None:
    login_recepcion = contexto_e2e.login(
        "recepcion_demo", contexto_e2e.config.seed_recepcion_password
    )
    assert login_recepcion.status_code == 200
    cabeceras_recepcion = _cabeceras(login_recepcion.json()["access_token"])
    ids = contexto_e2e.leer_ids_demo()

    cuerpo = {
        "paciente_id": ids.paciente_1,
        "profesional_id": ids.profesional_a,
        "sillon_id": ids.sillon_1,
        "prestacion_id": ids.consulta,
        "inicio": f"{LUNES_DEMO}T10:00:00",
    }
    primero = contexto_e2e.cliente.post("/turnos", json=cuerpo, headers=cabeceras_recepcion)
    assert primero.status_code == 201
    primero_id = primero.json()["id"]

    cancelacion = contexto_e2e.cliente.post(
        f"/turnos/{primero_id}/cancelar", headers=cabeceras_recepcion
    )
    assert cancelacion.status_code == 200

    segundo = contexto_e2e.cliente.post(
        "/turnos",
        json={**cuerpo, "paciente_id": ids.paciente_2},
        headers=cabeceras_recepcion,
    )
    assert segundo.status_code == 201
    assert segundo.json()["estado"] == "reservado"
    assert segundo.json()["inicio"] == f"{LUNES_DEMO}T10:00:00"
    assert segundo.json()["profesional_id"] == ids.profesional_a
    assert segundo.json()["sillon_id"] == ids.sillon_1


def test_flujo_e2e_reprogramacion_rechazada_con_409_no_agrega_auditoria(
    contexto_e2e: ContextoE2E,
) -> None:
    login_recepcion = contexto_e2e.login(
        "recepcion_demo", contexto_e2e.config.seed_recepcion_password
    )
    assert login_recepcion.status_code == 200
    cabeceras_recepcion = _cabeceras(login_recepcion.json()["access_token"])
    ids = contexto_e2e.leer_ids_demo()

    turno_1 = contexto_e2e.cliente.post(
        "/turnos",
        json={
            "paciente_id": ids.paciente_1,
            "profesional_id": ids.profesional_a,
            "sillon_id": ids.sillon_1,
            "prestacion_id": ids.consulta,
            "inicio": f"{LUNES_DEMO}T10:00:00",
        },
        headers=cabeceras_recepcion,
    )
    assert turno_1.status_code == 201
    turno_1_id = turno_1.json()["id"]

    turno_2 = contexto_e2e.cliente.post(
        "/turnos",
        json={
            "paciente_id": ids.paciente_2,
            "profesional_id": ids.profesional_a,
            "sillon_id": ids.sillon_1,
            "prestacion_id": ids.consulta,
            "inicio": f"{LUNES_DEMO}T11:00:00",
        },
        headers=cabeceras_recepcion,
    )
    assert turno_2.status_code == 201

    rechazo = contexto_e2e.cliente.post(
        f"/turnos/{turno_1_id}/reprogramar",
        json={"nuevo_inicio": f"{LUNES_DEMO}T11:00:00"},
        headers=cabeceras_recepcion,
    )
    assert rechazo.status_code == 409
    assert rechazo.json()["codigo"] == "conflicto_agenda"

    login_admin = contexto_e2e.login("admin_demo", contexto_e2e.config.seed_admin_password)
    assert login_admin.status_code == 200
    cabeceras_admin = _cabeceras(login_admin.json()["access_token"])

    auditoria = contexto_e2e.cliente.get(
        f"/auditoria?turno_id={turno_1_id}",
        headers=cabeceras_admin,
    )
    assert auditoria.status_code == 200
    registros = auditoria.json()["registros"]
    assert [r["accion"] for r in registros] == ["crear"]
