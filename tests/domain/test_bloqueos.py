"""Tests unitarios de Bloqueo y validación en dominio puro (C-09, RN-REC-02)."""

from datetime import UTC, datetime

import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import Bloqueo, validar_datos_bloqueo


def test_validar_datos_bloqueo_con_datos_validos_construye_bloqueo() -> None:
    inicio = datetime(2026, 11, 10, 9, 0)
    fin = datetime(2026, 11, 10, 13, 0)

    bloqueo = validar_datos_bloqueo(
        alcance="profesional",
        recurso_id=1,
        inicio=inicio,
        fin=fin,
        motivo="  Vacaciones  ",
    )

    assert bloqueo == Bloqueo(
        id=None,
        alcance="profesional",
        recurso_id=1,
        inicio=inicio,
        fin=fin,
        motivo="Vacaciones",
    )


@pytest.mark.parametrize(
    ("inicio", "fin"),
    [
        (datetime(2026, 11, 10, 10, 0), datetime(2026, 11, 10, 10, 0)),
        (datetime(2026, 11, 10, 12, 0), datetime(2026, 11, 10, 10, 0)),
    ],
)
def test_validar_datos_bloqueo_con_inicio_mayor_o_igual_que_fin_lanza_dato_invalido(
    inicio: datetime, fin: datetime
) -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_bloqueo(
            alcance="sillon",
            recurso_id=1,
            inicio=inicio,
            fin=fin,
            motivo="Mantenimiento",
        )


def test_validar_datos_bloqueo_con_alcance_invalido_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_bloqueo(
            alcance="consultorio",
            recurso_id=1,
            inicio=datetime(2026, 11, 10, 9, 0),
            fin=datetime(2026, 11, 10, 13, 0),
        )


def test_validar_datos_bloqueo_con_zona_horaria_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_bloqueo(
            alcance="profesional",
            recurso_id=1,
            inicio=datetime(2026, 11, 10, 9, 0, tzinfo=UTC),
            fin=datetime(2026, 11, 10, 13, 0, tzinfo=UTC),
        )
