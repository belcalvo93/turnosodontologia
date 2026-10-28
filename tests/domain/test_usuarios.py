"""Tests de Rol y Usuario: dominio puro, sin base de datos ni HTTP (C-03)."""

import ast
import dataclasses
from pathlib import Path

import pytest

from app.domain import usuarios
from app.domain.usuarios import Rol, Usuario

# Datos ficticios (RN-PAC-03)
RECEPCION_FICTICIA = Usuario(
    id=1,
    username="recepcion_ficticia",
    rol=Rol.RECEPCION,
    profesional_id=None,
    activo=True,
)


def test_rol_tiene_exactamente_los_tres_roles_del_mvp() -> None:
    assert {rol.value for rol in Rol} == {"administracion", "recepcion", "odontologo"}


def test_rol_se_construye_desde_el_texto_guardado_en_la_base() -> None:
    assert Rol("odontologo") is Rol.ODONTOLOGO
    assert Rol.RECEPCION == "recepcion"


def test_rol_desconocido_se_rechaza() -> None:
    with pytest.raises(ValueError):
        Rol("superusuario")


@pytest.mark.parametrize(("campo", "valor"), [("rol", Rol.ADMINISTRACION), ("activo", False)])
def test_usuario_es_inmutable(campo: str, valor: object) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(RECEPCION_FICTICIA, campo, valor)


def test_usuario_odontologo_lleva_su_profesional() -> None:
    odontologo = Usuario(
        id=2,
        username="odontologo_ficticio",
        rol=Rol.ODONTOLOGO,
        profesional_id=7,
        activo=True,
    )

    assert odontologo.profesional_id == 7
    assert odontologo != RECEPCION_FICTICIA


def test_modulo_usuarios_no_importa_capas_externas() -> None:
    fuente = Path(usuarios.__file__).read_text(encoding="utf-8")
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)

    prohibidos = ("fastapi", "starlette", "app.db", "app.api")
    assert importados
    assert [modulo for modulo in importados if modulo.startswith(prohibidos)] == []


def test_usuario_no_tiene_password_hash() -> None:
    campos = {campo.name for campo in dataclasses.fields(Usuario)}

    assert "password_hash" not in campos
    assert not hasattr(RECEPCION_FICTICIA, "password_hash")
