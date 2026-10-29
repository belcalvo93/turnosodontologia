"""Tests unitarios de Sillon y validación de datos en dominio puro (C-05)."""

import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import Sillon, validar_datos_sillon


def test_validar_datos_sillon_con_nombre_valido_normaliza_espacios() -> None:
    assert validar_datos_sillon("  Sillón 1 (ficticio)  ") == "Sillón 1 (ficticio)"


@pytest.mark.parametrize("nombre_invalido", ["", "   "])
def test_validar_datos_sillon_con_nombre_vacio_lanza_dato_invalido(
    nombre_invalido: str,
) -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_sillon(nombre_invalido)


def test_sillon_por_defecto_queda_activo_y_sin_id() -> None:
    sillon = Sillon(nombre="Sillón 1 (ficticio)")

    assert sillon.id is None
    assert sillon.nombre == "Sillón 1 (ficticio)"
    assert sillon.activo is True


def test_sillon_conserva_los_valores_explicitos() -> None:
    sillon = Sillon(id=3, nombre="Box 2 (ficticio)", activo=False)

    assert sillon.id == 3
    assert sillon.nombre == "Box 2 (ficticio)"
    assert sillon.activo is False
