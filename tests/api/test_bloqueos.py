"""Tests de API para bloqueos horarios y permisos RBAC (C-09, US-005, RN-REC-02, RN-ACC-01/02)."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

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
    assert listado.json() == [bloqueo]


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
