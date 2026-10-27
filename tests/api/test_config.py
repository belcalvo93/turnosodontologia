"""Tests de la configuración leída desde variables de entorno (C-01)."""

from pathlib import Path

from app.config import cargar_config


def test_entorno_vacio_usa_defaults_de_desarrollo() -> None:
    config = cargar_config(entorno={})

    assert config.app_env == "development"
    assert config.database_path == Path("./turnos.db")
    assert config.clinic_timezone == "America/Argentina/Buenos_Aires"
