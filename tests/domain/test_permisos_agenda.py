"""Tests de permisos y validaciones de rango para la agenda en dominio puro (C-14)."""

from datetime import datetime

import pytest

from app.domain.errores import DatoInvalido
from app.domain.usuarios import (
    Rol,
    Usuario,
    puede_ver_agenda_profesional,
    puede_ver_agenda_sillon,
    validar_rango_agenda,
)


def _usuario(rol: Rol, profesional_id: int | None = None) -> Usuario:
    return Usuario(
        id=1,
        username="usuario_test",
        rol=rol,
        profesional_id=profesional_id,
        activo=True,
    )


def test_administracion_y_recepcion_pueden_ver_agenda_de_cualquier_profesional() -> None:
    admin = _usuario(Rol.ADMINISTRACION)
    recep = _usuario(Rol.RECEPCION)

    assert puede_ver_agenda_profesional(admin, profesional_id=1) is True
    assert puede_ver_agenda_profesional(admin, profesional_id=99) is True
    assert puede_ver_agenda_profesional(recep, profesional_id=1) is True
    assert puede_ver_agenda_profesional(recep, profesional_id=99) is True


def test_odontologo_solo_puede_ver_su_propia_agenda_profesional() -> None:
    odontologo = _usuario(Rol.ODONTOLOGO, profesional_id=5)

    assert puede_ver_agenda_profesional(odontologo, profesional_id=5) is True
    assert puede_ver_agenda_profesional(odontologo, profesional_id=6) is False


def test_odontologo_sin_profesional_id_no_puede_ver_ninguna_agenda() -> None:
    odontologo_sin_vincular = _usuario(Rol.ODONTOLOGO, profesional_id=None)

    assert puede_ver_agenda_profesional(odontologo_sin_vincular, profesional_id=1) is False


def test_solo_administracion_y_recepcion_pueden_ver_agenda_de_sillon() -> None:
    admin = _usuario(Rol.ADMINISTRACION)
    recep = _usuario(Rol.RECEPCION)
    odontologo = _usuario(Rol.ODONTOLOGO, profesional_id=1)

    assert puede_ver_agenda_sillon(admin) is True
    assert puede_ver_agenda_sillon(recep) is True
    assert puede_ver_agenda_sillon(odontologo) is False


def test_validar_rango_agenda_correcto_no_lanza_error() -> None:
    desde = datetime(2026, 11, 16, 8, 0)
    hasta = datetime(2026, 11, 16, 18, 0)
    validar_rango_agenda(desde, hasta)


def test_validar_rango_agenda_mismo_instante_no_lanza_error() -> None:
    instante = datetime(2026, 11, 16, 12, 0)
    validar_rango_agenda(instante, instante)


def test_validar_rango_agenda_invertido_lanza_dato_invalido() -> None:
    desde = datetime(2026, 11, 16, 18, 0)
    hasta = datetime(2026, 11, 16, 8, 0)

    with pytest.raises(DatoInvalido, match="rango de fechas"):
        validar_rango_agenda(desde, hasta)
