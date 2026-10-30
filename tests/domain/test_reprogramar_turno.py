"""Tests unitarios de reprogramación de turno en dominio puro (C-13, RN-TUR-07, RN-TUR-08, RN-TUR-09, RN-TUR-10, D-05)."""

from collections.abc import Sequence
from datetime import datetime, time

import pytest

from app.domain.errores import (
    ConflictoAgenda,
    DatoInvalido,
    DentroDeBloqueo,
    FueraDeHorario,
    TurnoNoModificable,
)
from app.domain.models import (
    Bloqueo,
    EstadoTurno,
    HorarioAtencion,
    Prestacion,
    Profesional,
    Sillon,
    Turno,
)
from app.domain.reglas_turno import validar_reprogramacion

LUNES = datetime(2026, 10, 19)
AHORA_FIJO = LUNES.replace(hour=8, minute=0)

ODONTOLOGO_A = 1
ODONTOLOGO_B = 2
SILLON_1 = 1
SILLON_2 = 2
PACIENTE_1 = 1
PACIENTE_2 = 2

CONSULTA_30 = Prestacion(id=1, nombre="Consulta ficticia", duracion_minutos=30)

HORARIOS_A = [
    HorarioAtencion(
        profesional_id=ODONTOLOGO_A,
        dia_semana=0,
        hora_desde=time(9),
        hora_hasta=time(14),
    )
]

HORARIOS_B = [
    HorarioAtencion(
        profesional_id=ODONTOLOGO_B,
        dia_semana=0,
        hora_desde=time(9),
        hora_hasta=time(14),
    )
]


def _hora(hh: int, mm: int = 0) -> datetime:
    return LUNES.replace(hour=hh, minute=mm)


def _turno(
    inicio: datetime,
    fin: datetime,
    *,
    id: int = 1,
    profesional_id: int = ODONTOLOGO_A,
    sillon_id: int = SILLON_1,
    paciente_id: int = PACIENTE_1,
    estado: EstadoTurno = "reservado",
) -> Turno:
    return Turno(
        id=id,
        paciente_id=paciente_id,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion_id=CONSULTA_30.id,
        inicio=inicio,
        fin=fin,
        estado=estado,
    )


def test_reprogramar_turno_futuro_exitoso_mantiene_id_y_recalcula_intervalo() -> None:
    turno_original = _turno(_hora(9, 0), _hora(9, 30), id=5)
    nuevo_inicio = _hora(11, 0)

    reprogramado = validar_reprogramacion(
        turno=turno_original,
        nuevo_inicio=nuevo_inicio,
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_A,
        bloqueos=[],
        turnos_activos=[turno_original],
    )

    assert reprogramado.id == 5
    assert reprogramado.inicio == _hora(11, 0)
    assert reprogramado.fin == _hora(11, 30)
    assert reprogramado.profesional_id == ODONTOLOGO_A
    assert reprogramado.sillon_id == SILLON_1
    assert reprogramado.paciente_id == PACIENTE_1
    assert reprogramado.estado == "reservado"


def test_reprogramar_turno_pasado_lanza_turno_no_modificable() -> None:
    turno_pasado = _turno(_hora(7, 0), _hora(7, 30), id=1)
    with pytest.raises(TurnoNoModificable, match="futuros"):
        validar_reprogramacion(
            turno=turno_pasado,
            nuevo_inicio=_hora(10, 0),
            ahora=AHORA_FIJO,  # 08:00
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[],
        )


def test_reprogramar_turno_en_curso_instante_exacto_lanza_turno_no_modificable() -> None:
    turno_en_curso = _turno(_hora(8, 0), _hora(8, 30), id=1)
    with pytest.raises(TurnoNoModificable, match="futuros"):
        validar_reprogramacion(
            turno=turno_en_curso,
            nuevo_inicio=_hora(10, 0),
            ahora=AHORA_FIJO,  # 08:00
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[],
        )


