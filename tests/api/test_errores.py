"""Tests del formato global de errores {codigo, mensaje, detalles?} (C-03, RN-GLO-01)."""

import pytest
from fastapi.testclient import TestClient

from tests.api.rutas_prueba import (
    MENSAJE_CONFLICTO_AGENDA,
    MENSAJE_DATO_INVALIDO,
    MENSAJE_DENTRO_DE_BLOQUEO,
    MENSAJE_FUERA_DE_HORARIO,
)


@pytest.mark.parametrize(
    ("ruta", "status", "codigo", "mensaje"),
    [
        ("/prueba/error/conflicto-agenda", 409, "conflicto_agenda", MENSAJE_CONFLICTO_AGENDA),
        ("/prueba/error/fuera-de-horario", 409, "fuera_de_horario", MENSAJE_FUERA_DE_HORARIO),
        ("/prueba/error/dentro-de-bloqueo", 409, "dentro_de_bloqueo", MENSAJE_DENTRO_DE_BLOQUEO),
        ("/prueba/error/dato-invalido", 422, "dato_invalido", MENSAJE_DATO_INVALIDO),
    ],
)
def test_error_de_dominio_responde_su_status_con_codigo_y_mensaje(
    cliente_con_rutas_prueba: TestClient, ruta: str, status: int, codigo: str, mensaje: str
) -> None:
    respuesta = cliente_con_rutas_prueba.get(ruta)

    assert respuesta.status_code == status
    assert respuesta.json() == {"codigo": codigo, "mensaje": mensaje}
