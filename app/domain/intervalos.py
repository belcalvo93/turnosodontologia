"""Comparación de intervalos semiabiertos [inicio, fin) (RN-TUR-04, RN-TUR-09)."""

from datetime import datetime
from typing import Protocol


class Intervalo(Protocol):
    @property
    def inicio(self) -> datetime: ...

    @property
    def fin(self) -> datetime: ...


def solapan(a: Intervalo, b: Intervalo) -> bool:
    """Devuelve True si [a.inicio, a.fin) y [b.inicio, b.fin) comparten algún instante.

    Los intervalos contiguos (a.fin == b.inicio) no solapan.
    """
    return a.inicio < b.fin and b.inicio < a.fin


def es_futuro(intervalo: Intervalo, ahora: datetime) -> bool:
    """Devuelve True si el inicio del intervalo es estrictamente posterior a `ahora` (RN-TUR-09)."""
    return intervalo.inicio > ahora
