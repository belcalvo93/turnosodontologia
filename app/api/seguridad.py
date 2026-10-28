"""Hash de contraseñas y token de acceso (C-03). Sin FastAPI: funciones puras de la capa API.

Las contraseñas se guardan solo como hash Argon2id con sal (RN-ACC-04).
"""

from datetime import datetime
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config import Config
from app.domain.usuarios import Usuario

# Aislado en dos funciones para poder cambiar de algoritmo sin tocar a quien las usa.
_hasher = PasswordHash((Argon2Hasher(),))


def hashear(password: str) -> str:
    """Devuelve el hash Argon2id (con sal aleatoria) de la contraseña."""
    return _hasher.hash(password)


def verificar(password: str, password_hash: str) -> bool:
    """Indica si la contraseña corresponde al hash guardado."""
    return _hasher.verify(password, password_hash)


# PyJWT verifica la firma y la presencia de los claims. El tiempo lo verificamos nosotros
# contra `ahora`, porque PyJWT solo sabe compararlo con la hora real (design §11).
_OPCIONES_DECODIFICACION: dict[str, Any] = {
    "require": ["exp", "iat", "sub"],
    "verify_exp": False,
    "verify_iat": False,
}


class TokenInvalido(Exception):
    """El token no es confiable: firma, algoritmo, claims o `iat` en el futuro."""


class TokenVencido(TokenInvalido):
    """El token ya venció (`exp <= ahora`)."""


def emitir_token(usuario: Usuario, config: Config, ahora: datetime) -> str:
    """Firma un token para `usuario`, emitido en `ahora` y válido por la duración configurada."""
    emitido = int(ahora.timestamp())
    claims = {
        "sub": str(usuario.id),
        "rol": usuario.rol.value,
        "iat": emitido,
        "exp": emitido + config.access_token_expire_minutes * 60,
    }
    return jwt.encode(claims, config.jwt_secret, algorithm=config.jwt_algorithm)


def decodificar_token(token: str, config: Config, ahora: datetime) -> dict[str, Any]:
    """Valida firma y claims con PyJWT, y el tiempo contra `ahora` (no contra la hora real)."""
    try:
        # La lista fija de algoritmos bloquea `alg: none` y la confusión de algoritmos.
        claims: dict[str, Any] = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm],
            options=_OPCIONES_DECODIFICACION,
        )
    except jwt.InvalidTokenError as error:
        raise TokenInvalido("El token no es válido.") from error

    instante = ahora.timestamp()
    if claims["iat"] > instante:
        raise TokenInvalido("El token fue emitido en el futuro.")
    if claims["exp"] <= instante:
        raise TokenVencido("El token venció.")
    return claims
