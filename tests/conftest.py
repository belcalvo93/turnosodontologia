"""Fixtures compartidas de la suite: configuración y cliente HTTP (C-01)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Config, cargar_config
from app.main import create_app


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
