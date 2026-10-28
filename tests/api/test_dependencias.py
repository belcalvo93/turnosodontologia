"""Tests de las dependencias de la API sobre rutas de prueba (C-03)."""

import sqlite3

import pytest
from fastapi.testclient import TestClient


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
