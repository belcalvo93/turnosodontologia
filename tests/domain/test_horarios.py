from datetime import time
import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import (
    HorarioAtencion,
    validar_datos_horario,
    validar_franjas_no_superpuestas,
    validar_horario_no_solapa,
)


def test_validar_datos_horario_con_datos_validos() -> None:
    horario = validar_datos_horario(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    assert horario.profesional_id == 1
    assert horario.dia_semana == 0
    assert horario.hora_desde == time(9, 0)
    assert horario.hora_hasta == time(13, 0)
    assert horario.id is None


@pytest.mark.parametrize("dia_invalido", [-1, 7, 10])
def test_validar_datos_horario_con_dia_semana_invalido_lanza_dato_invalido(
    dia_invalido: int,
) -> None:
    with pytest.raises(DatoInvalido, match="día de la semana"):
        validar_datos_horario(
            profesional_id=1,
            dia_semana=dia_invalido,
            hora_desde=time(9, 0),
            hora_hasta=time(13, 0),
        )


@pytest.mark.parametrize(
    ("hora_desde", "hora_hasta"),
    [
        (time(13, 0), time(9, 0)),
        (time(10, 0), time(10, 0)),
    ],
)
def test_validar_datos_horario_con_franja_invertida_o_igual_lanza_dato_invalido(
    hora_desde: time, hora_hasta: time
) -> None:
    with pytest.raises(DatoInvalido, match="anterior"):
        validar_datos_horario(
            profesional_id=1,
            dia_semana=0,
            hora_desde=hora_desde,
            hora_hasta=hora_hasta,
        )


def test_dos_franjas_en_el_mismo_dia_disjuntas_son_validas() -> None:
    f1 = HorarioAtencion(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    f2 = HorarioAtencion(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(14, 0),
        hora_hasta=time(18, 0),
    )
    validar_franjas_no_superpuestas([f1, f2])
    validar_horario_no_solapa(f2, [f1])


def test_dos_franjas_en_el_mismo_dia_contiguas_son_validas() -> None:
    f1 = HorarioAtencion(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    f2 = HorarioAtencion(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(13, 0),
        hora_hasta=time(17, 0),
    )
    validar_franjas_no_superpuestas([f1, f2])
    validar_horario_no_solapa(f2, [f1])


def test_dos_franjas_en_el_mismo_dia_superpuestas_lanzan_dato_invalido() -> None:
    f1 = HorarioAtencion(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    f2 = HorarioAtencion(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(12, 0),
        hora_hasta=time(15, 0),
    )
    with pytest.raises(DatoInvalido, match="superponer"):
        validar_franjas_no_superpuestas([f1, f2])

    with pytest.raises(DatoInvalido, match="superpone"):
        validar_horario_no_solapa(f2, [f1])


def test_franjas_en_dias_distintos_con_mismo_horario_son_validas() -> None:
    lunes = HorarioAtencion(
        profesional_id=1,
        dia_semana=0,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    martes = HorarioAtencion(
        profesional_id=1,
        dia_semana=1,
        hora_desde=time(9, 0),
        hora_hasta=time(13, 0),
    )
    validar_franjas_no_superpuestas([lunes, martes])
    validar_horario_no_solapa(martes, [lunes])
