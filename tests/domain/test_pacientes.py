"""Tests unitarios de Paciente y validación de datos en dominio puro (C-06)."""

import pytest

from app.domain.errores import DatoInvalido
from app.domain.models import Paciente, validar_datos_paciente


def test_validar_datos_paciente_normaliza_espacios_en_nombre() -> None:
    nombre, _, _, _, _, _ = validar_datos_paciente(
        "  Ana  ", "Pérez", "30111222 (ficticio)"
    )

    assert nombre == "Ana"


def test_validar_datos_paciente_normaliza_espacios_en_apellido() -> None:
    _, apellido, _, _, _, _ = validar_datos_paciente(
        "Ana", "  Pérez  ", "30111222 (ficticio)"
    )

    assert apellido == "Pérez"


def test_validar_datos_paciente_normaliza_espacios_en_dni() -> None:
    _, _, dni, _, _, _ = validar_datos_paciente(
        "Ana", "Pérez", "  30111222 (ficticio)  "
    )

    assert dni == "30111222 (ficticio)"


def test_validar_datos_paciente_conserva_puntos_guiones_y_espacios_internos_del_dni() -> (
    None
):
    _, _, dni, _, _, _ = validar_datos_paciente(
        "Ana", "Pérez", "  00.000.001 (ficticio)  "
    )

    assert dni == "00.000.001 (ficticio)"


def test_validar_datos_paciente_normaliza_espacios_en_telefono() -> None:
    _, _, _, telefono, _, _ = validar_datos_paciente(
        "Ana", "Pérez", "30111222 (ficticio)", telefono="  3884000000  "
    )

    assert telefono == "3884000000"


def test_validar_datos_paciente_normaliza_espacios_en_obra_social() -> None:
    _, _, _, _, obra_social, _ = validar_datos_paciente(
        "Ana", "Pérez", "30111222 (ficticio)", obra_social="  Obra Social (ficticia)  "
    )

    assert obra_social == "Obra Social (ficticia)"


def test_validar_datos_paciente_normaliza_espacios_en_nro_afiliado() -> None:
    _, _, _, _, _, nro_afiliado = validar_datos_paciente(
        "Ana", "Pérez", "30111222 (ficticio)", nro_afiliado="  12345 (ficticio)  "
    )

    assert nro_afiliado == "12345 (ficticio)"


def test_validar_datos_paciente_con_nombre_vacio_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_paciente("", "Pérez", "30111222 (ficticio)")


def test_validar_datos_paciente_con_nombre_solo_espacios_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_paciente("   ", "Pérez", "30111222 (ficticio)")


def test_validar_datos_paciente_con_apellido_vacio_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_paciente("Ana", "", "30111222 (ficticio)")


def test_validar_datos_paciente_con_apellido_solo_espacios_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_paciente("Ana", "   ", "30111222 (ficticio)")


def test_validar_datos_paciente_con_dni_vacio_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_paciente("Ana", "Pérez", "")


def test_validar_datos_paciente_con_dni_solo_espacios_lanza_dato_invalido() -> None:
    with pytest.raises(DatoInvalido):
        validar_datos_paciente("Ana", "Pérez", "   ")


def test_validar_datos_paciente_convierte_telefono_vacio_en_none() -> None:
    _, _, _, telefono, _, _ = validar_datos_paciente(
        "Ana", "Pérez", "30111222 (ficticio)", telefono=""
    )

    assert telefono is None


def test_validar_datos_paciente_convierte_obra_social_vacia_en_none() -> None:
    _, _, _, _, obra_social, _ = validar_datos_paciente(
        "Ana", "Pérez", "30111222 (ficticio)", obra_social=""
    )

    assert obra_social is None


def test_validar_datos_paciente_convierte_nro_afiliado_vacio_en_none() -> None:
    _, _, _, _, _, nro_afiliado = validar_datos_paciente(
        "Ana", "Pérez", "30111222 (ficticio)", nro_afiliado=""
    )

    assert nro_afiliado is None


def test_validar_datos_paciente_deja_opcionales_omitidos_en_none() -> None:
    _, _, _, telefono, obra_social, nro_afiliado = validar_datos_paciente(
        "Ana", "Pérez", "30111222 (ficticio)"
    )

    assert telefono is None
    assert obra_social is None
    assert nro_afiliado is None


def test_paciente_por_defecto_tiene_id_none_y_opcionales_none() -> None:
    paciente = Paciente(
        nombre="Ana", apellido="Pérez", dni="30111222 (ficticio)"
    )

    assert paciente.id is None
    assert paciente.telefono is None
    assert paciente.obra_social is None
    assert paciente.nro_afiliado is None


def test_paciente_conserva_los_valores_explicitos() -> None:
    paciente = Paciente(
        id=7,
        nombre="Ana",
        apellido="Pérez",
        dni="30111222 (ficticio)",
        telefono="3884000000",
        obra_social="Obra Social (ficticia)",
        nro_afiliado="12345 (ficticio)",
    )

    assert paciente.id == 7
    assert paciente.nombre == "Ana"
    assert paciente.apellido == "Pérez"
    assert paciente.dni == "30111222 (ficticio)"
    assert paciente.telefono == "3884000000"
    assert paciente.obra_social == "Obra Social (ficticia)"
    assert paciente.nro_afiliado == "12345 (ficticio)"
