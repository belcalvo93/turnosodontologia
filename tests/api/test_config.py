"""Tests de la configuración leída desde variables de entorno (C-01, C-03)."""

from pathlib import Path

import pytest

from app.config import ConfigInvalida, cargar_config
from app.main import create_app


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


def test_entorno_vacio_usa_defaults_de_autenticacion() -> None:
    config = cargar_config(entorno={})

    assert config.jwt_algorithm == "HS256"
    assert config.access_token_expire_minutes == 60
    assert config.seed_admin_password is None
    assert isinstance(config.jwt_secret, str)
    assert config.jwt_secret != ""


def test_jwt_secret_explicito_se_respeta_tal_cual() -> None:
    secreto = "secreto-ficticio-de-test-con-32-caracteres-o-mas"

    config = cargar_config(entorno={"JWT_SECRET": secreto})

    assert config.jwt_secret == secreto


def test_sin_jwt_secret_en_test_genera_un_secreto_aleatorio_por_carga() -> None:
    primera = cargar_config(entorno={"APP_ENV": "test"})
    segunda = cargar_config(entorno={"APP_ENV": "test"})

    assert primera.jwt_secret != ""
    assert segunda.jwt_secret != ""
    assert primera.jwt_secret != segunda.jwt_secret


def test_sin_jwt_secret_en_production_falla_nombrando_la_variable() -> None:
    with pytest.raises(ConfigInvalida, match="JWT_SECRET"):
        cargar_config(entorno={"APP_ENV": "production"})


@pytest.mark.parametrize(
    "entorno",
    [
        {"APP_ENV": "staging"},
        {"APP_ENV": "production", "JWT_SECRET": ""},
    ],
)
def test_sin_jwt_secret_fuera_de_development_y_test_falla(entorno: dict[str, str]) -> None:
    with pytest.raises(ConfigInvalida, match="JWT_SECRET"):
        cargar_config(entorno=entorno)


def test_jwt_secret_definido_en_production_se_acepta() -> None:
    secreto = "secreto-ficticio-de-produccion-con-32-caracteres"

    config = cargar_config(entorno={"APP_ENV": "production", "JWT_SECRET": secreto})

    assert config.jwt_secret == secreto


def test_create_app_no_arranca_sin_jwt_secret_en_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ConfigInvalida, match="JWT_SECRET"):
        create_app()


def test_duracion_del_token_y_password_de_seed_se_leen_del_entorno() -> None:
    config = cargar_config(
        entorno={
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            "SEED_ADMIN_PASSWORD": "clave-demo-ficticia",
        }
    )

    assert config.access_token_expire_minutes == 15
    assert config.seed_admin_password == "clave-demo-ficticia"


def test_password_de_seed_vacia_equivale_a_no_definida() -> None:
    config = cargar_config(entorno={"SEED_ADMIN_PASSWORD": ""})

    assert config.seed_admin_password is None
