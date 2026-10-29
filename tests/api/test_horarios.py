from collections.abc import Callable
from datetime import time
from typing import Any
import pytest
from fastapi.testclient import TestClient

from app.db.conexion import abrir_conexion, transaccion
from app.db.repositorio_profesionales import crear_profesional
from app.domain.usuarios import Rol, Usuario


@pytest.fixture
def profesional_id(cliente: TestClient) -> int:
    config = cliente.app.state.config
    conexion = abrir_conexion(config.database_path)
    with transaccion(conexion):
        prof = crear_profesional(conexion, nombre="Odontólogo", apellido="Uno")
    conexion.close()
    assert prof.id is not None
    return prof.id


@pytest.fixture
def otro_profesional_id(cliente: TestClient) -> int:
    config = cliente.app.state.config
    conexion = abrir_conexion(config.database_path)
    with transaccion(conexion):
        prof = crear_profesional(conexion, nombre="Odontólogo", apellido="Dos")
    conexion.close()
    assert prof.id is not None
    return prof.id


def _headers(token_de: Callable[[Usuario], str], usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_de(usuario)}"}


def test_post_horario_valido_responde_201(
    cliente: TestClient,
    profesional_id: int,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario(username="admin_h", rol=Rol.ADMINISTRACION)
    headers = _headers(token_de, admin)

    payload = {
        "dia_semana": 0,
        "hora_desde": "09:00",
        "hora_hasta": "13:00",
    }
    resp = cliente.post(f"/profesionales/{profesional_id}/horarios", json=payload, headers=headers)
    assert resp.status_code == 201
    datos = resp.json()
    assert datos["id"] is not None
    assert datos["profesional_id"] == profesional_id
    assert datos["dia_semana"] == 0
    assert datos["hora_desde"] == "09:00"
    assert datos["hora_hasta"] == "13:00"


def test_post_horario_con_profesional_inexistente_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario(username="admin_h2", rol=Rol.ADMINISTRACION)
    headers = _headers(token_de, admin)

    payload = {
        "dia_semana": 0,
        "hora_desde": "09:00",
        "hora_hasta": "13:00",
    }
    resp = cliente.post("/profesionales/9999/horarios", json=payload, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["codigo"] == "dato_invalido"


def test_post_horario_con_franja_invertida_responde_422(
    cliente: TestClient,
    profesional_id: int,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario(username="admin_h3", rol=Rol.ADMINISTRACION)
    headers = _headers(token_de, admin)

    payload = {
        "dia_semana": 0,
        "hora_desde": "14:00",
        "hora_hasta": "10:00",
    }
    resp = cliente.post(f"/profesionales/{profesional_id}/horarios", json=payload, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["codigo"] == "dato_invalido"


def test_post_horario_con_dia_invalido_responde_422(
    cliente: TestClient,
    profesional_id: int,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario(username="admin_h4", rol=Rol.ADMINISTRACION)
    headers = _headers(token_de, admin)

    payload = {
        "dia_semana": 8,
        "hora_desde": "09:00",
        "hora_hasta": "13:00",
    }
    resp = cliente.post(f"/profesionales/{profesional_id}/horarios", json=payload, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["codigo"] == "dato_invalido"


def test_post_horario_superpuesto_en_mismo_dia_responde_422(
    cliente: TestClient,
    profesional_id: int,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario(username="admin_h5", rol=Rol.ADMINISTRACION)
    headers = _headers(token_de, admin)

    f1 = {"dia_semana": 0, "hora_desde": "09:00", "hora_hasta": "13:00"}
    resp1 = cliente.post(f"/profesionales/{profesional_id}/horarios", json=f1, headers=headers)
    assert resp1.status_code == 201

    f2 = {"dia_semana": 0, "hora_desde": "12:00", "hora_hasta": "15:00"}
    resp2 = cliente.post(f"/profesionales/{profesional_id}/horarios", json=f2, headers=headers)
    assert resp2.status_code == 422
    assert resp2.json()["codigo"] == "dato_invalido"


def test_post_dos_horarios_disjuntos_en_mismo_dia_responde_201(
    cliente: TestClient,
    profesional_id: int,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario(username="admin_h6", rol=Rol.ADMINISTRACION)
    headers = _headers(token_de, admin)

    f1 = {"dia_semana": 0, "hora_desde": "09:00", "hora_hasta": "13:00"}
    f2 = {"dia_semana": 0, "hora_desde": "14:00", "hora_hasta": "18:00"}
    resp1 = cliente.post(f"/profesionales/{profesional_id}/horarios", json=f1, headers=headers)
    assert resp1.status_code == 201
    resp2 = cliente.post(f"/profesionales/{profesional_id}/horarios", json=f2, headers=headers)
    assert resp2.status_code == 201


def test_post_horarios_permisos(
    cliente: TestClient,
    profesional_id: int,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario(username="recep_h", rol=Rol.RECEPCION)
    odontologo = crear_usuario(username="odo_h", rol=Rol.ODONTOLOGO, profesional_id=profesional_id)

    payload = {"dia_semana": 1, "hora_desde": "09:00", "hora_hasta": "13:00"}

    # Sin token -> 401
    resp_anon = cliente.post(f"/profesionales/{profesional_id}/horarios", json=payload)
    assert resp_anon.status_code == 401

    # Recepción -> 403
    resp_recep = cliente.post(
        f"/profesionales/{profesional_id}/horarios", json=payload, headers=_headers(token_de, recepcion)
    )
    assert resp_recep.status_code == 403

    # Odontólogo -> 403
    resp_odo = cliente.post(
        f"/profesionales/{profesional_id}/horarios", json=payload, headers=_headers(token_de, odontologo)
    )
    assert resp_odo.status_code == 403


def test_get_horarios_consulta_y_permisos(
    cliente: TestClient,
    profesional_id: int,
    otro_profesional_id: int,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario(username="admin_h7", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario(username="recep_h2", rol=Rol.RECEPCION)
    odontologo = crear_usuario(
        username="odo_h2", rol=Rol.ODONTOLOGO, profesional_id=profesional_id
    )

    # Cargar horario
    payload = {"dia_semana": 2, "hora_desde": "08:00", "hora_hasta": "12:00"}
    resp_crear = cliente.post(
        f"/profesionales/{profesional_id}/horarios",
        json=payload,
        headers=_headers(token_de, admin),
    )
    assert resp_crear.status_code == 201

    # Sin token -> 401
    assert cliente.get(f"/profesionales/{profesional_id}/horarios").status_code == 401

    # Admin -> 200
    resp_admin = cliente.get(
        f"/profesionales/{profesional_id}/horarios", headers=_headers(token_de, admin)
    )
    assert resp_admin.status_code == 200
    assert len(resp_admin.json()) == 1

    # Recepción -> 200
    resp_recep = cliente.get(
        f"/profesionales/{profesional_id}/horarios", headers=_headers(token_de, recepcion)
    )
    assert resp_recep.status_code == 200
    assert len(resp_recep.json()) == 1

    # Odontólogo consulta sus propios horarios -> 200
    resp_odo_propio = cliente.get(
        f"/profesionales/{profesional_id}/horarios", headers=_headers(token_de, odontologo)
    )
    assert resp_odo_propio.status_code == 200
    assert len(resp_odo_propio.json()) == 1

    # Odontólogo consulta horarios de otro profesional -> 403
    resp_odo_ajeno = cliente.get(
        f"/profesionales/{otro_profesional_id}/horarios", headers=_headers(token_de, odontologo)
    )
    assert resp_odo_ajeno.status_code == 403

    # Profesional inexistente -> 404
    resp_404 = cliente.get(
        "/profesionales/9999/horarios", headers=_headers(token_de, admin)
    )
    assert resp_404.status_code == 404
