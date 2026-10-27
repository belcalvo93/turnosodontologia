"""Tests del armado de la aplicación (C-01)."""

from pathlib import Path

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
