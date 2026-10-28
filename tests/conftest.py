"""Fixtures compartidas de la suite: configuración, reloj, usuarios y clientes HTTP (C-01, C-03)."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.seguridad import emitir_token, hashear
from app.config import Config, cargar_config
from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio import insertar_usuario
from app.domain.usuarios import Rol, Usuario
from app.main import create_app
from tests.api.rutas_prueba import router as router_prueba

# Instante fijo de arranque del reloj de los tests: ningún test depende de la hora real.
INSTANTE_INICIAL = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
# Contraseña ficticia por defecto de los usuarios de test (nunca una credencial real).
CLAVE_FICTICIA = "clave-ficticia-123"


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


@pytest.fixture
def crear_usuario(config: Config) -> Callable[..., Usuario]:
    """Inserta un usuario ficticio con el hash real de su contraseña y lo devuelve."""
    inicializar_esquema(config.database_path)

    def _crear(
        username: str,
        *,
        password: str = CLAVE_FICTICIA,
        rol: Rol = Rol.RECEPCION,
        profesional_id: int | None = None,
        activo: bool = True,
    ) -> Usuario:
        conexion = abrir_conexion(config.database_path)
        try:
            with transaccion(conexion):
                id_usuario = insertar_usuario(
                    conexion,
                    username=username,
                    password_hash=hashear(password),
                    rol=rol,
                    profesional_id=profesional_id,
                    activo=activo,
                )
        finally:
            conexion.close()
        return Usuario(
            id=id_usuario, username=username, rol=rol, profesional_id=profesional_id, activo=activo
        )

    return _crear


@pytest.fixture
def token_de(config: Config, reloj: RelojFijo) -> Callable[[Usuario], str]:
    """Emite un token para `usuario` en el instante actual del reloj fijo."""

    def _emitir(usuario: Usuario) -> str:
        return emitir_token(usuario, config, ahora=reloj())

    return _emitir
