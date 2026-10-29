"""Modelos de dominio (dataclasses puras, sin dependencias de DB ni HTTP)."""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Literal

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
class Sillon:
    nombre: str
    activo: bool = True
    id: int | None = None


def validar_datos_sillon(nombre: str) -> str:
    """Normaliza y valida que el nombre del sillón no esté vacío (C-05)."""
    nombre_limpio = nombre.strip()
    if not nombre_limpio:
        raise DatoInvalido("El nombre del sillón no puede estar vacío.")
    return nombre_limpio


@dataclass(frozen=True, kw_only=True)
class Prestacion:
    id: int
    nombre: str
    duracion_minutos: int
    activa: bool = True


def validar_datos_prestacion(nombre: str, duracion_minutos: int) -> tuple[str, int]:
    """Normaliza el nombre y exige duración mayor que cero (RN-REC-01, C-05)."""
    nombre_limpio = nombre.strip()
    if not nombre_limpio:
        raise DatoInvalido("El nombre de la prestación no puede estar vacío.")
    if duracion_minutos <= 0:
        raise DatoInvalido("La duración de la prestación debe ser mayor que cero.")
    return nombre_limpio, duracion_minutos


@dataclass(frozen=True, kw_only=True)
class Paciente:
    nombre: str
    apellido: str
    dni: str
    telefono: str | None = None
    obra_social: str | None = None
    nro_afiliado: str | None = None
    id: int | None = None


def validar_datos_paciente(
    nombre: str,
    apellido: str,
    dni: str,
    telefono: str | None = None,
    obra_social: str | None = None,
    nro_afiliado: str | None = None,
) -> tuple[str, str, str, str | None, str | None, str | None]:
    """Normaliza y valida los datos mínimos del paciente (RN-PAC-01, C-06)."""
    nombre_limpio = nombre.strip()
    if not nombre_limpio:
        raise DatoInvalido("El nombre del paciente no puede estar vacío.")
    apellido_limpio = apellido.strip()
    if not apellido_limpio:
        raise DatoInvalido("El apellido del paciente no puede estar vacío.")
    dni_limpio = dni.strip()
    if not dni_limpio:
        raise DatoInvalido("El DNI del paciente no puede estar vacío.")
    telefono_limpio = telefono.strip() if telefono is not None else None
    if telefono_limpio == "":
        telefono_limpio = None
    obra_social_limpia = obra_social.strip() if obra_social is not None else None
    if obra_social_limpia == "":
        obra_social_limpia = None
    nro_afiliado_limpio = nro_afiliado.strip() if nro_afiliado is not None else None
    if nro_afiliado_limpio == "":
        nro_afiliado_limpio = None
    return (
        nombre_limpio,
        apellido_limpio,
        dni_limpio,
        telefono_limpio,
        obra_social_limpia,
        nro_afiliado_limpio,
    )


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
