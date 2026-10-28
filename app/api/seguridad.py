"""Hash de contraseñas y token de acceso (C-03). Sin FastAPI: funciones puras de la capa API.

Las contraseñas se guardan solo como hash Argon2id con sal (RN-ACC-04).
"""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Aislado en dos funciones para poder cambiar de algoritmo sin tocar a quien las usa.
_hasher = PasswordHash((Argon2Hasher(),))


def hashear(password: str) -> str:
    """Devuelve el hash Argon2id (con sal aleatoria) de la contraseña."""
    return _hasher.hash(password)


def verificar(password: str, password_hash: str) -> bool:
    """Indica si la contraseña corresponde al hash guardado."""
    return _hasher.verify(password, password_hash)
