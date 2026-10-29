"""Tests de API para prestaciones y permisos RBAC (C-05, RN-REC-01, RN-REC-03)."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.domain.usuarios import Rol, Usuario


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _crear_prestacion(
    cliente: TestClient,
    cabeceras: dict[str, str],
    nombre: str = "Consulta ficticia",
    duracion_minutos: int = 45,
) -> dict[str, object]:
    return cliente.post(
        "/prestaciones",
        json={"nombre": nombre, "duracion_minutos": duracion_minutos},
        headers=cabeceras,
    ).json()


def test_post_prestaciones_alta_valida_normaliza_el_nombre(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "  Consulta ficticia  ", "duracion_minutos": 45},
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 1,
        "nombre": "Consulta ficticia",
        "duracion_minutos": 45,
        "activa": True,
    }


def test_post_prestaciones_con_nombre_duplicado_responde_409(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    _crear_prestacion(cliente, cabeceras)

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "Consulta ficticia", "duracion_minutos": 30},
        headers=cabeceras,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "nombre_duplicado"
    mensaje = respuesta.json()["mensaje"]
    assert isinstance(mensaje, str) and mensaje.strip() != ""
    assert len(cliente.get("/prestaciones", headers=cabeceras).json()) == 1


def test_post_prestaciones_con_nombre_vacio_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "", "duracion_minutos": 45},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == []


def test_post_prestaciones_con_nombre_solo_espacios_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "   ", "duracion_minutos": 45},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == []


def test_post_prestaciones_con_duracion_cero_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "Consulta ficticia", "duracion_minutos": 0},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == []


def test_post_prestaciones_con_duracion_negativa_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "Consulta ficticia", "duracion_minutos": -30},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == []


def test_patch_prestaciones_desactiva_y_sigue_en_el_listado(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}", json={"activa": False}, headers=cabeceras
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": creada["id"],
        "nombre": "Consulta ficticia",
        "duracion_minutos": 45,
        "activa": False,
    }
    assert cliente.get("/prestaciones", headers=cabeceras).json() == [
        respuesta.json()
    ]


def test_patch_prestaciones_renombra_la_prestacion(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}",
        json={"nombre": "  Consulta ficticia bis  "},
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": creada["id"],
        "nombre": "Consulta ficticia bis",
        "duracion_minutos": 45,
        "activa": True,
    }


def test_patch_prestaciones_cambia_la_duracion(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras, duracion_minutos=30)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}",
        json={"duracion_minutos": 60},
        headers=cabeceras,
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": creada["id"],
        "nombre": "Consulta ficticia",
        "duracion_minutos": 60,
        "activa": True,
    }


def test_patch_prestaciones_a_nombre_existente_responde_409(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    _crear_prestacion(cliente, cabeceras, "Consulta ficticia", 45)
    segunda = _crear_prestacion(cliente, cabeceras, "Limpieza ficticia", 30)

    respuesta = cliente.patch(
        f"/prestaciones/{segunda['id']}",
        json={"nombre": "Consulta ficticia"},
        headers=cabeceras,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "nombre_duplicado"
    assert cliente.get("/prestaciones", headers=cabeceras).json()[1] == segunda


def test_patch_prestaciones_con_nombre_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}", json={"nombre": None}, headers=cabeceras
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == [creada]


def test_patch_prestaciones_con_duracion_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}",
        json={"duracion_minutos": None},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == [creada]


def test_patch_prestaciones_con_activa_null_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}", json={"activa": None}, headers=cabeceras
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == [creada]


def test_patch_prestaciones_con_nombre_solo_espacios_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}", json={"nombre": "   "}, headers=cabeceras
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == [creada]


@pytest.mark.parametrize("duracion_invalida", [0, -30])
def test_patch_prestaciones_con_duracion_invalida_responde_422_y_conserva_la_anterior(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    duracion_invalida: int,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    creada = _crear_prestacion(cliente, cabeceras, duracion_minutos=45)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}",
        json={"duracion_minutos": duracion_invalida},
        headers=cabeceras,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == [creada]


def test_patch_prestaciones_inexistente_responde_404(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = cliente.patch(
        "/prestaciones/9999",
        json={"activa": False},
        headers=_headers(token_de(admin)),
    )

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "no_encontrado"
    assert isinstance(cuerpo["mensaje"], str)
    assert cuerpo["mensaje"].strip() != ""


def test_recepcion_post_prestaciones_recibe_403(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    cabeceras = _headers(token_de(recepcion))

    respuesta = cliente.post(
        "/prestaciones",
        json={"nombre": "Consulta ficticia", "duracion_minutos": 45},
        headers=cabeceras,
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert cliente.get("/prestaciones", headers=cabeceras).json() == []


def test_odontologo_patch_prestaciones_recibe_403(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    creada = _crear_prestacion(cliente, _headers(token_de(admin)))
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO)

    respuesta = cliente.patch(
        f"/prestaciones/{creada['id']}",
        json={"activa": False},
        headers=_headers(token_de(odontologo)),
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    listado = cliente.get("/prestaciones", headers=_headers(token_de(admin))).json()
    assert listado == [creada]


def test_get_prestaciones_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.get("/prestaciones")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_post_prestaciones_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/prestaciones", json={"nombre": "Consulta ficticia", "duracion_minutos": 45}
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_patch_prestaciones_sin_token_responde_401(cliente: TestClient) -> None:
    respuesta = cliente.patch("/prestaciones/1", json={"activa": False})

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


@pytest.mark.parametrize(
    "rol", [Rol.ADMINISTRACION, Rol.RECEPCION, Rol.ODONTOLOGO]
)
def test_get_prestaciones_permitido_para_los_tres_roles(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    rol: Rol,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    creada = _crear_prestacion(cliente, _headers(token_de(admin)))
    usuario = crear_usuario(f"usuario_{rol.value}_ficticio", rol=rol)

    respuesta = cliente.get("/prestaciones", headers=_headers(token_de(usuario)))

    assert respuesta.status_code == 200
    assert respuesta.json() == [creada]