def test_reprogramar_turno_cancelado_lanza_turno_no_modificable() -> None:
    turno_cancelado = _turno(_hora(10, 0), _hora(10, 30), id=1, estado="cancelado")
    with pytest.raises(TurnoNoModificable, match="cancelado"):
        validar_reprogramacion(
            turno=turno_cancelado,
            nuevo_inicio=_hora(11, 0),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[],
        )


def test_reprogramar_sobre_propio_horario_anterior_no_genera_conflicto() -> None:
    # RN-TUR-08: mover de 10:00-10:30 a 10:15-10:45 se solapa consigo mismo en [10:15, 10:30)
    turno = _turno(_hora(10, 0), _hora(10, 30), id=10)
    nuevo_inicio = _hora(10, 15)

    reprogramado = validar_reprogramacion(
        turno=turno,
        nuevo_inicio=nuevo_inicio,
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_A,
        bloqueos=[],
        turnos_activos=[turno],
    )

    assert reprogramado.id == 10
    assert reprogramado.inicio == _hora(10, 15)
    assert reprogramado.fin == _hora(10, 45)


def test_reprogramar_solapa_con_otro_turno_activo_lanza_conflicto_agenda() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    otro_turno = _turno(_hora(10, 0), _hora(10, 30), id=2)

    with pytest.raises(ConflictoAgenda):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(10, 15),  # solapa con otro_turno en [10:15, 10:30)
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[turno, otro_turno],
        )


def test_reprogramar_fuera_de_horario_atencion_lanza_fuera_de_horario() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)

    with pytest.raises(FueraDeHorario):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(15, 0),  # Horario A atiende hasta las 14:00
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[turno],
        )


def test_reprogramar_dentro_de_bloqueo_lanza_dentro_de_bloqueo() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    bloqueo_prof = Bloqueo(
        alcance="profesional",
        recurso_id=ODONTOLOGO_A,
        inicio=_hora(11, 0),
        fin=_hora(13, 0),
        motivo="Reunión ficticia",
    )

    with pytest.raises(DentroDeBloqueo):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 15),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[bloqueo_prof],
            turnos_activos=[turno],
        )


def test_reprogramar_cambiando_profesional_y_sillon_exitoso() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1, profesional_id=ODONTOLOGO_A, sillon_id=SILLON_1)

    reprogramado = validar_reprogramacion(
        turno=turno,
        nuevo_inicio=_hora(10, 0),
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_B,
        bloqueos=[],
        turnos_activos=[turno],
        nuevo_profesional_id=ODONTOLOGO_B,
        nuevo_sillon_id=SILLON_2,
        nuevo_profesional=Profesional(nombre="Odontóloga", apellido="Ficticia B", id=ODONTOLOGO_B),
        nuevo_sillon=Sillon(nombre="Sillón 2", id=SILLON_2),
    )

    assert reprogramado.id == 1
    assert reprogramado.profesional_id == ODONTOLOGO_B
    assert reprogramado.sillon_id == SILLON_2
    assert reprogramado.inicio == _hora(10, 0)
    assert reprogramado.fin == _hora(10, 30)


# --- C-13 1.3: recursos nuevos y orden de validación (RN-REC-03, C-11 D10) ---

PROFESIONAL_B_ACTIVO = Profesional(nombre="Odontóloga", apellido="Ficticia B", id=ODONTOLOGO_B)
PROFESIONAL_B_INACTIVO = Profesional(
    nombre="Odontóloga", apellido="Ficticia B", activo=False, id=ODONTOLOGO_B
)
SILLON_2_ACTIVO = Sillon(nombre="Sillón 2", id=SILLON_2)
SILLON_2_INACTIVO = Sillon(nombre="Sillón 2", activo=False, id=SILLON_2)


