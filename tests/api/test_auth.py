"""Tests de `POST /auth/login` (C-03). Usuarios y contraseñas ficticios."""

from collections.abc import Callable
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.api.seguridad import decodificar_token, verificar
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


# --- Login fallido: mismo 401 sin revelar qué usuarios existen ---

OTRA_CLAVE_FICTICIA = "otra-clave-ficticia"


def _login(cliente: TestClient, username: str, password: str) -> Response:
    return cliente.post("/auth/login", json={"username": username, "password": password})


@pytest.fixture
def hashes_verificados(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Espía `verificar` en el login: registra contra qué hash se comparó cada contraseña."""
    vistos: list[str] = []

    def _espia(password: str, password_hash: str) -> bool:
        vistos.append(password_hash)
        return verificar(password, password_hash)

    monkeypatch.setattr("app.api.auth.verificar", _espia)
    return vistos


def _assert_credenciales_invalidas(respuesta: Response) -> None:
    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "credenciales_invalidas"
    assert respuesta.headers["www-authenticate"] == "Bearer"


def test_login_de_usuario_inexistente_responde_credenciales_invalidas(
    cliente: TestClient,
) -> None:
    _assert_credenciales_invalidas(_login(cliente, "fantasma_ficticio", CLAVE_FICTICIA))


def test_login_con_contrasena_incorrecta_responde_credenciales_invalidas(
    cliente: TestClient, crear_usuario: Callable[..., Usuario]
) -> None:
    crear_usuario("recepcion_ficticia")

    _assert_credenciales_invalidas(_login(cliente, "recepcion_ficticia", OTRA_CLAVE_FICTICIA))


def test_login_de_usuario_inactivo_responde_credenciales_invalidas(
    cliente: TestClient, crear_usuario: Callable[..., Usuario]
) -> None:
    crear_usuario("inactivo_ficticio", activo=False)

    _assert_credenciales_invalidas(_login(cliente, "inactivo_ficticio", CLAVE_FICTICIA))


def test_los_tres_logins_fallidos_devuelven_el_mismo_cuerpo(
    cliente: TestClient, crear_usuario: Callable[..., Usuario]
) -> None:
    crear_usuario("recepcion_ficticia")
    crear_usuario("inactivo_ficticio", activo=False)

    cuerpos = [
        _login(cliente, "fantasma_ficticio", CLAVE_FICTICIA).content,
        _login(cliente, "recepcion_ficticia", OTRA_CLAVE_FICTICIA).content,
        _login(cliente, "inactivo_ficticio", CLAVE_FICTICIA).content,
    ]

    assert cuerpos[0] == cuerpos[1] == cuerpos[2]


def test_usuario_inexistente_igual_verifica_contra_un_hash_ficticio(
    cliente: TestClient, hashes_verificados: list[str]
) -> None:
    _login(cliente, "fantasma_ficticio", CLAVE_FICTICIA)

    assert len(hashes_verificados) == 1
    assert hashes_verificados[0].startswith("$argon2id$")


def test_el_hash_ficticio_se_calcula_una_sola_vez(
    cliente: TestClient, hashes_verificados: list[str]
) -> None:
    _login(cliente, "fantasma_ficticio", CLAVE_FICTICIA)
    _login(cliente, "otro_fantasma_ficticio", OTRA_CLAVE_FICTICIA)

    assert len(hashes_verificados) == 2
    assert hashes_verificados[0] == hashes_verificados[1]


def test_usuario_inactivo_igual_verifica_su_contrasena(
    cliente: TestClient,
    crear_usuario: Callable[..., Usuario],
    hashes_verificados: list[str],
) -> None:
    crear_usuario("inactivo_ficticio", activo=False)

    _login(cliente, "inactivo_ficticio", CLAVE_FICTICIA)

    assert len(hashes_verificados) == 1
    assert verificar(CLAVE_FICTICIA, hashes_verificados[0]) is True
