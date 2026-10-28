"""Fixtures compartidas de la suite: configuración y clientes HTTP (C-01, C-03)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Config, cargar_config
from app.main import create_app
from tests.api.rutas_prueba import router as router_prueba


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """Configuración de test con una base SQLite temporal por test."""
    return cargar_config(
        entorno={
            "APP_ENV": "test",
            "DATABASE_URL": str(tmp_path / "turnos_test.db"),
        }
    )


@pytest.fixture
def cliente(config: Config) -> Iterator[TestClient]:
    """Cliente HTTP sobre una app de test.

    Se usa como context manager para que FastAPI dispare el lifespan
    (aplicación del esquema) cuando exista.
    """
    with TestClient(create_app(config)) as cliente_http:
        yield cliente_http


@pytest.fixture
def cliente_con_rutas_prueba(config: Config) -> Iterator[TestClient]:
    """Cliente HTTP sobre una app de test con el router de `tests/api/rutas_prueba.py`."""
    aplicacion = create_app(config)
    aplicacion.include_router(router_prueba)
    with TestClient(aplicacion) as cliente_http:
        yield cliente_http
