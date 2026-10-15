"""Comparación de intervalos semiabiertos [inicio, fin) (RN-TUR-04)."""

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
