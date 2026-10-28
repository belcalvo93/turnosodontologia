"""Configuración de la aplicación desde variables de entorno (C-01, C-03)."""

import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_DEFAULTS = {
    "APP_ENV": "development",
    "DATABASE_URL": "./turnos.db",
    "CLINIC_TIMEZONE": "America/Argentina/Buenos_Aires",
    "JWT_ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
}

_PREFIJO_SQLITE = "sqlite:///"

# Entornos donde, sin JWT_SECRET, se admite un secreto aleatorio por proceso.
_ENTORNOS_CON_SECRETO_ALEATORIO = frozenset({"development", "test"})

# El secreto es simétrico: solo se admiten algoritmos HMAC.
_ALGORITMOS_JWT_ADMITIDOS = ("HS256", "HS384", "HS512")


class ConfigInvalida(ValueError):
    """La configuración del entorno no permite arrancar la aplicación."""


@dataclass(frozen=True)
class Config:
    """Configuración inmutable de la aplicación."""

    app_env: str
    database_path: Path
    clinic_timezone: str
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    seed_admin_password: str | None


def cargar_config(entorno: Mapping[str, str] | None = None) -> Config:
    """Construye la config desde el entorno; usa os.environ si no se inyecta."""
    valores = os.environ if entorno is None else entorno
    app_env = _valor(valores, "APP_ENV")
    return Config(
        app_env=app_env,
        database_path=_normalizar_database_url(_valor(valores, "DATABASE_URL")),
        clinic_timezone=_valor(valores, "CLINIC_TIMEZONE"),
        jwt_secret=_jwt_secret(valores, app_env),
        jwt_algorithm=_jwt_algorithm(_valor(valores, "JWT_ALGORITHM")),
        access_token_expire_minutes=_minutos_de_expiracion(
            _valor(valores, "ACCESS_TOKEN_EXPIRE_MINUTES")
        ),
        seed_admin_password=valores.get("SEED_ADMIN_PASSWORD") or None,
    )


def _valor(valores: Mapping[str, str], clave: str) -> str:
    """Devuelve la variable del entorno o el default de desarrollo si falta o está vacía."""
    return valores.get(clave) or _DEFAULTS[clave]


def _jwt_secret(valores: Mapping[str, str], app_env: str) -> str:
    """Devuelve JWT_SECRET; si falta, uno aleatorio en development/test o falla.

    Nunca hay un secreto fijo en el código (regla dura 9).
    """
    secreto = valores.get("JWT_SECRET")
    if secreto:
        return secreto
    if app_env in _ENTORNOS_CON_SECRETO_ALEATORIO:
        return secrets.token_urlsafe(32)
    raise ConfigInvalida(
        f"Falta la variable de entorno JWT_SECRET (obligatoria con APP_ENV={app_env})."
    )


def _jwt_algorithm(valor: str) -> str:
    """Valida que JWT_ALGORITHM sea un algoritmo HMAC admitido."""
    if valor not in _ALGORITMOS_JWT_ADMITIDOS:
        admitidos = ", ".join(_ALGORITMOS_JWT_ADMITIDOS)
        raise ConfigInvalida(f"JWT_ALGORITHM inválido: {valor!r}. Valores admitidos: {admitidos}.")
    return valor


def _minutos_de_expiracion(valor: str) -> int:
    """Convierte ACCESS_TOKEN_EXPIRE_MINUTES a un entero mayor que 0."""
    error = ConfigInvalida(
        f"ACCESS_TOKEN_EXPIRE_MINUTES debe ser un entero mayor que 0 (recibido: {valor!r})."
    )
    try:
        minutos = int(valor)
    except ValueError:
        raise error from None
    if minutos <= 0:
        raise error
    return minutos


def _normalizar_database_url(valor: str) -> Path:
    """Acepta `sqlite:///ruta` o un path plano y devuelve el path de la base."""
    return Path(valor.removeprefix(_PREFIJO_SQLITE))
