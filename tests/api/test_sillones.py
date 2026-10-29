"""Tests de API para sillones y permisos RBAC (C-05, US-002, RN-REC-01, RN-REC-03)."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.domain.usuarios import Rol, Usuario


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _crear_sillon(
    cliente: TestClient,
    cabeceras: dict[str, str],
    nombre: str = "Sillón 1 (ficticio)",
) -> dict[str, object]:
    return cliente.post("/sillones", json={"nombre": nombre}, headers=cabeceras).json()


def test_post_sillones_alta_valida_normaliza_el_nombre(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.post(
        "/sillones",
        json={"nombre": "  Sillón 1 (ficticio)  "},
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 1,
        "nombre": "Sillón 1 (ficticio)",
        "activo": True,
    }


def test_post_sillones_con_nombre_duplicado_responde_409(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    _crear_sillon(cliente, cabeceras)

    respuesta = cliente.post(
        "/sillones",
        json={"nombre": "Sillón 1 (ficticio)"},
        headers=cabeceras,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "nombre_duplicado"
    assert len(cliente.get("/sillones", headers=cabeceras).json()) == 1


def test_post_sillones_con_nombre_vacio_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post("/sillones", json={"nombre": ""}, headers=cabeceras)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/sillones", headers=cabeceras).json() == []


def test_post_sillones_con_nombre_solo_espacios_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post("/sillones", json={"nombre": "   "}, headers=cabeceras)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/sillones", headers=cabeceras).json() == []


def test_patch_sillones_desactiva_y_el_sillon_sigue_en_el_listado(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creado = _crear_sillon(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/sillones/{creado['id']}", json={"activo": False}, headers=cabeceras
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": creado["id"],
        "nombre": "Sillón 1 (ficticio)",
        "activo": False,
    }
    assert cliente.get("/sillones", headers=cabeceras).json() == [respuesta.json()]


def test_patch_sillones_renombra_el_sillon(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creado = _crear_sillon(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/sillones/{creado['id']}",
        json={"nombre": "  Box 2 (ficticio)  "},
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": creado["id"],
        "nombre": "Box 2 (ficticio)",
        "activo": True,
    }


def test_patch_sillones_a_nombre_existente_responde_409(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    _crear_sillon(cliente, cabeceras, "Sillón 1 (ficticio)")
    segundo = _crear_sillon(cliente, cabeceras, "Sillón 2 (ficticio)")

    respuesta = cliente.patch(
        f"/sillones/{segundo['id']}",
        json={"nombre": "Sillón 1 (ficticio)"},
        headers=cabeceras,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "nombre_duplicado"
    assert cliente.get("/sillones", headers=cabeceras).json()[1] == segundo


def test_patch_sillones_con_nombre_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creado = _crear_sillon(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/sillones/{creado['id']}", json={"nombre": None}, headers=cabeceras
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/sillones", headers=cabeceras).json() == [creado]


def test_patch_sillones_con_nombre_solo_espacios_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creado = _crear_sillon(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/sillones/{creado['id']}", json={"nombre": "   "}, headers=cabeceras
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/sillones", headers=cabeceras).json() == [creado]


def test_patch_sillones_con_activo_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creado = _crear_sillon(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/sillones/{creado['id']}", json={"activo": None}, headers=cabeceras
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/sillones", headers=cabeceras).json() == [creado]


def test_patch_sillones_inexistente_responde_404(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.patch(
        "/sillones/9999",
        json={"activo": False},
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "no_encontrado"
    assert isinstance(cuerpo["mensaje"], str)
    assert cuerpo["mensaje"].strip() != ""


def test_recepcion_post_sillones_recibe_403(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/sillones", json={"nombre": "Sillón 1 (ficticio)"}, headers=cabeceras
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert cliente.get("/sillones", headers=cabeceras).json() == []


def test_odontologo_patch_sillones_recibe_403(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    creado = _crear_sillon(cliente, _headers(token_de(admin)))
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO)

    respuesta = cliente.patch(
        f"/sillones/{creado['id']}",
        json={"activo": False},
        headers=_headers(token_de(odontologo)),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    listado = cliente.get("/sillones", headers=_headers(token_de(admin))).json()
    assert listado == [creado]


def test_get_sillones_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.get("/sillones")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_post_sillones_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.post("/sillones", json={"nombre": "Sillón 1 (ficticio)"})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_patch_sillones_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.patch("/sillones/1", json={"activo": False})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


@pytest.mark.parametrize(
    "rol", [Rol.ADMINISTRACION, Rol.RECEPCION, Rol.ODONTOLOGO]
)
def test_get_sillones_permitido_para_los_tres_roles(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    rol: Rol,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    creado = _crear_sillon(cliente, _headers(token_de(admin)))
    usuario = crear_usuario(f"usuario_{rol.value}_ficticio", rol=rol)

    respuesta = cliente.get("/sillones", headers=_headers(token_de(usuario)))

    assert respuesta.status_code == 200
    assert respuesta.json() == [creado]
