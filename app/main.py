"""Aplicación FastAPI: crea la app y monta los routers (C-01)."""

from fastapi import FastAPI

from app.api.salud import router as router_salud
from app.config import Config, cargar_config


def create_app(config: Config | None = None) -> FastAPI:
    """Crea la app con su configuración y los routers de la API."""
    aplicacion = FastAPI(title="Turnos Odontológicos")
    aplicacion.state.config = config if config is not None else cargar_config()
    aplicacion.include_router(router_salud)
    return aplicacion


app = create_app()
