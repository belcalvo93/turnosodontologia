"""Tests del endpoint de salud (C-01)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.salud import router


def _cliente() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_health_responde_200_sin_autenticacion() -> None:
    respuesta = _cliente().get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}
