"""Tests del repositorio SQLite de usuarios (C-07, US-013)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.api.seguridad import hashear, verificar
from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio import buscar_credenciales
from app.db.repositorio_usuarios import (
    actualizar_usuario,
    crear_usuario,
    listar_usuarios,
)
from app.domain.errores import UsernameDuplicado
from app.domain.usuarios import Rol, Usuario

# Contraseñas ficticias: nunca credenciales reales (RN-PAC-03, regla dura 9).
CLAVE_FICTICIA = "clave-ficticia-123"
OTRA_CLAVE_FICTICIA = "otra-clave-ficticia-456"


def _crear_admin(conexion: sqlite3.Connection, *, username: str = "admin_ficticio") -> Usuario:
    return crear_usuario(
        conexion,
        username=username,
        password_hash=hashear(CLAVE_FICTICIA),
        rol=Rol.ADMINISTRACION,
    )


def test_crear_usuario_guarda_el_hash_y_devuelve_la_entidad(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_crear.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_usuario(
                conexion,
                username="recepcion_ficticia",
                password_hash=hashear(CLAVE_FICTICIA),
                rol=Rol.RECEPCION,
            )

        assert creado == Usuario(
            id=1,
            username="recepcion_ficticia",
            rol=Rol.RECEPCION,
            profesional_id=None,
            activo=True,
        )
        credenciales = buscar_credenciales(conexion, "recepcion_ficticia")
        assert credenciales is not None
        usuario, password_hash = credenciales
        assert usuario == creado
        assert password_hash != CLAVE_FICTICIA
        assert verificar(CLAVE_FICTICIA, password_hash)


def test_crear_usuario_odontologo_conserva_el_profesional(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_crear_odontologo.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_usuario(
                conexion,
                username="odontologo_ficticio",
                password_hash=hashear(CLAVE_FICTICIA),
                rol=Rol.ODONTOLOGO,
                profesional_id=3,
            )

        assert creado.rol is Rol.ODONTOLOGO
        assert creado.profesional_id == 3


def test_crear_usuario_username_duplicado_lanza_username_duplicado(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_duplicado.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            _crear_admin(conexion)
        with pytest.raises(UsernameDuplicado) as excinfo, transaccion(conexion):
            _crear_admin(conexion)

        assert "admin_ficticio" not in str(excinfo.value)
        assert conexion.execute("SELECT COUNT(*) FROM usuario").fetchone() == (1,)


def test_crear_usuario_re_lanza_otra_integridad(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_otra_integridad.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with pytest.raises(sqlite3.IntegrityError):
            crear_usuario(
                conexion,
                username=None,  # type: ignore[arg-type]
                password_hash=hashear(CLAVE_FICTICIA),
                rol=Rol.RECEPCION,
            )


def test_listar_usuarios_devuelve_ordenados_por_id_e_incluye_inactivos(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_listar.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            primero = _crear_admin(conexion)
            segundo = crear_usuario(
                conexion,
                username="recepcion_ficticia",
                password_hash=hashear(CLAVE_FICTICIA),
                rol=Rol.RECEPCION,
                activo=False,
            )

        assert listar_usuarios(conexion) == [primero, segundo]
        assert listar_usuarios(conexion)[1].activo is False


def test_listar_usuarios_sin_filas_devuelve_lista_vacia(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_listar_vacio.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        assert listar_usuarios(conexion) == []


def test_actualizar_usuario_cambia_rol_activo_y_profesional(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_actualizar.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_usuario(
                conexion,
                username="odontologo_ficticio",
                password_hash=hashear(CLAVE_FICTICIA),
                rol=Rol.ODONTOLOGO,
                profesional_id=2,
            )
            assert creado.id is not None
            actualizado = actualizar_usuario(
                conexion,
                creado.id,
                rol=Rol.RECEPCION,
                profesional_id=None,
                activo=False,
            )

        assert actualizado == Usuario(
            id=creado.id,
            username="odontologo_ficticio",
            rol=Rol.RECEPCION,
            profesional_id=None,
            activo=False,
        )


def test_actualizar_usuario_conserva_los_campos_omitidos(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_actualizar_omitidos.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_usuario(
                conexion,
                username="odontologo_ficticio",
                password_hash=hashear(CLAVE_FICTICIA),
                rol=Rol.ODONTOLOGO,
                profesional_id=2,
            )
            assert creado.id is not None
            actualizado = actualizar_usuario(conexion, creado.id, activo=False)

        assert actualizado == Usuario(
            id=creado.id,
            username="odontologo_ficticio",
            rol=Rol.ODONTOLOGO,
            profesional_id=2,
            activo=False,
        )


def test_actualizar_usuario_reemplaza_el_hash(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_actualizar_hash.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = _crear_admin(conexion)
            assert creado.id is not None
            actualizar_usuario(conexion, creado.id, password_hash=hashear(OTRA_CLAVE_FICTICIA))

        credenciales = buscar_credenciales(conexion, "admin_ficticio")
        assert credenciales is not None
        _, password_hash = credenciales
        assert verificar(OTRA_CLAVE_FICTICIA, password_hash)
        assert not verificar(CLAVE_FICTICIA, password_hash)


def test_actualizar_usuario_sin_hash_conserva_el_original(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_actualizar_sin_hash.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = _crear_admin(conexion)
        original = buscar_credenciales(conexion, "admin_ficticio")
        assert original is not None
        assert creado.id is not None

        with transaccion(conexion):
            actualizado = actualizar_usuario(conexion, creado.id, activo=False)

        assert actualizado is not None
        assert actualizado.activo is False
        despues = buscar_credenciales(conexion, "admin_ficticio")
        assert despues is not None
        assert despues[1] == original[1]


def test_actualizar_usuario_inexistente_devuelve_none(tmp_path: Path) -> None:
    ruta = tmp_path / "usuarios_actualizar_inexistente.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            assert actualizar_usuario(conexion, 9999, activo=False) is None
