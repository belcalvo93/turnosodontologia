"""Tests de `POST /auth/login` (C-03). Usuarios y contraseñas ficticios."""

from collections.abc import Callable
from datetime import timedelta

from fastapi.testclient import TestClient

from app.api.seguridad import decodificar_token
from app.config import Config
from app.domain.usuarios import Rol, Usuario
from tests.conftest import CLAVE_FICTICIA, INSTANTE_INICIAL, RelojFijo


def test_login_correcto_devuelve_un_token_bearer_con_id_y_rol(
    cliente: TestClient,
    config: Config,
    reloj: RelojFijo,
    crear_usuario: Callable[..., Usuario],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia")

    respuesta = cliente.post(
        "/auth/login", json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    claims = decodificar_token(cuerpo["access_token"], config, ahora=reloj())
    assert claims["sub"] == str(recepcion.id)
    assert claims["rol"] == "recepcion"


def test_login_de_otro_usuario_lleva_su_propio_id_y_rol(
    cliente: TestClient,
    config: Config,
    reloj: RelojFijo,
    crear_usuario: Callable[..., Usuario],
) -> None:
    crear_usuario("recepcion_ficticia")
    odontologo = crear_usuario(
        "odontologo_ficticio", password="otra-clave-ficticia", rol=Rol.ODONTOLOGO, profesional_id=3
    )

    respuesta = cliente.post(
        "/auth/login", json={"username": "odontologo_ficticio", "password": "otra-clave-ficticia"}
    )

    claims = decodificar_token(respuesta.json()["access_token"], config, ahora=reloj())
    assert claims["sub"] == str(odontologo.id)
    assert claims["rol"] == "odontologo"


def test_login_emite_el_token_con_el_instante_del_reloj_inyectado(
    cliente: TestClient,
    config: Config,
    reloj: RelojFijo,
    crear_usuario: Callable[..., Usuario],
) -> None:
    crear_usuario("recepcion_ficticia")
    reloj.avanzar(minutes=30)

    respuesta = cliente.post(
        "/auth/login", json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA}
    )

    claims = decodificar_token(respuesta.json()["access_token"], config, ahora=reloj())
    assert claims["iat"] == int((INSTANTE_INICIAL + timedelta(minutes=30)).timestamp())


def test_la_respuesta_del_login_solo_trae_access_token_y_token_type(
    cliente: TestClient, crear_usuario: Callable[..., Usuario]
) -> None:
    crear_usuario("recepcion_ficticia")

    respuesta = cliente.post(
        "/auth/login", json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA}
    )

    assert set(respuesta.json()) == {"access_token", "token_type"}


def test_token_de_emite_en_el_instante_del_reloj_fijo(
    config: Config,
    reloj: RelojFijo,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia")

    claims = decodificar_token(token_de(recepcion), config, ahora=reloj())

    assert claims["sub"] == str(recepcion.id)
    assert claims["iat"] == int(INSTANTE_INICIAL.timestamp())
