"""Recursos de un alta de turno: existentes y activos (RN-REC-03, RN-GLO-01). Dominio puro."""

import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import Paciente, Prestacion, Profesional, Sillon
from app.domain.reglas_turno import validar_recursos_alta

# Datos ficticios (RN-PAC-03)
PRESTACION = Prestacion(id=1, nombre="Consulta ficticia", duracion_minutos=30)
PROFESIONAL = Profesional(nombre="Ana", apellido="Ficticia", id=1)
SILLON = Sillon(nombre="Sillón 1 (ficticio)", id=1)
PACIENTE = Paciente(nombre="Juan", apellido="Ficticio", dni="30111222 (ficticio)", id=1)


def test_validar_recursos_alta_con_todo_activo_devuelve_la_prestacion() -> None:
    resultado = validar_recursos_alta(PRESTACION, PROFESIONAL, SILLON, PACIENTE)

    assert resultado is PRESTACION


def test_validar_recursos_alta_devuelve_la_prestacion_recibida_no_una_fija() -> None:
    otra = Prestacion(id=7, nombre="Limpieza ficticia", duracion_minutos=45)

    assert validar_recursos_alta(otra, PROFESIONAL, SILLON, PACIENTE) is otra


@pytest.mark.parametrize(
    ("prestacion", "profesional", "sillon", "paciente", "fragmento"),
    [
        (None, PROFESIONAL, SILLON, PACIENTE, "prestación"),
        (
            Prestacion(id=1, nombre="Consulta ficticia", duracion_minutos=30, activa=False),
            PROFESIONAL,
            SILLON,
            PACIENTE,
            "prestación",
        ),
        (PRESTACION, None, SILLON, PACIENTE, "profesional"),
        (
            PRESTACION,
            Profesional(nombre="Ana", apellido="Ficticia", activo=False, id=1),
            SILLON,
            PACIENTE,
            "profesional",
        ),
        (PRESTACION, PROFESIONAL, None, PACIENTE, "sillón"),
        (
            PRESTACION,
            PROFESIONAL,
            Sillon(nombre="Sillón 1 (ficticio)", activo=False, id=1),
            PACIENTE,
            "sillón",
        ),
        (PRESTACION, PROFESIONAL, SILLON, None, "paciente"),
    ],
    ids=[
        "prestacion_inexistente",
        "prestacion_inactiva",
        "profesional_inexistente",
        "profesional_inactivo",
        "sillon_inexistente",
        "sillon_inactivo",
        "paciente_inexistente",
    ],
)
def test_validar_recursos_alta_con_recurso_invalido_lanza_dato_invalido_en_espanol(
    prestacion: Prestacion | None,
    profesional: Profesional | None,
    sillon: Sillon | None,
    paciente: Paciente | None,
    fragmento: str,
) -> None:
    with pytest.raises(DatoInvalido) as error:
        validar_recursos_alta(prestacion, profesional, sillon, paciente)

    assert fragmento in str(error.value)


def test_validar_recursos_alta_con_varios_invalidos_informa_el_primero_en_orden() -> None:
    with pytest.raises(DatoInvalido) as error:
        validar_recursos_alta(None, None, None, None)

    assert "prestación" in str(error.value)
