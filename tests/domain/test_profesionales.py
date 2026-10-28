"""Tests unitarios de Profesional y validación de datos en dominio puro (C-04)."""

import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import Profesional, validar_datos_profesional


def test_validar_datos_profesional_con_datos_validos_normaliza_espacios() -> None:
    nombre, apellido, matricula = validar_datos_profesional(
        "  Juan  ", "  Pérez  ", "  0001 (ficticia)  "
    )

    assert nombre == "Juan"
    assert apellido == "Pérez"
    assert matricula == "0001 (ficticia)"


@pytest.mark.parametrize("matricula_entrada", [None, "", "   "])
def test_validar_datos_profesional_con_matricula_vacia_o_nula_devuelve_none(
    matricula_entrada: str | None,
) -> None:
    nombre, apellido, matricula = validar_datos_profesional(
        "María", "Gómez", matricula_entrada
    )

    assert nombre == "María"
    assert apellido == "Gómez"
    assert matricula is None


@pytest.mark.parametrize(
    ("nombre_invalido", "apellido_invalido"),
    [
        ("", "Pérez"),
        ("   ", "Pérez"),
        ("Juan", ""),
        ("Juan", "   "),
    ],
)
def test_validar_datos_profesional_con_nombre_o_apellido_vacio_lanza_dato_invalido(
    nombre_invalido: str, apellido_invalido: str
) -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_profesional(nombre_invalido, apellido_invalido)


def test_profesional_por_defecto_queda_activo_y_sin_id() -> None:
    profesional = Profesional(nombre="Juan", apellido="Pérez")

    assert profesional.id is None
    assert profesional.nombre == "Juan"
    assert profesional.apellido == "Pérez"
    assert profesional.matricula is None
    assert profesional.activo is True
