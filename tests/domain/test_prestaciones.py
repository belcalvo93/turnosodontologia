"""Tests unitarios de Prestacion y validación de datos en dominio puro (C-05, RN-REC-01)."""

import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import Prestacion, validar_datos_prestacion


def test_validar_datos_prestacion_con_datos_validos_normaliza_espacios() -> None:
    nombre, duracion_minutos = validar_datos_prestacion("  Consulta ficticia  ", 45)

    assert nombre == "Consulta ficticia"
    assert duracion_minutos == 45


@pytest.mark.parametrize("nombre_invalido", ["", "   "])
def test_validar_datos_prestacion_con_nombre_vacio_lanza_dato_invalido(
    nombre_invalido: str,
) -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_prestacion(nombre_invalido, 45)


@pytest.mark.parametrize("duracion_invalida", [0, -1, -45])
def test_validar_datos_prestacion_con_duracion_no_positiva_lanza_dato_invalido(
    duracion_invalida: int,
) -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_prestacion("Consulta ficticia", duracion_invalida)


def test_prestacion_por_defecto_queda_activa() -> None:
    prestacion = Prestacion(id=1, nombre="Consulta ficticia", duracion_minutos=45)

    assert prestacion.activa is True
