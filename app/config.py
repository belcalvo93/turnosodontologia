"""Configuración de la aplicación desde variables de entorno (C-01)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_DEFAULTS = {
    "APP_ENV": "development",
    "DATABASE_URL": "./turnos.db",
    "CLINIC_TIMEZONE": "America/Argentina/Buenos_Aires",
}


@dataclass(frozen=True)
class Config:
    """Configuración inmutable de la aplicación."""

    app_env: str
    database_path: Path
    clinic_timezone: str


def cargar_config(entorno: Mapping[str, str] | None = None) -> Config:
    """Construye la config desde el entorno; usa os.environ si no se inyecta."""
    valores = os.environ if entorno is None else entorno
    return Config(
        app_env=_valor(valores, "APP_ENV"),
        database_path=Path(_valor(valores, "DATABASE_URL")),
        clinic_timezone=_valor(valores, "CLINIC_TIMEZONE"),
    )


def _valor(valores: Mapping[str, str], clave: str) -> str:
    """Devuelve la variable del entorno o el default de desarrollo si falta o está vacía."""
    return valores.get(clave) or _DEFAULTS[clave]
