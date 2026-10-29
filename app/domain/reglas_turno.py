"""Reglas de alta, cancelación y reprogramación de turno en dominio puro (C-10, C-12, C-13)."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime, timedelta

from app.domain.errores import (
    ConflictoAgenda,
    DentroDeBloqueo,
    FueraDeHorario,
    TurnoNoModificable,
)
from app.domain.intervalos import es_futuro, solapan
from app.domain.models import Bloqueo, HorarioAtencion, Prestacion, Turno

_MENSAJE_BLOQUEO = {
    "profesional": "El profesional está bloqueado en ese horario.",
    "sillon": "El sillón está bloqueado en ese horario.",
}
_MENSAJE_CONFLICTO = {
    "profesional": "El profesional ya tiene un turno en ese horario.",
    "sillon": "El sillón ya está ocupado en ese horario.",
    "paciente": "El paciente ya tiene un turno en ese horario.",
}


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
    fin = inicio + timedelta(minutes=prestacion.duracion_minutos)
    if not any(_encaja_en_franja(inicio, fin, profesional_id, h) for h in horarios):
        raise FueraDeHorario("El turno no encaja en el horario de atención del profesional.")
    candidato = Turno(
        paciente_id=paciente_id,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion_id=prestacion.id,
        inicio=inicio,
        fin=fin,
    )
    for bloqueo in bloqueos:
        if _bloqueo_afecta(bloqueo, candidato) and solapan(candidato, bloqueo):
            raise DentroDeBloqueo(_MENSAJE_BLOQUEO[bloqueo.alcance])
    for turno in turnos_activos:
        es_excluido = excluir_turno_id is not None and turno.id == excluir_turno_id
        if turno.estado != "reservado" or es_excluido:
            continue  # RN-TUR-08: cancelados y el propio turno no ocupan agenda
        recurso = _recurso_compartido(candidato, turno)
        if recurso is not None and solapan(candidato, turno):
            raise ConflictoAgenda(_MENSAJE_CONFLICTO[recurso])
    return candidato


def validar_cancelacion(turno: Turno, ahora: datetime) -> Turno:
    """Valida que el turno esté reservado y sea futuro, devolviendo el turno cancelado (RN-TUR-09, RN-TUR-10)."""
    if turno.estado == "cancelado":
        raise TurnoNoModificable("El turno ya está cancelado.")
    if not es_futuro(turno, ahora):
        raise TurnoNoModificable("Solo se pueden cancelar turnos futuros.")
    return replace(turno, estado="cancelado")


def _recurso_compartido(candidato: Turno, turno: Turno) -> str | None:
    """RN-TUR-03/12: un turno compite si comparte profesional, sillón o paciente."""
    if turno.profesional_id == candidato.profesional_id:
        return "profesional"
    if turno.sillon_id == candidato.sillon_id:
        return "sillon"
    if turno.paciente_id == candidato.paciente_id:
        return "paciente"
    return None


def _bloqueo_afecta(bloqueo: Bloqueo, turno: Turno) -> bool:
    """RN-TUR-05: el bloqueo aplica si es del profesional o del sillón del turno."""
    recurso_del_turno = turno.profesional_id if bloqueo.alcance == "profesional" else turno.sillon_id
    return bloqueo.recurso_id == recurso_del_turno


def _encaja_en_franja(
    inicio: datetime, fin: datetime, profesional_id: int, horario: HorarioAtencion
) -> bool:
    """RN-PRO-01/02: el turno entra completo en una única franja del profesional."""
    if horario.profesional_id != profesional_id or horario.dia_semana != inicio.weekday():
        return False
    desde = datetime.combine(inicio.date(), horario.hora_desde)
    hasta = datetime.combine(inicio.date(), horario.hora_hasta)
    return desde <= inicio and fin <= hasta


def validar_reprogramacion(
    turno: Turno,
    nuevo_inicio: datetime,
    ahora: datetime,
    prestacion: Prestacion,
    horarios: Sequence[HorarioAtencion],
    bloqueos: Sequence[Bloqueo],
    turnos_activos: Sequence[Turno],
    nuevo_profesional_id: int | None = None,
    nuevo_sillon_id: int | None = None,
) -> Turno:
    """Valida y ejecuta la reprogramación de un turno futuro activo (RN-TUR-07, RN-TUR-08, RN-TUR-09, RN-TUR-10)."""
    if turno.estado != "reservado":
        raise TurnoNoModificable("No se puede reprogramar un turno cancelado.")
    if not es_futuro(turno, ahora):
        raise TurnoNoModificable("Solo se pueden reprogramar turnos futuros.")

    profesional_id = nuevo_profesional_id if nuevo_profesional_id is not None else turno.profesional_id
    sillon_id = nuevo_sillon_id if nuevo_sillon_id is not None else turno.sillon_id

    candidato = validar_alta(
        inicio=nuevo_inicio,
        prestacion=prestacion,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        paciente_id=turno.paciente_id,
        horarios=horarios,
        bloqueos=bloqueos,
        turnos_activos=turnos_activos,
        excluir_turno_id=turno.id,
    )
    return replace(candidato, id=turno.id, estado=turno.estado)
