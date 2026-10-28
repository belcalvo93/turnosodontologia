"""Fixtures compartidas de la suite: configuración, reloj y clientes HTTP (C-01, C-03)."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Config, cargar_config
from app.main import create_app
from tests.api.rutas_prueba import router as router_prueba

# Instante fijo de arranque del reloj de los tests: ningún test depende de la hora real.
INSTANTE_INICIAL = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)


class RelojFijo:
    """Reloj que solo se mueve con `avanzar(...)`; se inyecta en `create_app(reloj=...)`."""

    def __init__(self, inicio: datetime = INSTANTE_INICIAL) -> None:
        self._ahora = inicio

    def __call__(self) -> datetime:
        return self._ahora

    def avanzar(self, *, minutes: int) -> None:
        self._ahora += timedelta(minutes=minutes)


@pytest.fixture
def reloj() -> RelojFijo:
    return RelojFijo()


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
def cliente(config: Config, reloj: RelojFijo) -> Iterator[TestClient]:
    """Cliente HTTP sobre una app de test.

    Se usa como context manager para que FastAPI dispare el lifespan
    (aplicación del esquema) cuando exista.
    """
    with TestClient(create_app(config, reloj=reloj)) as cliente_http:
        yield cliente_http


@pytest.fixture
def cliente_con_rutas_prueba(config: Config, reloj: RelojFijo) -> Iterator[TestClient]:
    """Cliente HTTP sobre una app de test con el router de `tests/api/rutas_prueba.py`."""
    aplicacion = create_app(config, reloj=reloj)
    aplicacion.include_router(router_prueba)
    with TestClient(aplicacion) as cliente_http:
        yield cliente_http
