"""Tests de `requiere_rol(*roles)` sobre rutas de prueba (C-03, RN-ACC-02 mecanismo)."""

from collections.abc import Callable

from fastapi.testclient import TestClient
from httpx import Response

from app.config import Config
from app.db.conexion import abrir_conexion
from app.domain.usuarios import Rol, Usuario


def _get(cliente: TestClient, ruta: str, token: str) -> Response:
    return cliente.get(ruta, headers={"Authorization": f"Bearer {token}"})


def _assert_sin_permiso(respuesta: Response) -> None:
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"


def test_recepcion_no_puede_entrar_a_una_ruta_solo_admin(
    cliente_con_rutas_prueba: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia")

    _assert_sin_permiso(_get(cliente_con_rutas_prueba, "/prueba/solo-admin", token_de(recepcion)))


def test_recepcion_entra_a_una_ruta_de_admin_o_recepcion(
    cliente_con_rutas_prueba: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia")

    respuesta = _get(cliente_con_rutas_prueba, "/prueba/admin-o-recepcion", token_de(recepcion))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"rol": "recepcion"}


def test_administracion_entra_a_una_ruta_solo_admin(
    cliente_con_rutas_prueba: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("administracion_ficticia", rol=Rol.ADMINISTRACION)

    respuesta = _get(cliente_con_rutas_prueba, "/prueba/solo-admin", token_de(admin))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"rol": "administracion"}


def test_usuario_cuyo_rol_cambio_despues_del_login_recibe_403(
    cliente_con_rutas_prueba: TestClient,
    config: Config,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    # Movido desde la 6.6: autoriza el rol guardado en la base, no el del token.
    recepcion = crear_usuario("recepcion_ficticia")
    token = token_de(recepcion)
    assert _get(cliente_con_rutas_prueba, "/prueba/solo-recepcion", token).status_code == 200

    conexion = abrir_conexion(config.database_path)
    try:
        conexion.execute("UPDATE usuario SET rol = ? WHERE id = ?", ("odontologo", recepcion.id))
    finally:
        conexion.close()

    _assert_sin_permiso(_get(cliente_con_rutas_prueba, "/prueba/solo-recepcion", token))


def test_sin_token_una_ruta_con_rol_responde_401_y_no_403(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.get("/prueba/solo-admin")

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"


def test_odontologo_no_entra_a_una_ruta_de_admin_o_recepcion(
    cliente_con_rutas_prueba: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    odontologo = crear_usuario("odontologo_ficticio", rol=Rol.ODONTOLOGO, profesional_id=1)

    respuesta = _get(cliente_con_rutas_prueba, "/prueba/admin-o-recepcion", token_de(odontologo))

    _assert_sin_permiso(respuesta)
    assert "www-authenticate" not in respuesta.headers


def test_administracion_tambien_entra_a_una_ruta_de_admin_o_recepcion(
    cliente_con_rutas_prueba: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    admin = crear_usuario("administracion_ficticia", rol=Rol.ADMINISTRACION)

    respuesta = _get(cliente_con_rutas_prueba, "/prueba/admin-o-recepcion", token_de(admin))

    assert respuesta.json() == {"rol": "administracion"}
