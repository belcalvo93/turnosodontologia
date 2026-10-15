"""Errores de dominio. La capa API los traduce a HTTP (RN-GLO-01)."""


class ErrorDominio(Exception):
    """Base de todos los errores de dominio."""


class DatoInvalido(ErrorDominio):
    """Dato de entrada inválido (se mapea a 422)."""


class ConflictoAgenda(ErrorDominio):
    """Solapamiento con otro turno activo (se mapea a 409)."""


class FueraDeHorario(ErrorDominio):
    """El turno no encaja completo en una franja de atención (se mapea a 409)."""


class DentroDeBloqueo(ErrorDominio):
    """El turno cae dentro de un bloqueo de profesional o sillón (se mapea a 409)."""
