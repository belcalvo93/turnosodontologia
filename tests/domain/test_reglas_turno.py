from collections.abc import Sequence
from datetime import datetime, time

import pytest

from app.domain.errores import ConflictoAgenda, DentroDeBloqueo, FueraDeHorario
from app.domain.models import Bloqueo, EstadoTurno, HorarioAtencion, Prestacion, Turno
from app.domain.reglas_turno import validar_alta

# Datos ficticios (RN-PAC-03)
LUNES = datetime(2026, 10, 19)
ODONTOLOGO_FICTICIO_A = 1
ODONTOLOGO_FICTICIO_B = 2
SILLON_1 = 1
SILLON_2 = 2
PACIENTE_FICTICIO_1 = 1  # DNI "00000001 (ficticio)"
PACIENTE_FICTICIO_2 = 2  # DNI "00000002 (ficticio)"

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
    sillon_id: int = SILLON_1,
    bloqueos: Sequence[Bloqueo] = (),
    turnos_activos: Sequence[Turno] = (),
    excluir_turno_id: int | None = None,
) -> Turno:
    return validar_alta(
        inicio=inicio,
        prestacion=prestacion,
        profesional_id=ODONTOLOGO_FICTICIO_A,
        sillon_id=sillon_id,
        paciente_id=PACIENTE_FICTICIO_1,
        horarios=horarios,
        bloqueos=bloqueos,
        turnos_activos=turnos_activos,
        excluir_turno_id=excluir_turno_id,
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


MANTENIMIENTO_SILLON_1 = Bloqueo(
    alcance="sillon",
    recurso_id=SILLON_1,
    inicio=_hora(10),
    fin=_hora(12),
    motivo="Mantenimiento ficticio",
)


def test_bloqueo_de_sillon_rechaza_turno_en_ese_sillon() -> None:
    with pytest.raises(DentroDeBloqueo):
        _validar(_hora(11), sillon_id=SILLON_1, bloqueos=[MANTENIMIENTO_SILLON_1])


def test_bloqueo_de_sillon_no_afecta_a_otro_sillon() -> None:
    turno = _validar(_hora(11), sillon_id=SILLON_2, bloqueos=[MANTENIMIENTO_SILLON_1])
    assert turno.sillon_id == SILLON_2


def test_bloqueo_de_sillon_acepta_turno_contiguo_al_fin_del_bloqueo() -> None:
    turno = _validar(_hora(12), sillon_id=SILLON_1, bloqueos=[MANTENIMIENTO_SILLON_1])
    assert turno.inicio == _hora(12)


def test_bloqueo_de_profesional_rechaza_turno_en_cualquier_sillon() -> None:
    vacaciones = Bloqueo(
        alcance="profesional",
        recurso_id=ODONTOLOGO_FICTICIO_A,
        inicio=_hora(9),
        fin=_hora(13),
        motivo="Vacaciones ficticias",
    )
    with pytest.raises(DentroDeBloqueo):
        _validar(_hora(11), sillon_id=SILLON_2, bloqueos=[vacaciones])


def test_bloqueo_de_otro_profesional_no_afecta() -> None:
    vacaciones_de_otro = Bloqueo(
        alcance="profesional",
        recurso_id=ODONTOLOGO_FICTICIO_A + 1,
        inicio=_hora(9),
        fin=_hora(13),
        motivo="Vacaciones ficticias",
    )
    turno = _validar(_hora(11), bloqueos=[vacaciones_de_otro])
    assert turno.inicio == _hora(11)


def _turno_activo(
    inicio: datetime,
    fin: datetime,
    *,
    profesional_id: int = ODONTOLOGO_FICTICIO_B,
    sillon_id: int = SILLON_2,
    paciente_id: int = PACIENTE_FICTICIO_2,
    estado: EstadoTurno = "reservado",
    id: int | None = 100,
) -> Turno:
    """Turno existente; por defecto no comparte ningún recurso con la solicitud."""
    return Turno(
        id=id,
        paciente_id=paciente_id,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion_id=CONSULTA_FICTICIA.id,
        inicio=inicio,
        fin=fin,
        estado=estado,
    )


def test_solapamiento_del_profesional_lanza_conflicto_agenda() -> None:
    existente = _turno_activo(
        _hora(10), _hora(10, 30), profesional_id=ODONTOLOGO_FICTICIO_A, sillon_id=SILLON_1
    )
    with pytest.raises(ConflictoAgenda):
        _validar(_hora(10, 15), sillon_id=SILLON_2, turnos_activos=[existente])


def test_solapamiento_del_sillon_lanza_conflicto_agenda() -> None:
    existente = _turno_activo(_hora(10), _hora(10, 30), sillon_id=SILLON_1)
    with pytest.raises(ConflictoAgenda):
        _validar(_hora(10, 15), sillon_id=SILLON_1, turnos_activos=[existente])


def test_solapamiento_del_paciente_lanza_conflicto_agenda() -> None:
    existente = _turno_activo(_hora(10), _hora(10, 30), paciente_id=PACIENTE_FICTICIO_1)
    with pytest.raises(ConflictoAgenda):
        _validar(_hora(10, 15), sillon_id=SILLON_1, turnos_activos=[existente])


def test_solapamiento_sin_recursos_compartidos_se_acepta() -> None:
    existente = _turno_activo(_hora(10), _hora(10, 30))
    turno = _validar(_hora(10, 15), sillon_id=SILLON_1, turnos_activos=[existente])
    assert turno.inicio == _hora(10, 15)


def test_contiguo_mismo_profesional_y_sillon_se_acepta() -> None:
    existente = _turno_activo(
        _hora(10), _hora(10, 30), profesional_id=ODONTOLOGO_FICTICIO_A, sillon_id=SILLON_1
    )
    turno = _validar(_hora(10, 30), sillon_id=SILLON_1, turnos_activos=[existente])
    assert turno.fin == _hora(11)


def test_cancelado_que_se_superpone_no_genera_conflicto() -> None:
    cancelado = _turno_activo(
        _hora(10),
        _hora(10, 30),
        profesional_id=ODONTOLOGO_FICTICIO_A,
        sillon_id=SILLON_1,
        estado="cancelado",
    )
    turno = _validar(_hora(10), sillon_id=SILLON_1, turnos_activos=[cancelado])
    assert turno.inicio == _hora(10)


def test_excluir_turno_id_ignora_el_propio_turno() -> None:
    propio = _turno_activo(
        _hora(10), _hora(10, 30), profesional_id=ODONTOLOGO_FICTICIO_A, sillon_id=SILLON_1, id=7
    )
    turno = _validar(
        _hora(10, 15), sillon_id=SILLON_1, turnos_activos=[propio], excluir_turno_id=7
    )
    assert turno.inicio == _hora(10, 15)


def test_excluir_turno_id_no_oculta_conflicto_con_otro_turno() -> None:
    otro = _turno_activo(
        _hora(10), _hora(10, 30), profesional_id=ODONTOLOGO_FICTICIO_A, sillon_id=SILLON_1, id=8
    )
    with pytest.raises(ConflictoAgenda):
        _validar(_hora(10, 15), sillon_id=SILLON_1, turnos_activos=[otro], excluir_turno_id=7)


def test_solapamiento_con_turno_sin_id_y_sin_excluir_lanza_conflicto_agenda() -> None:
    sin_id = _turno_activo(
        _hora(10), _hora(10, 30), profesional_id=ODONTOLOGO_FICTICIO_A, id=None
    )
    with pytest.raises(ConflictoAgenda):
        _validar(_hora(10, 15), turnos_activos=[sin_id])
