"""Tests de API para profesionales y permisos RBAC (C-04, US-001, RN-REC-03, RN-ACC-01/02)."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.domain.usuarios import Rol, Usuario


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_post_profesionales_alta_valida_con_matricula_responde_201(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.post(
        "/profesionales",
        json={
            "nombre": "  Odontólogo  ",
            "apellido": "  Ficticio A  ",
            "matricula": "  0001 (ficticia)  ",
        },
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 1,
        "nombre": "Odontólogo",
        "apellido": "Ficticio A",
        "matricula": "0001 (ficticia)",
        "activo": True,
    }


def test_post_profesionales_alta_valida_sin_matricula_responde_201(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.post(
        "/profesionales",
        json={"nombre": "Odontóloga", "apellido": "Ficticia B"},
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 1,
        "nombre": "Odontóloga",
        "apellido": "Ficticia B",
        "matricula": None,
        "activo": True,
    }


@pytest.mark.parametrize(
    "payload_invalido",
    [
        {"nombre": "", "apellido": "Ficticio A"},
        {"nombre": "   ", "apellido": "Ficticio A"},
        {"nombre": "Odontólogo", "apellido": ""},
        {"nombre": "Odontólogo", "apellido": "   "},
    ],
)
def test_post_profesionales_con_nombre_o_apellido_vacio_responde_422_y_no_persiste(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    payload_invalido: dict[str, str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post("/profesionales", json=payload_invalido, headers=cabeceras)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    listado = cliente.get("/profesionales", headers=cabeceras)
    assert listado.status_code == 200
    assert listado.json() == []


def test_patch_profesionales_desactivado_sigue_listandose_como_inactivo(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    primero = cliente.post(
        "/profesionales",
        json={
            "nombre": "Odontólogo",
            "apellido": "Ficticio A",
            "matricula": "0001 (ficticia)",
        },
        headers=cabeceras,
    ).json()
    segundo = cliente.post(
        "/profesionales",
        json={"nombre": "Odontóloga", "apellido": "Ficticia B"},
        headers=cabeceras,
    ).json()

    respuesta_baja = cliente.patch(
        f"/profesionales/{segundo['id']}",
        json={"activo": False},
        headers=cabeceras,
    )

    assert respuesta_baja.status_code == 200
    assert respuesta_baja.json() == {
        "id": segundo["id"],
        "nombre": "Odontóloga",
        "apellido": "Ficticia B",
        "matricula": None,
        "activo": False,
    }

    listado = cliente.get("/profesionales", headers=cabeceras)
    assert listado.status_code == 200
    assert listado.json() == [
        primero,
        {
            "id": segundo["id"],
            "nombre": "Odontóloga",
            "apellido": "Ficticia B",
            "matricula": None,
            "activo": False,
        },
    ]


def test_patch_profesionales_edita_datos_parcialmente_y_valida_vacios(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creado = cliente.post(
        "/profesionales",
        json={
            "nombre": "Juan",
            "apellido": "Pérez",
            "matricula": "0001 (ficticia)",
        },
        headers=cabeceras,
    ).json()

    editado = cliente.patch(
        f"/profesionales/{creado['id']}",
        json={"nombre": "Juan Carlos", "matricula": None},
        headers=cabeceras,
    )
    assert editado.status_code == 200
    assert editado.json() == {
        "id": creado["id"],
        "nombre": "Juan Carlos",
        "apellido": "Pérez",
        "matricula": None,
        "activo": True,
    }

    invalido = cliente.patch(
        f"/profesionales/{creado['id']}",
        json={"nombre": "   "},
        headers=cabeceras,
    )
    assert invalido.status_code == 422
    assert invalido.json()["codigo"] == "dato_invalido"


def test_patch_profesionales_inexistente_responde_404(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.patch(
        "/profesionales/9999",
        json={"activo": False},
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


@pytest.mark.parametrize("rol_sin_escritura", [Rol.RECEPCION, Rol.ODONTOLOGO])
def test_recepcion_y_odontologo_reciben_403_al_crear_o_editar_y_200_al_listar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    rol_sin_escritura: Rol,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    creado = cliente.post(
        "/profesionales",
        json={"nombre": "Odontólogo", "apellido": "Ficticio A"},
        headers=_headers(token_de(admin)),
    ).json()

    usuario_lectura = crear_usuario("usuario_lectura_ficticio", rol=rol_sin_escritura)
    cabeceras_lectura = _headers(token_de(usuario_lectura))

    intento_alta = cliente.post(
        "/profesionales",
        json={"nombre": "Otro", "apellido": "Ficticio"},
        headers=cabeceras_lectura,
    )
    assert intento_alta.status_code == 403
    assert intento_alta.json()["codigo"] == "sin_permiso"

    intento_edicion = cliente.patch(
        f"/profesionales/{creado['id']}",
        json={"activo": False},
        headers=cabeceras_lectura,
    )
    assert intento_edicion.status_code == 403
    assert intento_edicion.json()["codigo"] == "sin_permiso"

    lectura = cliente.get("/profesionales", headers=cabeceras_lectura)
    assert lectura.status_code == 200
    assert lectura.json() == [creado]


def test_rutas_profesionales_sin_token_responden_401(cliente: TestClient) -> None:
    assert cliente.get("/profesionales").status_code == 401
    assert (
        cliente.post(
            "/profesionales", json={"nombre": "Juan", "apellido": "Pérez"}
        ).status_code
        == 401
    )
    assert (
        cliente.patch("/profesionales/1", json={"activo": False}).status_code == 401
    )
    assert cliente.get("/profesionales").json()["codigo"] == "no_autenticado"
