"""Tests de las dependencias de la API sobre rutas de prueba (C-03)."""

import sqlite3
from datetime import UTC, datetime, tzinfo

import pytest
from fastapi.testclient import TestClient

from app.config import Config
from app.main import create_app
from tests.conftest import INSTANTE_INICIAL, RelojFijo


def _conexion_usada(cliente: TestClient) -> sqlite3.Connection:
    conexion: sqlite3.Connection = cliente.app.state.conexion_prueba  # type: ignore[attr-defined]
    return conexion


def test_la_ruta_consulta_la_base_configurada_sin_error_de_hilo(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.get("/prueba/conexion")

    assert respuesta.status_code == 200
    assert "usuario" in respuesta.json()["tablas"]


def test_la_conexion_queda_cerrada_despues_del_request(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    cliente_con_rutas_prueba.get("/prueba/conexion")

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        _conexion_usada(cliente_con_rutas_prueba).execute("SELECT 1")


def test_la_conexion_se_cierra_aunque_el_endpoint_falle(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.get("/prueba/conexion/error")

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "sin_permiso"
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        _conexion_usada(cliente_con_rutas_prueba).execute("SELECT 1")


def test_cada_request_recibe_su_propia_conexion(cliente_con_rutas_prueba: TestClient) -> None:
    cliente_con_rutas_prueba.get("/prueba/conexion")
    primera = _conexion_usada(cliente_con_rutas_prueba)

    cliente_con_rutas_prueba.get("/prueba/conexion")

    assert _conexion_usada(cliente_con_rutas_prueba) is not primera


def test_obtener_ahora_devuelve_el_instante_del_reloj_fijo(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.get("/prueba/ahora")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"ahora": "2026-01-05T12:00:00+00:00"}


def test_obtener_ahora_sigue_al_reloj_cuando_avanza(
    cliente_con_rutas_prueba: TestClient, reloj: RelojFijo
) -> None:
    reloj.avanzar(minutes=59)

    respuesta = cliente_con_rutas_prueba.get("/prueba/ahora")

    assert respuesta.json() == {"ahora": "2026-01-05T12:59:00+00:00"}


def test_el_cliente_sin_rutas_de_prueba_tambien_usa_el_reloj_fijo(
    cliente: TestClient, reloj: RelojFijo
) -> None:
    assert cliente.app.state.reloj is reloj  # type: ignore[attr-defined]


def test_sin_reloj_inyectado_la_app_usa_datetime_now_en_utc(
    config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Un doble de `datetime` en app.main: verifica el reloj por defecto sin leer la hora real.
    zonas_pedidas: list[tzinfo | None] = []

    class DatetimeFalso(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            zonas_pedidas.append(tz)
            return INSTANTE_INICIAL

    monkeypatch.setattr("app.main.datetime", DatetimeFalso)

    assert create_app(config).state.reloj() == INSTANTE_INICIAL
    assert zonas_pedidas == [UTC]
