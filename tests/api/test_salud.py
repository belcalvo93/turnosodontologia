"""Tests del endpoint de salud (C-01)."""

from fastapi.testclient import TestClient


def test_health_responde_200_sin_autenticacion(cliente: TestClient) -> None:
    respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}
