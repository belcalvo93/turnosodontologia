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
    return Config(
        app_env=_valor(valores, "APP_ENV"),
        database_path=_normalizar_database_url(_valor(valores, "DATABASE_URL")),
        clinic_timezone=_valor(valores, "CLINIC_TIMEZONE"),
        jwt_secret=_jwt_secret(valores),
        jwt_algorithm=_valor(valores, "JWT_ALGORITHM"),
        access_token_expire_minutes=int(_valor(valores, "ACCESS_TOKEN_EXPIRE_MINUTES")),
        seed_admin_password=valores.get("SEED_ADMIN_PASSWORD") or None,
    )


def _valor(valores: Mapping[str, str], clave: str) -> str:
    """Devuelve la variable del entorno o el default de desarrollo si falta o está vacía."""
    return valores.get(clave) or _DEFAULTS[clave]


def _jwt_secret(valores: Mapping[str, str]) -> str:
    """Devuelve JWT_SECRET o, si falta, uno aleatorio por carga (nunca un valor fijo en el código)."""
    return valores.get("JWT_SECRET") or secrets.token_urlsafe(32)


def _normalizar_database_url(valor: str) -> Path:
    """Acepta `sqlite:///ruta` o un path plano y devuelve el path de la base."""
    return Path(valor.removeprefix(_PREFIJO_SQLITE))
