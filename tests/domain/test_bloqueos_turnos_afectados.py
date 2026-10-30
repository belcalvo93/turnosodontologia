"""Tests de turnos_afectados_por_bloqueo en dominio puro (C-16, RN-TUR-04/05/08)."""

import inspect
from collections.abc import Sequence
from datetime import datetime

from app.domain.models import Bloqueo, Turno
from app.domain.reglas_turno import turnos_afectados_por_bloqueo

# Datos ficticios (RN-PAC-03)
LUNES = datetime(2026, 10, 19)
ODONTOLOGO_FICTICIO_A = 1
ODONTOLOGO_FICTICIO_B = 2
SILLON_1 = 1
SILLON_2 = 2
PACIENTE_FICTICIO_1 = 1  # DNI "00000001 (ficticio)"
PACIENTE_FICTICIO_2 = 2  # DNI "00000002 (ficticio)"
PACIENTE_FICTICIO_3 = 3  # DNI "00000003 (ficticio)"
CONSULTA_FICTICIA = 1


def _hora(hh: int, mm: int = 0) -> datetime:
    return LUNES.replace(hour=hh, minute=mm)


def _turno(
    inicio: datetime,
    fin: datetime,
    *,
    profesional_id: int = ODONTOLOGO_FICTICIO_A,
    sillon_id: int = SILLON_1,
    estado: str = "reservado",
    id: int | None = None,
) -> Turno:
    return Turno(
        id=id,
        paciente_id=PACIENTE_FICTICIO_1,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion_id=CONSULTA_FICTICIA,
        inicio=inicio,
        fin=fin,
        estado=estado,
    )


def _bloqueo(
    inicio: datetime,
    fin: datetime,
    *,
    alcance: str = "profesional",
    recurso_id: int = ODONTOLOGO_FICTICIO_A,
) -> Bloqueo:
    return Bloqueo(
        alcance=alcance,
        recurso_id=recurso_id,
        inicio=inicio,
        fin=fin,
        motivo="Motivo ficticio",
    )


def test_reporta_turno_reservado_que_solapa_parcialmente() -> None:
    bloqueo = _bloqueo(_hora(9), _hora(10))
    turno = _turno(_hora(9, 30), _hora(10, 30))

    afectados = turnos_afectados_por_bloqueo(bloqueo, [turno])

    assert afectados == [turno]


def test_bloqueo_de_profesional_excluye_turnos_de_otro_profesional() -> None:
    bloqueo = _bloqueo(_hora(9), _hora(10), alcance="profesional", recurso_id=ODONTOLOGO_FICTICIO_A)
    turno_propio = _turno(_hora(9, 30), _hora(10, 30))
    turno_ajeno = _turno(
        _hora(9, 30), _hora(10, 30), profesional_id=ODONTOLOGO_FICTICIO_B
    )

    afectados = turnos_afectados_por_bloqueo(bloqueo, [turno_propio, turno_ajeno])

    assert afectados == [turno_propio]


def test_bloqueo_de_sillon_excluye_turnos_de_otro_sillon_y_de_otro_profesional() -> None:
    bloqueo = _bloqueo(_hora(9), _hora(10), alcance="sillon", recurso_id=SILLON_1)
    turno_sillon_propio = _turno(_hora(9, 30), _hora(10, 30))
    turno_otro_sillon = _turno(_hora(9, 30), _hora(10, 30), sillon_id=SILLON_2)
    turno_otro_profesional_sillon_ajeno = _turno(
        _hora(9, 30), _hora(10, 30), profesional_id=ODONTOLOGO_FICTICIO_B, sillon_id=SILLON_2
    )
    turnos: Sequence[Turno] = [
        turno_sillon_propio,
        turno_otro_sillon,
        turno_otro_profesional_sillon_ajeno,
    ]

    afectados = turnos_afectados_por_bloqueo(bloqueo, turnos)

    assert afectados == [turno_sillon_propio]


def test_turnos_contiguos_al_bloqueo_no_se_reportan() -> None:
    bloqueo = _bloqueo(_hora(10), _hora(13))
    turno_termina_en_borde = _turno(_hora(8), _hora(10))
    turno_empieza_en_borde = _turno(_hora(13), _hora(15))

    afectados = turnos_afectados_por_bloqueo(
        bloqueo, [turno_termina_en_borde, turno_empieza_en_borde]
    )

    assert afectados == []


def test_turnos_cancelados_no_se_reportan() -> None:
    bloqueo = _bloqueo(_hora(9), _hora(13))
    turno_reservado_1 = _turno(_hora(9, 30), _hora(10), id=1)
    turno_reservado_2 = _turno(_hora(10), _hora(10, 30), id=2)
    turno_cancelado = _turno(_hora(11), _hora(11, 30), estado="cancelado", id=3)

    afectados = turnos_afectados_por_bloqueo(
        bloqueo, [turno_reservado_1, turno_reservado_2, turno_cancelado]
    )

    assert afectados == [turno_reservado_1, turno_reservado_2]


def test_ordena_por_inicio_ascendente() -> None:
    bloqueo = _bloqueo(_hora(9), _hora(13))
    turno_11 = _turno(_hora(11), _hora(11, 30), id=3)
    turno_10 = _turno(_hora(10), _hora(10, 30), id=2)
    turno_10_30 = _turno(_hora(10, 30), _hora(11), id=1)
    turnos: Sequence[Turno] = [turno_11, turno_10, turno_10_30]

    afectados = turnos_afectados_por_bloqueo(bloqueo, turnos)

    assert afectados == [turno_10, turno_10_30, turno_11]


def test_desempata_por_id_ascendente_con_inicio_igual() -> None:
    bloqueo = _bloqueo(_hora(9), _hora(13))
    turno_id_7 = _turno(_hora(10), _hora(10, 30), id=7)
    turno_id_3 = _turno(_hora(10), _hora(10, 30), id=3)

    afectados = turnos_afectados_por_bloqueo(bloqueo, [turno_id_7, turno_id_3])

    assert afectados == [turno_id_3, turno_id_7]


def test_no_depende_del_reloj() -> None:
    firma = inspect.signature(turnos_afectados_por_bloqueo)
    assert list(firma.parameters) == ["bloqueo", "turnos"]

    # Un bloqueo retroactivo también lista los turnos reservados del período (D-A3).
    bloqueo_pasado = _bloqueo(datetime(2020, 3, 2, 9), datetime(2020, 3, 2, 13))
    turno_pasado = _turno(datetime(2020, 3, 2, 9, 30), datetime(2020, 3, 2, 10))

    afectados = turnos_afectados_por_bloqueo(bloqueo_pasado, [turno_pasado])

    assert afectados == [turno_pasado]