def test_turno_cancelado_con_nuevo_sillon_inactivo_lanza_turno_no_modificable() -> None:
    turno = _turno(_hora(10, 0), _hora(10, 30), estado="cancelado")
    with pytest.raises(TurnoNoModificable):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 0),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[],
            nuevo_sillon_id=SILLON_2,
            nuevo_sillon=SILLON_2_INACTIVO,
        )


def test_turno_pasado_con_nuevo_profesional_inexistente_lanza_turno_no_modificable() -> None:
    turno = _turno(_hora(7, 0), _hora(7, 30))
    with pytest.raises(TurnoNoModificable):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 0),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=[],
            bloqueos=[],
            turnos_activos=[],
            nuevo_profesional_id=99,
            nuevo_profesional=None,
        )


@pytest.mark.parametrize(
    ("nuevo_profesional", "mensaje"),
    [
        (None, "no existe"),
        (PROFESIONAL_B_INACTIVO, "inactivo"),
    ],
)
def test_nuevo_profesional_inexistente_o_inactivo_lanza_dato_invalido(
    nuevo_profesional: Profesional | None, mensaje: str
) -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30))
    with pytest.raises(DatoInvalido, match=f"profesional.*{mensaje}"):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 0),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_B,
            bloqueos=[],
            turnos_activos=[turno],
            nuevo_profesional_id=ODONTOLOGO_B,
            nuevo_profesional=nuevo_profesional,
        )


@pytest.mark.parametrize(
    ("nuevo_sillon", "mensaje"),
    [
        (None, "no existe"),
        (SILLON_2_INACTIVO, "inactivo"),
    ],
)
def test_nuevo_sillon_inexistente_o_inactivo_lanza_dato_invalido(
    nuevo_sillon: Sillon | None, mensaje: str
) -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30))
    with pytest.raises(DatoInvalido, match=f"sillón.*{mensaje}"):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 0),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[turno],
            nuevo_sillon_id=SILLON_2,
            nuevo_sillon=nuevo_sillon,
        )


def test_recurso_nuevo_inactivo_con_conflicto_lanza_dato_invalido_y_no_conflicto() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    otro = _turno(_hora(11, 0), _hora(11, 30), id=2, profesional_id=ODONTOLOGO_B, paciente_id=PACIENTE_2)
    with pytest.raises(DatoInvalido):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 0),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_B,
            bloqueos=[],
            turnos_activos=[turno, otro],
            nuevo_profesional_id=ODONTOLOGO_B,
            nuevo_profesional=PROFESIONAL_B_INACTIVO,
        )


def test_sillon_nuevo_inactivo_con_conflicto_lanza_dato_invalido_y_no_conflicto() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    otro = _turno(_hora(11, 0), _hora(11, 30), id=2, sillon_id=SILLON_2, paciente_id=PACIENTE_2, profesional_id=ODONTOLOGO_B)
    with pytest.raises(DatoInvalido):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 0),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[turno, otro],
            nuevo_sillon_id=SILLON_2,
            nuevo_sillon=SILLON_2_INACTIVO,
        )


def test_recurso_vigente_inactivo_que_no_se_envia_no_impide_reprogramar() -> None:
    # El turno ya tiene un sillón vigente que hoy está inactivo; solo se cambia el horario
    # y se envía un profesional nuevo activo: el sillón actual no se revalida.
    turno = _turno(_hora(9, 0), _hora(9, 30), id=3, sillon_id=SILLON_1)

    reprogramado = validar_reprogramacion(
        turno=turno,
        nuevo_inicio=_hora(11, 0),
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_B,
        bloqueos=[],
        turnos_activos=[turno],
        nuevo_profesional_id=ODONTOLOGO_B,
        nuevo_profesional=PROFESIONAL_B_ACTIVO,
    )

    assert reprogramado.profesional_id == ODONTOLOGO_B
    assert reprogramado.sillon_id == SILLON_1


