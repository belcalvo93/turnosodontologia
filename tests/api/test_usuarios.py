"""Tests de API de la gestión de usuarios y permisos RBAC (C-07, US-013)."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.domain.usuarios import Rol, Usuario

CLAVE_FICTICIA = "clave-ficticia-123"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _crear_profesional(
    cliente: TestClient,
    cabeceras: dict[str, str],
    *,
    activo: bool = True,
    matricula: str = "0001 (ficticia)",
) -> int:
    respuesta = cliente.post(
        "/profesionales",
        json={
            "nombre": "Odontóloga",
            "apellido": "Ficticia A",
            "matricula": matricula,
        },
        headers=cabeceras,
    )
    assert respuesta.status_code == 201
    id_profesional = int(respuesta.json()["id"])
    if not activo:
        respuesta_patch = cliente.patch(
            f"/profesionales/{id_profesional}", json={"activo": False}, headers=cabeceras
        )
        assert respuesta_patch.status_code == 200
    return id_profesional


def _crear_usuario(
    cliente: TestClient,
    cabeceras: dict[str, str],
    *,
    username: str = "recepcion_ficticia",
    password: str = CLAVE_FICTICIA,
    rol: str = "recepcion",
    profesional_id: int | None = None,
):
    cuerpo: dict[str, object] = {"username": username, "password": password, "rol": rol}
    if profesional_id is not None:
        cuerpo["profesional_id"] = profesional_id
    return cliente.post("/usuarios", json=cuerpo, headers=cabeceras)


# --- POST /usuarios ---------------------------------------------------------------


def test_post_usuarios_recepcion_responde_201_sin_profesional(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(cliente, _headers(token_de(admin)))

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id": 2,
        "username": "recepcion_ficticia",
        "rol": "recepcion",
        "profesional_id": None,
        "activo": True,
    }


def test_post_usuarios_odontologo_con_profesional_activo_responde_201(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    id_profesional = _crear_profesional(cliente, cabeceras)

    respuesta = _crear_usuario(
        cliente,
        cabeceras,
        username="odontologo_ficticio",
        rol="odontologo",
        profesional_id=id_profesional,
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["rol"] == "odontologo"
    assert respuesta.json()["profesional_id"] == id_profesional


def test_post_usuarios_username_duplicado_responde_409(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    crear_usuario("recepcion_ficticia")

    respuesta = _crear_usuario(cliente, _headers(token_de(admin)))

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "username_duplicado"
    assert "recepcion_ficticia" not in cuerpo["mensaje"]
    assert set(cuerpo) == {"codigo", "mensaje"}


def test_post_usuarios_odontologo_sin_profesional_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(
        cliente, _headers(token_de(admin)), username="odontologo_ficticio", rol="odontologo"
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_post_usuarios_odontologo_con_profesional_inexistente_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(
        cliente,
        _headers(token_de(admin)),
        username="odontologo_ficticio",
        rol="odontologo",
        profesional_id=9999,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_post_usuarios_odontologo_con_profesional_inactivo_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    id_profesional = _crear_profesional(cliente, cabeceras, activo=False)

    respuesta = _crear_usuario(
        cliente,
        cabeceras,
        username="odontologo_ficticio",
        rol="odontologo",
        profesional_id=id_profesional,
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_post_usuarios_rol_sin_vinculo_con_profesional_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    cabeceras = _headers(token_de(admin))
    id_profesional = _crear_profesional(cliente, cabeceras)

    respuesta = _crear_usuario(cliente, cabeceras, profesional_id=id_profesional)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_post_usuarios_administracion_sin_profesional_responde_201(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(
        cliente, _headers(token_de(admin)), username="otra_admin_ficticia", rol="administracion"
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["profesional_id"] is None


@pytest.mark.parametrize("username", ["", "   "])
def test_post_usuarios_username_vacio_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    username: str,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(cliente, _headers(token_de(admin)), username=username)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_post_usuarios_password_vacia_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(cliente, _headers(token_de(admin)), password="")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_post_usuarios_rol_fuera_del_mvp_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(cliente, _headers(token_de(admin)), rol="paciente")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"


def test_post_usuarios_no_expone_el_hash(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _crear_usuario(cliente, _headers(token_de(admin)))

    assert respuesta.status_code == 201
    assert "password" not in respuesta.text
    assert "password_hash" not in respuesta.text


# --- GET /usuarios ----------------------------------------------------------------


def test_get_usuarios_lista_ordenado_e_incluye_inactivos(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia", rol=Rol.RECEPCION)
    odontologo = crear_usuario(
        "odontologo_ficticio", rol=Rol.ODONTOLOGO, profesional_id=5, activo=False
    )

    respuesta = cliente.get("/usuarios", headers=_headers(token_de(admin)))

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {
            "id": admin.id,
            "username": "admin_ficticio",
            "rol": "administracion",
            "profesional_id": None,
            "activo": True,
        },
        {
            "id": recepcion.id,
            "username": "recepcion_ficticia",
            "rol": "recepcion",
            "profesional_id": None,
            "activo": True,
        },
        {
            "id": odontologo.id,
            "username": "odontologo_ficticio",
            "rol": "odontologo",
            "profesional_id": 5,
            "activo": False,
        },
    ]


def test_get_usuarios_no_expone_el_hash(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    crear_usuario("recepcion_ficticia")

    respuesta = cliente.get("/usuarios", headers=_headers(token_de(admin)))

    assert respuesta.status_code == 200
    assert "password" not in respuesta.text
    assert all("password_hash" not in usuario for usuario in respuesta.json())


@pytest.mark.parametrize("rol", [Rol.RECEPCION, Rol.ODONTOLOGO])
def test_get_usuarios_rol_sin_permiso_responde_403(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    rol: Rol,
) -> None:
    usuario = crear_usuario("usuario_ficticio", rol=rol)

    respuesta = cliente.get("/usuarios", headers=_headers(token_de(usuario)))

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


# --- PATCH /usuarios/{id} ---------------------------------------------------------


def _patch_usuario(
    cliente: TestClient,
    cabeceras: dict[str, str],
    id_usuario: int,
    cuerpo: dict[str, object],
):
    return cliente.patch(f"/usuarios/{id_usuario}", json=cuerpo, headers=cabeceras)


def _usuarios_por_id(
    cliente: TestClient, cabeceras: dict[str, str]
) -> dict[int, dict[str, object]]:
    respuesta = cliente.get("/usuarios", headers=cabeceras)
    assert respuesta.status_code == 200
    return {int(usuario["id"]): usuario for usuario in respuesta.json()}


def _llamar(
    cliente: TestClient,
    metodo: str,
    ruta: str,
    cuerpo: dict[str, object] | None,
    *,
    cabeceras: dict[str, str] | None = None,
):
    """Ejecuta GET/POST/PATCH sin enviar `json` en los métodos que no lo admiten."""
    kwargs: dict[str, object] = {} if cabeceras is None else {"headers": cabeceras}
    if cuerpo is None:
        return getattr(cliente, metodo)(ruta, **kwargs)
    return getattr(cliente, metodo)(ruta, json=cuerpo, **kwargs)


def test_patch_usuarios_desactiva_y_reactiva(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    desactivado = _patch_usuario(cliente, cabeceras, recepcion.id, {"activo": False})
    reactivado = _patch_usuario(cliente, cabeceras, recepcion.id, {"activo": True})

    assert desactivado.status_code == 200
    assert desactivado.json()["activo"] is False
    assert reactivado.status_code == 200
    assert reactivado.json()["activo"] is True


@pytest.mark.parametrize("campo", ["rol", "activo"])
def test_patch_usuarios_campo_nulo_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    campo: str,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    respuesta = _patch_usuario(cliente, cabeceras, recepcion.id, {campo: None})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert _usuarios_por_id(cliente, cabeceras)[recepcion.id] == {
        "id": recepcion.id,
        "username": "recepcion_ficticia",
        "rol": "recepcion",
        "profesional_id": None,
        "activo": True,
    }


def test_patch_usuarios_username_presente_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    respuesta = _patch_usuario(
        cliente, cabeceras, recepcion.id, {"username": "otro_nombre_ficticio"}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert _usuarios_por_id(cliente, cabeceras)[recepcion.id]["username"] == "recepcion_ficticia"


def test_patch_usuarios_inexistente_responde_404(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _patch_usuario(cliente, _headers(token_de(admin)), 9999, {"activo": False})

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "no_encontrado"
    assert cuerpo["mensaje"]


def test_patch_usuarios_recepcion_a_odontologo_con_profesional(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    id_profesional = _crear_profesional(cliente, cabeceras)
    assert recepcion.id is not None

    respuesta = _patch_usuario(
        cliente,
        cabeceras,
        recepcion.id,
        {"rol": "odontologo", "profesional_id": id_profesional},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "odontologo"
    assert respuesta.json()["profesional_id"] == id_profesional


def test_patch_usuarios_recepcion_a_odontologo_sin_profesional_responde_422(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    respuesta = _patch_usuario(cliente, cabeceras, recepcion.id, {"rol": "odontologo"})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert _usuarios_por_id(cliente, cabeceras)[recepcion.id]["rol"] == "recepcion"
    assert _usuarios_por_id(cliente, cabeceras)[recepcion.id]["profesional_id"] is None


@pytest.mark.parametrize("rol_nuevo", ["recepcion", "administracion"])
def test_patch_usuarios_salir_de_odontologo_limpia_el_profesional(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    rol_nuevo: str,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO, profesional_id=5)
    cabeceras = _headers(token_de(admin))
    assert odontologo.id is not None

    respuesta = _patch_usuario(cliente, cabeceras, odontologo.id, {"rol": rol_nuevo})

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == rol_nuevo
    assert respuesta.json()["profesional_id"] is None


def test_patch_usuarios_cambia_profesional_conservando_el_rol(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO, profesional_id=5)
    cabeceras = _headers(token_de(admin))
    id_profesional = _crear_profesional(cliente, cabeceras)
    assert odontologo.id is not None

    respuesta = _patch_usuario(
        cliente, cabeceras, odontologo.id, {"profesional_id": id_profesional}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "odontologo"
    assert respuesta.json()["profesional_id"] == id_profesional


def test_patch_usuarios_profesional_inactivo_responde_422_sin_modificar(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO, profesional_id=5)
    cabeceras = _headers(token_de(admin))
    id_profesional = _crear_profesional(cliente, cabeceras, activo=False)
    assert odontologo.id is not None

    respuesta = _patch_usuario(
        cliente, cabeceras, odontologo.id, {"profesional_id": id_profesional}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    assert _usuarios_por_id(cliente, cabeceras)[odontologo.id]["profesional_id"] == 5


def test_patch_usuarios_reset_de_password_cambia_el_hash_y_habilita_el_login(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    respuesta = _patch_usuario(
        cliente, cabeceras, recepcion.id, {"password": "nueva-clave-ficticia-789"}
    )

    assert respuesta.status_code == 200
    assert "password" not in respuesta.text
    login_nuevo = cliente.post(
        "/auth/login",
        json={"username": "recepcion_ficticia", "password": "nueva-clave-ficticia-789"},
    )
    login_viejo = cliente.post(
        "/auth/login",
        json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA},
    )
    assert login_nuevo.status_code == 200
    assert login_nuevo.json()["access_token"]
    assert login_viejo.status_code == 401
    assert login_viejo.json()["codigo"] == "credenciales_invalidas"


def test_patch_usuarios_sin_password_conserva_el_hash(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    _patch_usuario(cliente, cabeceras, recepcion.id, {"activo": False})
    _patch_usuario(cliente, cabeceras, recepcion.id, {"activo": True})

    login = cliente.post(
        "/auth/login",
        json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA},
    )
    assert login.status_code == 200


def test_patch_usuarios_password_vacia_responde_422_sin_cambiar_el_hash(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    respuesta = _patch_usuario(cliente, cabeceras, recepcion.id, {"password": ""})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_invalido"
    login = cliente.post(
        "/auth/login",
        json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA},
    )
    assert login.status_code == 200


def test_patch_usuarios_no_expone_el_hash(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    assert recepcion.id is not None

    respuesta = _patch_usuario(
        cliente, _headers(token_de(admin)), recepcion.id, {"password": "otra-clave-ficticia-000"}
    )

    assert respuesta.status_code == 200
    assert "password" not in respuesta.text
    assert "password_hash" not in respuesta.text


# --- Acceso, baja lógica y métodos no admitidos ------------------------------------

_RUTAS_USUARIOS = [
    pytest.param("get", "/usuarios", None, id="get"),
    pytest.param(
        "post",
        "/usuarios",
        {"username": "nuevo_ficticio", "password": CLAVE_FICTICIA, "rol": "recepcion"},
        id="post",
    ),
    pytest.param("patch", "/usuarios/1", {"activo": False}, id="patch"),
]


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), _RUTAS_USUARIOS)
def test_rutas_usuarios_sin_token_responde_401(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    metodo: str,
    ruta: str,
    cuerpo: dict[str, object] | None,
) -> None:
    crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)

    respuesta = _llamar(cliente, metodo, ruta, cuerpo)

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), _RUTAS_USUARIOS)
@pytest.mark.parametrize("rol", [Rol.RECEPCION, Rol.ODONTOLOGO])
def test_rutas_usuarios_rol_sin_permiso_responde_403(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
    metodo: str,
    ruta: str,
    cuerpo: dict[str, object] | None,
    rol: Rol,
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    usuario = crear_usuario("usuario_ficticio", rol=rol)

    respuesta = _llamar(cliente, metodo, ruta, cuerpo, cabeceras=_headers(token_de(usuario)))

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    assert _usuarios_por_id(cliente, _headers(token_de(admin))) == {
        admin.id: {
            "id": admin.id,
            "username": "admin_ficticio",
            "rol": "administracion",
            "profesional_id": None,
            "activo": True,
        },
        usuario.id: {
            "id": usuario.id,
            "username": "usuario_ficticio",
            "rol": rol.value,
            "profesional_id": None,
            "activo": True,
        },
    }


def test_delete_usuarios_responde_405_y_conserva_el_usuario(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    cabeceras = _headers(token_de(admin))
    assert recepcion.id is not None

    respuesta = cliente.delete(f"/usuarios/{recepcion.id}", headers=cabeceras)

    assert respuesta.status_code == 405
    assert respuesta.json()["codigo"] == "metodo_no_permitido"
    assert recepcion.id in _usuarios_por_id(cliente, cabeceras)


def test_usuario_desactivado_no_puede_loguear(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    assert recepcion.id is not None
    _patch_usuario(cliente, _headers(token_de(admin)), recepcion.id, {"activo": False})

    login = cliente.post(
        "/auth/login",
        json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA},
    )

    assert login.status_code == 401
    assert login.json()["codigo"] == "credenciales_invalidas"


def test_token_emitido_antes_de_la_desactivacion_deja_de_servir(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("admin_ficticio", rol=Rol.ADMINISTRACION)
    recepcion = crear_usuario("recepcion_ficticia")
    assert recepcion.id is not None
    token_recepcion = token_de(recepcion)
    _patch_usuario(cliente, _headers(token_de(admin)), recepcion.id, {"activo": False})

    respuesta = cliente.get("/usuarios", headers=_headers(token_recepcion))

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
