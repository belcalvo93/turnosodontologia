"""Conversión del instante del reloj a hora local del consultorio (C-11, D3)."""

from datetime import UTC, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.api.dependencias import a_hora_local
from tests.conftest import RelojFijo

ZONA_CONSULTORIO = "America/Argentina/Buenos_Aires"


def test_a_hora_local_convierte_utc_a_buenos_aires_sin_tzinfo() -> None:
    instante = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)

    local = a_hora_local(instante, ZONA_CONSULTORIO)

    assert local == datetime(2026, 1, 5, 9, 0)
    assert local.tzinfo is None


def test_a_hora_local_cambia_de_dia_al_convertir() -> None:
    instante = datetime(2026, 1, 6, 2, 30, tzinfo=UTC)

    local = a_hora_local(instante, ZONA_CONSULTORIO)

    assert local == datetime(2026, 1, 5, 23, 30)
    assert local.tzinfo is None


def test_a_hora_local_con_otra_zona_de_origen_convierte_al_mismo_instante() -> None:
    instante = datetime(2026, 1, 5, 14, 0, tzinfo=timezone(timedelta(hours=2)))

    local = a_hora_local(instante, ZONA_CONSULTORIO)

    assert local == datetime(2026, 1, 5, 9, 0)
    assert local.tzinfo is None


def test_obtener_ahora_local_devuelve_la_hora_local_del_reloj_fijo(
    cliente_con_rutas_prueba: TestClient,
) -> None:
    respuesta = cliente_con_rutas_prueba.get("/prueba/ahora-local")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"ahora_local": "2026-01-05T09:00:00"}


def test_obtener_ahora_local_sigue_al_reloj_cuando_avanza(
    cliente_con_rutas_prueba: TestClient, reloj: RelojFijo
) -> None:
    reloj.avanzar(minutes=90)

    respuesta = cliente_con_rutas_prueba.get("/prueba/ahora-local")

    assert respuesta.json() == {"ahora_local": "2026-01-05T10:30:00"}
