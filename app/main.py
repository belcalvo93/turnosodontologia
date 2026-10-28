"""Aplicación FastAPI: crea la app, aplica el esquema y monta los routers (C-01, C-03)."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI

from app.api.errores import registrar_manejadores
from app.api.salud import router as router_salud
from app.config import Config, cargar_config
from app.db.conexion import inicializar_esquema


def _hora_real() -> datetime:
    # Único lugar de app/ que lee la hora real; los tests inyectan un reloj fijo (design §11).
    return datetime.now(UTC)


def create_app(
    config: Config | None = None, reloj: Callable[[], datetime] | None = None
) -> FastAPI:
    """Crea la app con su configuración, su reloj y los routers de la API."""
    config_app = config if config is not None else cargar_config()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Aplica el esquema antes de atender requests."""
        inicializar_esquema(config_app.database_path)
        yield

    # /docs y /openapi.json solo en development (03 §Rutas públicas); con None no se registran.
    con_docs = config_app.app_env == "development"
    aplicacion = FastAPI(
        title="Turnos Odontológicos",
        lifespan=lifespan,
        docs_url="/docs" if con_docs else None,
        redoc_url="/redoc" if con_docs else None,
        openapi_url="/openapi.json" if con_docs else None,
    )
    aplicacion.state.config = config_app
    aplicacion.state.reloj = reloj if reloj is not None else _hora_real
    registrar_manejadores(aplicacion)
    aplicacion.include_router(router_salud)
    return aplicacion


app = create_app()
