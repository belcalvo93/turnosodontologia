"""Tests de hash de contraseñas y token, sin HTTP (C-03, RN-ACC-04)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.api.seguridad import (
    TokenInvalido,
    TokenVencido,
    decodificar_token,
    emitir_token,
    hashear,
    verificar,
)
from app.config import cargar_config
from app.domain.usuarios import Rol, Usuario

# Contraseñas ficticias: nunca usar credenciales reales en los tests.
CLAVE_FICTICIA = "clave-ficticia-123"
OTRA_CLAVE_FICTICIA = "otra-clave-ficticia"


def test_hash_no_es_ni_contiene_la_contrasena() -> None:
    hash_clave = hashear(CLAVE_FICTICIA)

    assert hash_clave != CLAVE_FICTICIA
    assert CLAVE_FICTICIA not in hash_clave


def test_misma_contrasena_produce_hashes_distintos() -> None:
    assert hashear(CLAVE_FICTICIA) != hashear(CLAVE_FICTICIA)


def test_verificar_acepta_solo_la_contrasena_correcta() -> None:
    hash_clave = hashear(CLAVE_FICTICIA)

    assert verificar(CLAVE_FICTICIA, hash_clave) is True
    assert verificar(OTRA_CLAVE_FICTICIA, hash_clave) is False


def test_el_hash_usa_argon2id() -> None:
    assert hashear(CLAVE_FICTICIA).startswith("$argon2id$")


@pytest.mark.parametrize("casi_igual", ["clave-ficticia-12", "Clave-Ficticia-123", ""])
def test_verificar_rechaza_contrasenas_casi_iguales(casi_igual: str) -> None:
    assert verificar(casi_igual, hashear(CLAVE_FICTICIA)) is False


def test_contrasena_con_caracteres_no_ascii_se_verifica() -> None:
    clave_con_enie = "contraseña-ficticia-ñandú"

    hash_clave = hashear(clave_con_enie)

    assert verificar(clave_con_enie, hash_clave) is True
    assert verificar("contrasena-ficticia-nandu", hash_clave) is False


# --- Token: el tiempo siempre llega como parámetro, nunca se lee la hora real ---

T = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
# 64+ caracteres: el caso HS512 firma con este mismo secreto y PyJWT exige 64 bytes para SHA-512.
SECRETO_FICTICIO = "secreto-ficticio-de-test-con-64-caracteres-o-mas-para-hs512-ok-ok"
CONFIG = cargar_config(entorno={"APP_ENV": "test", "JWT_SECRET": SECRETO_FICTICIO})

RECEPCION_FICTICIA = Usuario(
    id=1, username="recepcion_ficticia", rol=Rol.RECEPCION, profesional_id=None, activo=True
)


def test_ida_y_vuelta_del_token_conserva_sub_y_rol() -> None:
    token = emitir_token(RECEPCION_FICTICIA, CONFIG, ahora=T)

    claims = decodificar_token(token, CONFIG, ahora=T)

    assert claims["sub"] == "1"
    assert claims["rol"] == "recepcion"


def test_el_token_dura_access_token_expire_minutes() -> None:
    claims = decodificar_token(emitir_token(RECEPCION_FICTICIA, CONFIG, ahora=T), CONFIG, ahora=T)

    assert claims["iat"] == int(T.timestamp())
    assert claims["exp"] - claims["iat"] == CONFIG.access_token_expire_minutes * 60


def test_token_sigue_valido_un_minuto_antes_de_vencer() -> None:
    token = emitir_token(RECEPCION_FICTICIA, CONFIG, ahora=T)

    claims = decodificar_token(token, CONFIG, ahora=T + timedelta(minutes=59))

    assert claims["sub"] == "1"


def test_token_vence_en_el_instante_exacto_de_exp() -> None:
    token = emitir_token(RECEPCION_FICTICIA, CONFIG, ahora=T)

    with pytest.raises(TokenVencido):
        decodificar_token(token, CONFIG, ahora=T + timedelta(minutes=60))


def test_token_emitido_en_el_futuro_es_invalido() -> None:
    token = emitir_token(RECEPCION_FICTICIA, CONFIG, ahora=T)

    with pytest.raises(TokenInvalido):
        decodificar_token(token, CONFIG, ahora=T - timedelta(minutes=1))


def _claims_validos() -> dict[str, object]:
    return {
        "sub": "1",
        "rol": "recepcion",
        "iat": int(T.timestamp()),
        "exp": int((T + timedelta(minutes=60)).timestamp()),
    }


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(
            jwt.encode(_claims_validos(), "otra-clave-ficticia-con-32-caracteres-o-mas", "HS256"),
            id="firmado-con-otra-clave",
        ),
        pytest.param(jwt.encode(_claims_validos(), None, algorithm="none"), id="alg-none"),
        pytest.param(
            jwt.encode(
                {clave: valor for clave, valor in _claims_validos().items() if clave != "sub"},
                SECRETO_FICTICIO,
                "HS256",
            ),
            id="sin-sub",
        ),
    ],
)
def test_token_no_confiable_lanza_token_invalido(token: str) -> None:
    with pytest.raises(TokenInvalido):
        decodificar_token(token, CONFIG, ahora=T)


def test_la_duracion_configurada_define_el_vencimiento() -> None:
    config_corta = cargar_config(
        entorno={
            "APP_ENV": "test",
            "JWT_SECRET": SECRETO_FICTICIO,
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        }
    )
    token = emitir_token(RECEPCION_FICTICIA, config_corta, ahora=T)

    assert decodificar_token(token, config_corta, ahora=T + timedelta(minutes=14))["sub"] == "1"
    with pytest.raises(TokenVencido):
        decodificar_token(token, config_corta, ahora=T + timedelta(minutes=15))


@pytest.mark.parametrize(
    "token",
    [
        pytest.param("no-es-un-token", id="texto-arbitrario"),
        pytest.param(
            jwt.encode(_claims_validos(), SECRETO_FICTICIO, algorithm="HS512"),
            id="otro-algoritmo-hmac",
        ),
        pytest.param(
            jwt.encode({**_claims_validos(), "sub": 1}, SECRETO_FICTICIO, algorithm="HS256"),
            id="sub-no-string",
        ),
    ],
)
def test_otros_tokens_no_confiables_lanzan_token_invalido(token: str) -> None:
    with pytest.raises(TokenInvalido):
        decodificar_token(token, CONFIG, ahora=T)


def test_token_vencido_tambien_es_token_invalido() -> None:
    # Quien valida (usuario_actual) captura un solo error y responde 401 no_autenticado.
    token = emitir_token(RECEPCION_FICTICIA, CONFIG, ahora=T)

    with pytest.raises(TokenInvalido):
        decodificar_token(token, CONFIG, ahora=T + timedelta(hours=2))
