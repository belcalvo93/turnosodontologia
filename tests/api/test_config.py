"""Tests de la configuración leída desde variables de entorno (C-01)."""

from pathlib import Path

from app.config import cargar_config


def test_entorno_vacio_usa_defaults_de_desarrollo() -> None:
    config = cargar_config(entorno={})

    assert config.app_env == "development"
    assert config.database_path == Path("./turnos.db")
    assert config.clinic_timezone == "America/Argentina/Buenos_Aires"


def test_database_url_con_esquema_de_url_se_normaliza() -> None:
    config = cargar_config(
        entorno={
            "APP_ENV": "test",
            "DATABASE_URL": "sqlite:///./turnos.db",
        }
    )

    assert config.app_env == "test"
    assert config.database_path == Path("./turnos.db")


def test_database_url_con_path_absoluto_queda_intacto(tmp_path: Path) -> None:
    ruta = tmp_path / "turnos_test.db"

    config = cargar_config(entorno={"DATABASE_URL": str(ruta)})

    assert config.database_path == ruta
