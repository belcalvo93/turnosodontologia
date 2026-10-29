"""Tests de dominio para la gestión de usuarios (C-07, US-013). Python puro, sin DB ni HTTP."""

import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import Profesional
from app.domain.usuarios import (
    Rol,
    Usuario,
    aplicar_cambios_usuario,
    validar_datos_usuario,
    validar_username,
)

# Datos ficticios (RN-PAC-03): nunca nombres ni matrículas reales.
PROFESIONAL_ACTIVO = Profesional(
    id=7, nombre="Odontóloga", apellido="Ficticia A", matricula="0001 (ficticia)", activo=True
)
PROFESIONAL_INACTIVO = Profesional(
    id=8, nombre="Odontólogo", apellido="Ficticio B", matricula="0002 (ficticia)", activo=False
)
ODONTOLOGO_FICTICIO = Usuario(
    id=2,
    username="odontologo_ficticio",
    rol=Rol.ODONTOLOGO,
    profesional_id=PROFESIONAL_ACTIVO.id,
    activo=True,
)
RECEPCION_FICTICIA = Usuario(
    id=1,
    username="recepcion_ficticia",
    rol=Rol.RECEPCION,
    profesional_id=None,
    activo=True,
)


def test_validar_username_quita_espacios_laterales() -> None:
    assert validar_username("  recepcion_ficticia  ") == "recepcion_ficticia"


@pytest.mark.parametrize("username", ["", "   "])
def test_validar_username_rechaza_vacio(username: str) -> None:
    with pytest.raises(DatoInvalido):
        validar_username(username)


def test_validar_datos_usuario_odontologo_con_profesional_activo() -> None:
    rol, profesional_id = validar_datos_usuario(
        rol=Rol.ODONTOLOGO,
        profesional_id=PROFESIONAL_ACTIVO.id,
        profesional=PROFESIONAL_ACTIVO,
    )

    assert (rol, profesional_id) == (Rol.ODONTOLOGO, PROFESIONAL_ACTIVO.id)


def test_validar_datos_usuario_odontologo_sin_profesional_id() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_usuario(rol=Rol.ODONTOLOGO, profesional_id=None, profesional=None)


def test_validar_datos_usuario_odontologo_con_profesional_inexistente() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_usuario(
            rol=Rol.ODONTOLOGO,
            profesional_id=PROFESIONAL_INACTIVO.id,
            profesional=None,
        )


def test_validar_datos_usuario_odontologo_con_profesional_inactivo() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_usuario(
            rol=Rol.ODONTOLOGO,
            profesional_id=PROFESIONAL_INACTIVO.id,
            profesional=PROFESIONAL_INACTIVO,
        )


@pytest.mark.parametrize("rol", [Rol.ADMINISTRACION, Rol.RECEPCION])
def test_validar_datos_usuario_rol_sin_vinculo_rechaza_profesional(rol: Rol) -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_usuario(
            rol=rol,
            profesional_id=PROFESIONAL_ACTIVO.id,
            profesional=PROFESIONAL_ACTIVO,
        )


@pytest.mark.parametrize(
    ("rol", "esperado"),
    [(Rol.ADMINISTRACION, Rol.ADMINISTRACION), (Rol.RECEPCION, Rol.RECEPCION)],
)
def test_validar_datos_usuario_rol_sin_vinculo_devuelve_sin_profesional(
    rol: Rol, esperado: Rol
) -> None:
    assert validar_datos_usuario(rol=rol, profesional_id=None, profesional=None) == (
        esperado,
        None,
    )


def test_aplicar_cambios_usuario_sin_cambios_conserva_todo() -> None:
    assert aplicar_cambios_usuario(ODONTOLOGO_FICTICIO) == (
        Rol.ODONTOLOGO,
        PROFESIONAL_ACTIVO.id,
        True,
    )


def test_aplicar_cambios_usuario_cambia_solo_el_estado() -> None:
    assert aplicar_cambios_usuario(ODONTOLOGO_FICTICIO, activo=False) == (
        Rol.ODONTOLOGO,
        PROFESIONAL_ACTIVO.id,
        False,
    )


def test_aplicar_cambios_usuario_al_salir_de_odontologo_limpia_el_vinculo() -> None:
    assert aplicar_cambios_usuario(ODONTOLOGO_FICTICIO, rol=Rol.RECEPCION) == (
        Rol.RECEPCION,
        None,
        True,
    )


def test_aplicar_cambios_usuario_al_pasar_a_administracion_limpia_el_vinculo() -> None:
    assert aplicar_cambios_usuario(ODONTOLOGO_FICTICIO, rol=Rol.ADMINISTRACION) == (
        Rol.ADMINISTRACION,
        None,
        True,
    )


def test_aplicar_cambios_usuario_entrar_a_odontologo_sin_profesional_falla_al_validar() -> None:
    rol, profesional_id, _ = aplicar_cambios_usuario(RECEPCION_FICTICIA, rol=Rol.ODONTOLOGO)

    assert (rol, profesional_id) == (Rol.ODONTOLOGO, None)
    with pytest.raises(DatoInvalido):
        validar_datos_usuario(rol=rol, profesional_id=profesional_id, profesional=None)


def test_aplicar_cambios_usuario_entrar_a_odontologo_con_profesional() -> None:
    rol, profesional_id, activo = aplicar_cambios_usuario(
        RECEPCION_FICTICIA,
        rol=Rol.ODONTOLOGO,
        profesional_id=PROFESIONAL_ACTIVO.id,
    )

    assert (rol, profesional_id, activo) == (Rol.ODONTOLOGO, PROFESIONAL_ACTIVO.id, True)
    assert validar_datos_usuario(
        rol=rol, profesional_id=profesional_id, profesional=PROFESIONAL_ACTIVO
    ) == (Rol.ODONTOLOGO, PROFESIONAL_ACTIVO.id)


def test_aplicar_cambios_usuario_profesional_nulo_explicito_rompe_la_invariante() -> None:
    rol, profesional_id, _ = aplicar_cambios_usuario(ODONTOLOGO_FICTICIO, profesional_id=None)

    assert (rol, profesional_id) == (Rol.ODONTOLOGO, None)
    with pytest.raises(DatoInvalido):
        validar_datos_usuario(rol=rol, profesional_id=profesional_id, profesional=None)


def test_aplicar_cambios_usuario_cambia_profesional_sin_cambiar_rol() -> None:
    assert aplicar_cambios_usuario(
        ODONTOLOGO_FICTICIO, profesional_id=PROFESIONAL_INACTIVO.id
    ) == (Rol.ODONTOLOGO, PROFESIONAL_INACTIVO.id, True)
