"""Tests de `usuario_actual` sobre `GET /prueba/autenticado` (C-03, RN-ACC-01)."""

from collections.abc import Callable

import jwt
import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.api.seguridad import emitir_token
from app.config import Config
from app.domain.usuarios import Rol, Usuario
from tests.conftest import CLAVE_FICTICIA, INSTANTE_INICIAL, RelojFijo

RUTA = "/prueba/autenticado"


def _claims_de_id(sub: str) -> dict[str, object]:
    emitido = int(INSTANTE_INICIAL.timestamp())
    return {"sub": sub, "iat": emitido, "exp": emitido + 3600}


def _claims_de(usuario: Usuario) -> dict[str, object]:
    return {**_claims_de_id(str(usuario.id)), "rol": usuario.rol.value}


def _assert_no_autenticado(respuesta: Response) -> None:
    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "no_autenticado"
    assert respuesta.headers["www-authenticate"] == "Bearer"


def test_sin_cabecera_authorization_responde_no_autenticado(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    _assert_no_autenticado(cliente_con_rutas_prueba.get(RUTA))


@pytest.mark.parametrize(
    "authorization",
    [
        pytest.param("Basic dXN1YXJpbzpjbGF2ZQ==", id="esquema-basic"),
        pytest.param("no-es-un-token", id="texto-arbitrario-sin-esquema"),
        pytest.param("Bearer no-es-un-token", id="texto-arbitrario-como-bearer"),
    ],
)
def test_cabecera_mal_formada_o_token_ilegible_responde_no_autenticado(
    cliente_con_rutas_prueba: TestClient, authorization: str
) -> None:
    _assert_no_autenticado(
        cliente_con_rutas_prueba.get(RUTA, headers={"Authorization": authorization})
    )


def test_token_firmado_con_otra_clave_responde_no_autenticado(
    cliente_con_rutas_prueba: TestClient, crear_usuario: Callable[..., Usuario]
) -> None:
    recepcion = crear_usuario("recepcion_ficticia")
    token = jwt.encode(
        _claims_de(recepcion), "otra-clave-ficticia-con-32-caracteres-o-mas", algorithm="HS256"
    )

    _assert_no_autenticado(
        cliente_con_rutas_prueba.get(RUTA, headers={"Authorization": f"Bearer {token}"})
    )


def test_token_valido_responde_200_con_el_usuario(
    cliente_con_rutas_prueba: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    recepcion = crear_usuario("recepcion_ficticia")

    respuesta = cliente_con_rutas_prueba.get(
        RUTA, headers={"Authorization": f"Bearer {token_de(recepcion)}"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"id": recepcion.id, "rol": "recepcion"}


def test_token_con_algoritmo_none_responde_no_autenticado(
    cliente_con_rutas_prueba: TestClient, crear_usuario: Callable[..., Usuario]
) -> None:
    token = jwt.encode(_claims_de(crear_usuario("recepcion_ficticia")), None, algorithm="none")

    _assert_no_autenticado(
        cliente_con_rutas_prueba.get(RUTA, headers={"Authorization": f"Bearer {token}"})
    )


def test_token_valido_de_un_usuario_que_no_existe_responde_no_autenticado(
    cliente_con_rutas_prueba: TestClient, config: Config
) -> None:
    fantasma = Usuario(
        id=999, username="fantasma_ficticio", rol=Rol.RECEPCION, profesional_id=None, activo=True
    )
    token = emitir_token(fantasma, config, ahora=INSTANTE_INICIAL)

    _assert_no_autenticado(
        cliente_con_rutas_prueba.get(RUTA, headers={"Authorization": f"Bearer {token}"})
    )


def test_token_firmado_por_el_sistema_con_sub_no_numerico_responde_no_autenticado(
    cliente_con_rutas_prueba: TestClient, config: Config
) -> None:
    claims = {**_claims_de_id("no-es-un-id"), "rol": "recepcion"}
    token = jwt.encode(claims, config.jwt_secret, algorithm=config.jwt_algorithm)

    _assert_no_autenticado(
        cliente_con_rutas_prueba.get(RUTA, headers={"Authorization": f"Bearer {token}"})
    )


def test_cada_token_valido_identifica_a_su_propio_usuario(
    cliente_con_rutas_prueba: TestClient,
    crear_usuario: Callable[..., Usuario],
    token_de: Callable[[Usuario], str],
) -> None:
    crear_usuario("recepcion_ficticia")
    admin = crear_usuario("administracion_ficticia", rol=Rol.ADMINISTRACION)

    respuesta = cliente_con_rutas_prueba.get(
        RUTA, headers={"Authorization": f"Bearer {token_de(admin)}"}
    )

    assert respuesta.json() == {"id": admin.id, "rol": "administracion"}


def test_el_token_vence_al_mover_el_reloj_fijo_sin_esperar(
    cliente_con_rutas_prueba: TestClient,
    config: Config,
    reloj: RelojFijo,
    crear_usuario: Callable[..., Usuario],
) -> None:
    # Sin sleep ni hora real: el tiempo solo avanza con `reloj.avanzar(...)`.
    assert config.access_token_expire_minutes == 60
    crear_usuario("recepcion_ficticia")
    login = cliente_con_rutas_prueba.post(
        "/auth/login", json={"username": "recepcion_ficticia", "password": CLAVE_FICTICIA}
    )
    cabeceras = {"Authorization": f"Bearer {login.json()['access_token']}"}

    reloj.avanzar(minutes=59)
    assert cliente_con_rutas_prueba.get(RUTA, headers=cabeceras).status_code == 200

    reloj.avanzar(minutes=1)
    _assert_no_autenticado(cliente_con_rutas_prueba.get(RUTA, headers=cabeceras))
