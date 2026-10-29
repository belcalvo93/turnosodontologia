"""Usuarios y roles del sistema (C-03). Python puro: sin DB ni HTTP."""

from dataclasses import dataclass
from enum import StrEnum


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
