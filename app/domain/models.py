"""Modelos de dominio (dataclasses puras, sin dependencias de DB ni HTTP)."""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Literal, cast

from app.domain.errores import DatoInvalido

EstadoTurno = Literal["reservado", "cancelado"]
AlcanceBloqueo = Literal["profesional", "sillon"]


@dataclass(frozen=True, kw_only=True)
class Profesional:
    nombre: str
    apellido: str
    matricula: str | None = None
    activo: bool = True
    id: int | None = None


def validar_datos_profesional(
    nombre: str, apellido: str, matricula: str | None = None
) -> tuple[str, str, str | None]:
    """Normaliza y valida que nombre y apellido no estén vacíos (C-04)."""
    nombre_limpio = nombre.strip()
    if not nombre_limpio:
        raise DatoInvalido("El nombre del profesional no puede estar vacío.")
    apellido_limpio = apellido.strip()
    if not apellido_limpio:
        raise DatoInvalido("El apellido del profesional no puede estar vacío.")
    matricula_limpia = matricula.strip() if matricula is not None else None
    if matricula_limpia == "":
        matricula_limpia = None
    return nombre_limpio, apellido_limpio, matricula_limpia


@dataclass(frozen=True, kw_only=True)
class Prestacion:
    id: int
    nombre: str
    duracion_minutos: int
    activa: bool = True


@dataclass(frozen=True, kw_only=True)
class HorarioAtencion:
    profesional_id: int
    dia_semana: int  # 0 = lunes ... 6 = domingo
    hora_desde: time
    hora_hasta: time


@dataclass(frozen=True, kw_only=True)
class Bloqueo:
    alcance: AlcanceBloqueo
    recurso_id: int
    inicio: datetime
    fin: datetime
    motivo: str = ""
    id: int | None = None


def validar_datos_bloqueo(
    alcance: str,
    recurso_id: int,
    inicio: datetime,
    fin: datetime,
    motivo: str = "",
) -> Bloqueo:
    """Valida las invariantes de negocio de un bloqueo (C-09, RN-REC-02)."""
    if alcance not in ("profesional", "sillon"):
        raise DatoInvalido("El alcance del bloqueo debe ser 'profesional' o 'sillon'.")
    if inicio.tzinfo is not None or fin.tzinfo is not None:
        raise DatoInvalido("Las fechas del bloqueo deben ser hora local sin zona horaria.")
    if inicio >= fin:
        raise DatoInvalido("El inicio del bloqueo debe ser anterior al fin.")
    return Bloqueo(
        alcance=cast(AlcanceBloqueo, alcance),
        recurso_id=recurso_id,
        inicio=inicio,
        fin=fin,
        motivo=motivo.strip(),
    )


@dataclass(frozen=True, kw_only=True)
class Turno:
    paciente_id: int
    profesional_id: int
    sillon_id: int
    prestacion_id: int
    inicio: datetime
    fin: datetime
    estado: EstadoTurno = "reservado"
    id: int | None = None
