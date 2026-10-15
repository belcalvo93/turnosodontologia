from datetime import datetime, time

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


def _validar(inicio: datetime, prestacion: Prestacion = CONSULTA_FICTICIA) -> Turno:
    return validar_alta(
        inicio=inicio,
        prestacion=prestacion,
        profesional_id=ODONTOLOGO_FICTICIO_A,
        sillon_id=SILLON_1,
        paciente_id=PACIENTE_FICTICIO_1,
        horarios=HORARIO_LUNES,
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
