from collections.abc import Sequence
from datetime import datetime, time

import pytest

from app.domain.errores import FueraDeHorario
from app.domain.models import HorarioAtencion, Prestacion, Turno
from app.domain.reglas_turno import validar_alta

# Datos ficticios (RN-PAC-03)
LUNES = datetime(2026, 10, 19)
ODONTOLOGO_FICTICIO_A = 1
SILLON_1 = 1
PACIENTE_FICTICIO_1 = 1  # DNI "00000001 (ficticio)"

CONSULTA_FICTICIA = Prestacion(id=1, nombre="Consulta ficticia", duracion_minutos=30)
LIMPIEZA_FICTICIA = Prestacion(id=2, nombre="Limpieza ficticia", duracion_minutos=45)

HORARIO_LUNES = [
    HorarioAtencion(
        profesional_id=ODONTOLOGO_FICTICIO_A,
        dia_semana=0,
        hora_desde=time(9),
        hora_hasta=time(13),
    )
]


def _hora(hh: int, mm: int = 0) -> datetime:
    return LUNES.replace(hour=hh, minute=mm)


def _validar(
    inicio: datetime,
    prestacion: Prestacion = CONSULTA_FICTICIA,
    horarios: Sequence[HorarioAtencion] = HORARIO_LUNES,
) -> Turno:
    return validar_alta(
        inicio=inicio,
        prestacion=prestacion,
        profesional_id=ODONTOLOGO_FICTICIO_A,
        sillon_id=SILLON_1,
        paciente_id=PACIENTE_FICTICIO_1,
        horarios=horarios,
        bloqueos=[],
        turnos_activos=[],
    )


def test_fin_se_calcula_con_prestacion_de_30_minutos() -> None:
    turno = _validar(_hora(10), CONSULTA_FICTICIA)
    assert turno.inicio == _hora(10)
    assert turno.fin == _hora(10, 30)


def test_fin_se_calcula_con_prestacion_de_45_minutos() -> None:
    turno = _validar(_hora(10), LIMPIEZA_FICTICIA)
    assert turno.fin == _hora(10, 45)
    assert turno.prestacion_id == LIMPIEZA_FICTICIA.id


def test_turno_armado_queda_reservado_con_los_recursos_pedidos() -> None:
    turno = _validar(_hora(10))
    assert turno.estado == "reservado"
    assert turno.id is None
    assert (turno.profesional_id, turno.sillon_id, turno.paciente_id) == (
        ODONTOLOGO_FICTICIO_A,
        SILLON_1,
        PACIENTE_FICTICIO_1,
    )


def test_franja_turno_que_termina_justo_al_cierre_se_acepta() -> None:
    turno = _validar(_hora(12, 30))
    assert turno.fin == _hora(13)


def test_franja_turno_que_excede_el_cierre_lanza_fuera_de_horario() -> None:
    with pytest.raises(FueraDeHorario):
        _validar(_hora(12, 45))


def test_franja_turno_que_empieza_antes_de_la_apertura_lanza_fuera_de_horario() -> None:
    with pytest.raises(FueraDeHorario):
        _validar(_hora(8, 45))


def test_franja_turno_en_dia_sin_horario_lanza_fuera_de_horario() -> None:
    martes_10 = datetime(2026, 10, 20, 10)
    with pytest.raises(FueraDeHorario):
        _validar(martes_10)


def test_franja_turno_que_cruza_el_corte_entre_manana_y_tarde_lanza_fuera_de_horario() -> None:
    manana_y_tarde = [
        *HORARIO_LUNES,
        HorarioAtencion(
            profesional_id=ODONTOLOGO_FICTICIO_A,
            dia_semana=0,
            hora_desde=time(14),
            hora_hasta=time(18),
        ),
    ]
    assert _validar(_hora(14), horarios=manana_y_tarde).fin == _hora(14, 30)
    with pytest.raises(FueraDeHorario):
        _validar(_hora(12, 45), horarios=manana_y_tarde)


def test_franja_horario_de_otro_profesional_no_habilita_el_turno() -> None:
    horario_de_otro = [
        HorarioAtencion(
            profesional_id=ODONTOLOGO_FICTICIO_A + 1,
            dia_semana=0,
            hora_desde=time(9),
            hora_hasta=time(13),
        )
    ]
    with pytest.raises(FueraDeHorario):
        _validar(_hora(10), horarios=horario_de_otro)
