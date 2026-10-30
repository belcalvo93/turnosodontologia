"""Usuarios, roles y validaciones de la gestión de cuentas y agenda (C-03, C-07, C-14). Python puro."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.errores import DatoInvalido
from app.domain.models import Profesional, Turno


class Rol(StrEnum):
    """Roles del MVP (KB 03 §RBAC)."""

    ADMINISTRACION = "administracion"
    RECEPCION = "recepcion"
    ODONTOLOGO = "odontologo"


@dataclass(frozen=True, kw_only=True)
class Usuario:
    """Usuario autenticable.

    No incluye `password_hash`: el hash viaja aparte (ver `buscar_credenciales`)
    para que nunca termine serializado junto al usuario.
    """

    id: int
    username: str
    rol: Rol
    # Sin FK en la base; C-07 valida que el profesional exista para usuarios odontólogo.
    profesional_id: int | None
    activo: bool


def puede_ver_turno(usuario: Usuario, turno: Turno) -> bool:
    """Administración y recepción ven cualquier turno; el odontólogo solo los suyos (RN-ACC-03)."""
    if usuario.rol is Rol.ODONTOLOGO:
        return usuario.profesional_id is not None and usuario.profesional_id == turno.profesional_id
    return True


def puede_ver_agenda_profesional(usuario: Usuario, profesional_id: int) -> bool:
    """Administración y recepción ven cualquier agenda; el odontólogo solo la propia (RN-ACC-03)."""
    if usuario.rol is Rol.ODONTOLOGO:
        return usuario.profesional_id is not None and usuario.profesional_id == profesional_id
    return True


def puede_ver_agenda_sillon(usuario: Usuario) -> bool:
    """Administración y recepción ven la agenda de sillones; el odontólogo no (03 §RBAC)."""
    return usuario.rol in (Rol.ADMINISTRACION, Rol.RECEPCION)


def validar_rango_agenda(desde: datetime, hasta: datetime) -> None:
    """Valida que el rango temporal de consulta sea consistente (desde <= hasta)."""
    if desde > hasta:
        raise DatoInvalido("El rango de fechas es inválido: 'desde' no puede ser posterior a 'hasta'.")



def validar_username(username: str) -> str:
    """Normaliza el nombre de usuario y rechaza vacíos (C-07)."""
    username_limpio = username.strip()
    if not username_limpio:
        raise DatoInvalido("El nombre de usuario no puede estar vacío.")
    return username_limpio


def validar_datos_usuario(
    *,
    rol: Rol,
    profesional_id: int | None,
    profesional: Profesional | None,
) -> tuple[Rol, int | None]:
    """Aplica la invariante rol ↔ profesional de un usuario (C-07, US-013).

    Un odontólogo debe estar vinculado a un profesional existente y activo; los
    demás roles no llevan vínculo. Devuelve los valores normalizados.
    """
    if rol is Rol.ODONTOLOGO:
        if profesional_id is None:
            raise DatoInvalido("Un usuario odontólogo debe estar vinculado a un profesional.")
        if profesional is None:
            raise DatoInvalido("El profesional indicado no existe.")
        if not profesional.activo:
            raise DatoInvalido("El profesional indicado está inactivo.")
        return rol, profesional_id
    if profesional_id is not None:
        raise DatoInvalido("Solo los usuarios odontólogos se vinculan a un profesional.")
    return rol, None


# Centinela del dominio para distinguir "campo omitido" de "null explícito" en una edición.
SIN_CAMBIO = object()


def aplicar_cambios_usuario(
    actual: Usuario,
    *,
    rol: Rol | None = None,
    profesional_id: int | None | object = SIN_CAMBIO,
    activo: bool | None = None,
) -> tuple[Rol, int | None, bool]:
    """Combina una edición parcial con el usuario actual y aplica la limpieza del vínculo.

    Al cambiar el rol a uno distinto de `odontologo`, `profesional_id` se limpia solo
    para que la transición sea posible en un único request. El resultado todavía debe
    pasar por `validar_datos_usuario` para comprobar la invariante completa.
    """
    rol_candidato = actual.rol if rol is None else rol
    activo_candidato = actual.activo if activo is None else activo

    profesional_candidato: int | None
    if rol_candidato is not Rol.ODONTOLOGO:
        profesional_candidato = None
    elif profesional_id is SIN_CAMBIO:
        profesional_candidato = actual.profesional_id
    elif profesional_id is None:
        profesional_candidato = None
    elif isinstance(profesional_id, int):
        profesional_candidato = profesional_id
    else:
        raise TypeError("profesional_id debe ser un entero, None o SIN_CAMBIO.")

    return rol_candidato, profesional_candidato, activo_candidato