def test_solo_cambio_de_horario_sin_enviar_recursos_no_revalida_nada() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=4)

    reprogramado = validar_reprogramacion(
        turno=turno,
        nuevo_inicio=_hora(12, 0),
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_A,
        bloqueos=[],
        turnos_activos=[turno],
    )

    assert reprogramado.inicio == _hora(12, 0)


# --- C-13 1.5: conflictos por sillón, bloqueo de sillón y paciente (RN-TUR-03, RN-TUR-05, RN-TUR-12) ---


def test_reprogramar_solapa_con_turno_del_mismo_sillon_otro_profesional_lanza_conflicto() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    otro = _turno(
        _hora(11, 0), _hora(11, 30), id=2, profesional_id=ODONTOLOGO_B, paciente_id=PACIENTE_2
    )  # mismo sillón 1

    with pytest.raises(ConflictoAgenda, match="sillón"):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 15),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[turno, otro],
        )


def test_reprogramar_contiguo_al_turno_del_mismo_sillon_es_valido() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    otro = _turno(
        _hora(11, 0), _hora(11, 30), id=2, profesional_id=ODONTOLOGO_B, paciente_id=PACIENTE_2
    )

    reprogramado = validar_reprogramacion(
        turno=turno,
        nuevo_inicio=_hora(11, 30),  # [11:30, 12:00) no solapa con [11:00, 11:30)
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_A,
        bloqueos=[],
        turnos_activos=[turno, otro],
    )

    assert reprogramado.inicio == _hora(11, 30)


def test_reprogramar_dentro_de_bloqueo_de_sillon_lanza_dentro_de_bloqueo() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    bloqueo = Bloqueo(
        alcance="sillon",
        recurso_id=SILLON_1,
        inicio=_hora(11, 0),
        fin=_hora(13, 0),
        motivo="Mantenimiento ficticio",
    )

    with pytest.raises(DentroDeBloqueo, match="sillón"):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 15),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[bloqueo],
            turnos_activos=[turno],
        )


def test_reprogramar_con_bloqueo_de_otro_sillon_no_lo_afecta() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    bloqueo = Bloqueo(
        alcance="sillon",
        recurso_id=SILLON_2,
        inicio=_hora(11, 0),
        fin=_hora(13, 0),
        motivo="Mantenimiento ficticio",
    )

    reprogramado = validar_reprogramacion(
        turno=turno,
        nuevo_inicio=_hora(11, 15),
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_A,
        bloqueos=[bloqueo],
        turnos_activos=[turno],
    )

    assert reprogramado.inicio == _hora(11, 15)


def test_reprogramar_solapa_con_turno_del_mismo_paciente_lanza_conflicto() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    otro = _turno(
        _hora(11, 0), _hora(11, 30), id=2, profesional_id=ODONTOLOGO_B, sillon_id=SILLON_2
    )  # mismo paciente 1

    with pytest.raises(ConflictoAgenda, match="paciente"):
        validar_reprogramacion(
            turno=turno,
            nuevo_inicio=_hora(11, 15),
            ahora=AHORA_FIJO,
            prestacion=CONSULTA_30,
            horarios=HORARIOS_A,
            bloqueos=[],
            turnos_activos=[turno, otro],
        )


def test_reprogramar_ignora_turno_cancelado_del_mismo_paciente() -> None:
    turno = _turno(_hora(9, 0), _hora(9, 30), id=1)
    cancelado = _turno(
        _hora(11, 0),
        _hora(11, 30),
        id=2,
        profesional_id=ODONTOLOGO_B,
        sillon_id=SILLON_2,
        estado="cancelado",
    )

    reprogramado = validar_reprogramacion(
        turno=turno,
        nuevo_inicio=_hora(11, 15),
        ahora=AHORA_FIJO,
        prestacion=CONSULTA_30,
        horarios=HORARIOS_A,
        bloqueos=[],
        turnos_activos=[turno, cancelado],
    )

    assert reprogramado.inicio == _hora(11, 15)
