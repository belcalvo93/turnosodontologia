"""Quién puede ver un turno (RN-ACC-03). Dominio puro, sin base de datos ni HTTP."""

from datetime import datetime

import pytest

from app.domain.models import Turno
from app.domain.usuarios import Rol, Usuario, puede_ver_turno


def _usuario(rol: Rol, profesional_id: int | None = None) -> Usuario:
    return Usuario(
        id=1,
        username="usuario_ficticio",
        rol=rol,
        profesional_id=profesional_id,
        activo=True,
    )


def _turno(profesional_id: int) -> Turno:
    return Turno(
        id=1,
        paciente_id=1,
        profesional_id=profesional_id,
        sillon_id=1,
        prestacion_id=1,
        inicio=datetime(2026, 1, 12, 10, 0),
        fin=datetime(2026, 1, 12, 10, 30),
    )


def test_puede_ver_turno_odontologo_de_otro_profesional_devuelve_false() -> None:
    assert puede_ver_turno(_usuario(Rol.ODONTOLOGO, profesional_id=1), _turno(2)) is False


def test_puede_ver_turno_odontologo_del_mismo_profesional_devuelve_true() -> None:
    assert puede_ver_turno(_usuario(Rol.ODONTOLOGO, profesional_id=2), _turno(2)) is True


def test_puede_ver_turno_odontologo_sin_profesional_vinculado_devuelve_false() -> None:
    assert puede_ver_turno(_usuario(Rol.ODONTOLOGO, profesional_id=None), _turno(2)) is False


@pytest.mark.parametrize("rol", [Rol.ADMINISTRACION, Rol.RECEPCION])
@pytest.mark.parametrize("profesional_del_turno", [1, 2])
def test_puede_ver_turno_administracion_y_recepcion_ven_cualquier_profesional(
    rol: Rol, profesional_del_turno: int
) -> None:
    assert puede_ver_turno(_usuario(rol), _turno(profesional_del_turno)) is True
