"""Tests unitarios de cancelación de turno en dominio puro (C-12, RN-TUR-09, RN-TUR-10)."""

from datetime import datetime

import pytest

from app.domain.errores import TurnoNoModificable
from app.domain.models import EstadoTurno, Turno
from app.domain.reglas_turno import validar_cancelacion

LUNES = datetime(2026, 10, 19)
AHORA_FIJO = LUNES.replace(hour=9, minute=0)


def _hora(hh: int, mm: int = 0) -> datetime:
    return LUNES.replace(hour=hh, minute=mm)


def _turno(
    inicio: datetime,
    fin: datetime,
    *,
    estado: EstadoTurno = "reservado",
    id: int | None = 10,
) -> Turno:
    return Turno(
        id=id,
        paciente_id=1,
        profesional_id=1,
        sillon_id=1,
        prestacion_id=1,
        inicio=inicio,
        fin=fin,
        estado=estado,
    )


def test_cancelar_turno_futuro_devuelve_turno_en_estado_cancelado() -> None:
    turno = _turno(_hora(10, 0), _hora(10, 30))

    cancelado = validar_cancelacion(turno, ahora=AHORA_FIJO)

    assert cancelado.estado == "cancelado"
    assert cancelado.id == turno.id
    assert (cancelado.inicio, cancelado.fin) == (turno.inicio, turno.fin)
    assert turno.estado == "reservado"


def test_cancelar_turno_pasado_lanza_turno_no_modificable() -> None:
    turno_pasado = _turno(_hora(8, 30), _hora(9, 0))

    with pytest.raises(TurnoNoModificable, match="futuros"):
        validar_cancelacion(turno_pasado, ahora=AHORA_FIJO)


def test_cancelar_turno_en_el_instante_exacto_de_inicio_lanza_turno_no_modificable() -> None:
    turno_en_inicio = _turno(_hora(9, 0), _hora(9, 30))

    with pytest.raises(TurnoNoModificable, match="futuros"):
        validar_cancelacion(turno_en_inicio, ahora=AHORA_FIJO)


def test_cancelar_turno_ya_cancelado_lanza_turno_no_modificable() -> None:
    turno_cancelado = _turno(_hora(10, 0), _hora(10, 30), estado="cancelado")

    with pytest.raises(TurnoNoModificable, match="cancelado"):
        validar_cancelacion(turno_cancelado, ahora=AHORA_FIJO)
