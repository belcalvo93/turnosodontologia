"""Aplicación FastAPI: crea la app, aplica el esquema y monta los routers (C-01)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.salud import router as router_salud
from app.config import Config, cargar_config
from app.db.conexion import inicializar_esquema


def create_app(config: Config | None = None) -> FastAPI:
    """Crea la app con su configuración y los routers de la API."""
    config_app = config if config is not None else cargar_config()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Aplica el esquema antes de atender requests."""
        inicializar_esquema(config_app.database_path)
        yield

    aplicacion = FastAPI(title="Turnos Odontológicos", lifespan=lifespan)
    aplicacion.state.config = config_app
    aplicacion.include_router(router_salud)
    return aplicacion


app = create_app()
