"""Tests del esquema y repositorio SQLite de pacientes (C-06)."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from app.db.conexion import abrir_conexion, inicializar_esquema, transaccion
from app.db.repositorio_pacientes import (
    actualizar_paciente,
    crear_paciente,
    listar_pacientes,
    obtener_paciente_por_id,
)
from app.domain.errores import DniDuplicado
from app.domain.models import Paciente


def test_inicializar_esquema_crea_tabla_paciente_idempotente(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_esquema.db"

    inicializar_esquema(ruta)
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        fila = conexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'paciente'"
        ).fetchone()
        assert fila == ("paciente",)


def test_tabla_paciente_rechaza_nombre_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_nombre_vacio.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("", "Pérez", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_nombre_solo_espacios(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_nombre_espacios.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("   ", "Pérez", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_apellido_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_apellido_vacio.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_apellido_solo_espacios(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_apellido_espacios.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "   ", "30111222 (ficticio)"),
        )


def test_tabla_paciente_rechaza_dni_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_vacio.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", ""),
        )


def test_tabla_paciente_rechaza_dni_solo_espacios(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_espacios.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", "   "),
        )


def test_tabla_paciente_rechaza_dni_duplicado(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_duplicado.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", "30111222 (ficticio)"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conexion.execute(
                "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
                ("Luis", "Gómez", "30111222 (ficticio)"),
            )


def test_tabla_paciente_rechaza_dni_null(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_dni_null.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", None),
        )


def test_tabla_paciente_acepta_opcionales_null(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_opcionales_null.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        conexion.execute(
            "INSERT INTO paciente (nombre, apellido, dni) VALUES (?, ?, ?)",
            ("Ana", "Pérez", "30111222 (ficticio)"),
        )
        fila = conexion.execute(
            "SELECT nombre, apellido, dni, telefono, obra_social, nro_afiliado "
            "FROM paciente WHERE id = ?",
            (1,),
        ).fetchone()
        assert fila == ("Ana", "Pérez", "30111222 (ficticio)", None, None, None)


def test_crear_y_obtener_paciente_por_id(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_crear_obtener.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
                telefono="3884000001",
                obra_social="Obra Social Norte (ficticia)",
                nro_afiliado="AF-001 (ficticio)",
            )

        assert creado == Paciente(
            id=1,
            nombre="Ana",
            apellido="Pérez",
            dni="30111222 (ficticio)",
            telefono="3884000001",
            obra_social="Obra Social Norte (ficticia)",
            nro_afiliado="AF-001 (ficticio)",
        )
        assert obtener_paciente_por_id(conexion, 1) == creado


def test_obtener_paciente_por_id_inexistente_devuelve_none(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_obtener_inexistente.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        assert obtener_paciente_por_id(conexion, 999) is None


def test_listar_pacientes_devuelve_ordenados_por_id(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_listar.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            primero = crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )
            segundo = crear_paciente(
                conexion,
                nombre="Luis",
                apellido="Gómez",
                dni="30222333 (ficticio)",
                obra_social="Obra Social Sur (ficticia)",
            )

        assert listar_pacientes(conexion) == [primero, segundo]


def test_actualizar_paciente_modifica_nombre_y_apellido(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_actualizar_nombre_apellido.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )
            assert creado.id is not None
            actualizado = actualizar_paciente(
                conexion,
                creado.id,
                nombre="Ana María",
                apellido="Pérez López",
            )

        assert actualizado == Paciente(
            id=creado.id,
            nombre="Ana María",
            apellido="Pérez López",
            dni="30111222 (ficticio)",
        )


def test_actualizar_paciente_modifica_dni(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_actualizar_dni.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )
            assert creado.id is not None
            actualizado = actualizar_paciente(
                conexion,
                creado.id,
                dni="30999888 (ficticio)",
            )

        assert actualizado == Paciente(
            id=creado.id,
            nombre="Ana",
            apellido="Pérez",
            dni="30999888 (ficticio)",
        )


def test_actualizar_paciente_modifica_telefono_obra_social_y_nro_afiliado(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "pacientes_actualizar_opcionales.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )
            assert creado.id is not None
            actualizado = actualizar_paciente(
                conexion,
                creado.id,
                telefono="3884123456",
                obra_social="Obra Social Centro (ficticia)",
                nro_afiliado="AF-777 (ficticio)",
            )

        assert actualizado == Paciente(
            id=creado.id,
            nombre="Ana",
            apellido="Pérez",
            dni="30111222 (ficticio)",
            telefono="3884123456",
            obra_social="Obra Social Centro (ficticia)",
            nro_afiliado="AF-777 (ficticio)",
        )


def test_actualizar_paciente_limpia_opcional_con_none(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_limpiar_opcional.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
                telefono="3884123456",
                obra_social="Obra Social Centro (ficticia)",
                nro_afiliado="AF-777 (ficticio)",
            )
            assert creado.id is not None
            actualizado = actualizar_paciente(
                conexion,
                creado.id,
                telefono=None,
            )

        assert actualizado == Paciente(
            id=creado.id,
            nombre="Ana",
            apellido="Pérez",
            dni="30111222 (ficticio)",
            telefono=None,
            obra_social="Obra Social Centro (ficticia)",
            nro_afiliado="AF-777 (ficticio)",
        )


def test_actualizar_paciente_inexistente_devuelve_none(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_actualizar_inexistente.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion, transaccion(conexion):
        assert actualizar_paciente(conexion, 9999, nombre="Ana") is None


def test_crear_paciente_con_dni_duplicado_lanza_dni_duplicado(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_crear_duplicado.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )

        with pytest.raises(DniDuplicado), transaccion(conexion):
            crear_paciente(
                conexion,
                nombre="Luis",
                apellido="Gómez",
                dni="30111222 (ficticio)",
            )


def test_actualizar_paciente_a_dni_existente_lanza_dni_duplicado(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_actualizar_duplicado.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )
            segundo = crear_paciente(
                conexion,
                nombre="Luis",
                apellido="Gómez",
                dni="30222333 (ficticio)",
            )

        assert segundo.id is not None
        with pytest.raises(DniDuplicado), transaccion(conexion):
            actualizar_paciente(
                conexion,
                segundo.id,
                dni="30111222 (ficticio)",
            )


def test_actualizar_paciente_a_su_mismo_dni_no_lanza_conflicto(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_actualizar_mismo_dni.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            creado = crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )
            assert creado.id is not None
            actualizado = actualizar_paciente(
                conexion,
                creado.id,
                dni="30111222 (ficticio)",
            )

        assert actualizado == creado


def test_mensaje_de_dni_duplicado_no_contiene_el_dni_recibido(tmp_path: Path) -> None:
    ruta = tmp_path / "pacientes_mensaje_duplicado.db"
    inicializar_esquema(ruta)
    dni_repetido = "30111222 (ficticio)"

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni=dni_repetido,
            )

        with pytest.raises(DniDuplicado) as info_error, transaccion(conexion):
            crear_paciente(
                conexion,
                nombre="Luis",
                apellido="Gómez",
                dni=dni_repetido,
            )

        assert dni_repetido not in str(info_error.value)
        assert "30111222" not in str(info_error.value)


def test_integrity_error_no_unique_se_propaga_sin_traducir_a_dni_duplicado(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "pacientes_integrity_no_unique.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with pytest.raises(sqlite3.IntegrityError) as info_error, transaccion(conexion):
            crear_paciente(
                conexion,
                nombre="   ",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )

        assert not isinstance(info_error.value, DniDuplicado)


def test_fila_conserva_valores_previos_tras_intento_de_dni_duplicado(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "pacientes_conserva_valores_previos.db"
    inicializar_esquema(ruta)

    with closing(abrir_conexion(ruta)) as conexion:
        with transaccion(conexion):
            crear_paciente(
                conexion,
                nombre="Ana",
                apellido="Pérez",
                dni="30111222 (ficticio)",
            )
            segundo = crear_paciente(
                conexion,
                nombre="Luis",
                apellido="Gómez",
                dni="30222333 (ficticio)",
                telefono="3884000009",
            )

        assert segundo.id is not None
        with pytest.raises(DniDuplicado), transaccion(conexion):
            actualizar_paciente(
                conexion,
                segundo.id,
                nombre="Nombre Fallido",
                dni="30111222 (ficticio)",
            )

        assert obtener_paciente_por_id(conexion, segundo.id) == segundo
