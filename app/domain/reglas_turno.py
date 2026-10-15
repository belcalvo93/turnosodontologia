"""Reglas de alta de turno en dominio puro (C-10)."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from app.domain.models import Bloqueo, HorarioAtencion, Prestacion, Turno


def validar_alta(
    inicio: datetime,
    prestacion: Prestacion,
    profesional_id: int,
    sillon_id: int,
    paciente_id: int,
    horarios: Sequence[HorarioAtencion],
    bloqueos: Sequence[Bloqueo],
    turnos_activos: Sequence[Turno],
    excluir_turno_id: int | None = None,
) -> Turno:
    return Turno(
        paciente_id=paciente_id,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion_id=prestacion.id,
        inicio=inicio,
        fin=inicio + timedelta(minutes=prestacion.duracion_minutos),
    )
