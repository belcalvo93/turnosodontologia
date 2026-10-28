"""Tests del armado de la aplicación (C-01, C-03)."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Config, cargar_config
from app.main import app, create_app


def test_create_app_guarda_la_config_y_monta_health(tmp_path: Path) -> None:
    config = cargar_config(entorno={"DATABASE_URL": str(tmp_path / "turnos_test.db")})

    aplicacion = create_app(config)

    assert isinstance(aplicacion, FastAPI)
    assert aplicacion.state.config == config
    respuesta = TestClient(aplicacion).get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_existe_una_app_a_nivel_modulo() -> None:
    assert isinstance(app, FastAPI)
    assert isinstance(app.state.config, Config)


def test_arranque_inicializa_el_esquema(config: Config, cliente: TestClient) -> None:
    assert config.database_path.exists()
    assert cliente.get("/health").status_code == 200


_RUTAS_DE_DOCUMENTACION = ("/docs", "/redoc", "/openapi.json")


def _cliente_en_entorno(tmp_path: Path, app_env: str) -> TestClient:
    config = cargar_config(
        entorno={
            "APP_ENV": app_env,
            "DATABASE_URL": str(tmp_path / f"{app_env}.db"),
            "JWT_SECRET": "secreto-ficticio-de-test-con-32-caracteres-o-mas",
        }
    )
    return TestClient(create_app(config))


@pytest.mark.parametrize("ruta", _RUTAS_DE_DOCUMENTACION)
def test_documentacion_disponible_en_development(tmp_path: Path, ruta: str) -> None:
    with _cliente_en_entorno(tmp_path, "development") as cliente_dev:
        assert cliente_dev.get(ruta).status_code == 200


@pytest.mark.parametrize("app_env", ["test", "production"])
@pytest.mark.parametrize("ruta", _RUTAS_DE_DOCUMENTACION)
def test_documentacion_oculta_fuera_de_development(
    tmp_path: Path, app_env: str, ruta: str
) -> None:
    with _cliente_en_entorno(tmp_path, app_env) as cliente_entorno:
        assert cliente_entorno.get(ruta).status_code == 404
