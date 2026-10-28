"""Tests de hash de contraseñas y token, sin HTTP (C-03, RN-ACC-04)."""

import pytest

from app.api.seguridad import hashear, verificar

# Contraseñas ficticias: nunca usar credenciales reales en los tests.
CLAVE_FICTICIA = "clave-ficticia-123"
OTRA_CLAVE_FICTICIA = "otra-clave-ficticia"


def test_hash_no_es_ni_contiene_la_contrasena() -> None:
    hash_clave = hashear(CLAVE_FICTICIA)

    assert hash_clave != CLAVE_FICTICIA
    assert CLAVE_FICTICIA not in hash_clave


def test_misma_contrasena_produce_hashes_distintos() -> None:
    assert hashear(CLAVE_FICTICIA) != hashear(CLAVE_FICTICIA)


def test_verificar_acepta_solo_la_contrasena_correcta() -> None:
    hash_clave = hashear(CLAVE_FICTICIA)

    assert verificar(CLAVE_FICTICIA, hash_clave) is True
    assert verificar(OTRA_CLAVE_FICTICIA, hash_clave) is False


def test_el_hash_usa_argon2id() -> None:
    assert hashear(CLAVE_FICTICIA).startswith("$argon2id$")


@pytest.mark.parametrize("casi_igual", ["clave-ficticia-12", "Clave-Ficticia-123", ""])
def test_verificar_rechaza_contrasenas_casi_iguales(casi_igual: str) -> None:
    assert verificar(casi_igual, hashear(CLAVE_FICTICIA)) is False


def test_contrasena_con_caracteres_no_ascii_se_verifica() -> None:
    clave_con_enie = "contraseña-ficticia-ñandú"

    hash_clave = hashear(clave_con_enie)

    assert verificar(clave_con_enie, hash_clave) is True
    assert verificar("contrasena-ficticia-nandu", hash_clave) is False
