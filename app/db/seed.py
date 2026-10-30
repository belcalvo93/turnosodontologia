"""Seed de desarrollo: catálogo demo ficticio y usuarios demo (C-03, C-17).

Recibe los hashes ya calculados: `db` no importa nada de `api` (KB 08, regla dura 1).
Solo consultas parametrizadas (regla dura 4) y datos ficticios rotulados (RN-PAC-03, regla dura 10).
"""

from dataclasses import dataclass
import sqlite3
from typing import Final

from app.db.conexion import transaccion
from app.domain.usuarios import Rol

USERNAME_ADMIN_DEMO: Final = "admin_demo"
USERNAME_RECEPCION_DEMO: Final = "recepcion_demo"
USERNAME_ODONTOLOGO_DEMO: Final = "odontologo_demo"

# ON CONFLICT ... DO NOTHING: idempotente y nunca pisa la contraseña de un usuario existente.
_INSERTAR_USUARIO_DEMO: Final = """
    INSERT INTO usuario (username, password_hash, rol, profesional_id, activo)
    VALUES (?, ?, ?, ?, 1)
    ON CONFLICT(username) DO NOTHING
"""
_SELECT_ID_USUARIO: Final = "SELECT id FROM usuario WHERE username = ?"

_INSERTAR_PROFESIONAL_SI_NO_EXISTE: Final = """
    INSERT INTO profesional (nombre, apellido, matricula, activo)
    SELECT ?, ?, ?, 1
    WHERE NOT EXISTS (
        SELECT 1 FROM profesional
        WHERE nombre = ? AND apellido = ? AND matricula = ?
    )
"""
_SELECT_ID_PROFESIONAL: Final = """
    SELECT id FROM profesional
    WHERE nombre = ? AND apellido = ? AND matricula = ?
"""

_INSERTAR_HORARIO_SI_NO_EXISTE: Final = """
    INSERT INTO horario_atencion (profesional_id, dia_semana, hora_desde, hora_hasta)
    SELECT ?, ?, ?, ?
    WHERE NOT EXISTS (
        SELECT 1 FROM horario_atencion
        WHERE profesional_id = ? AND dia_semana = ? AND hora_desde = ? AND hora_hasta = ?
    )
"""

_INSERTAR_SILLON: Final = """
    INSERT INTO sillon (nombre, activo)
    VALUES (?, 1)
    ON CONFLICT(nombre) DO NOTHING
"""
_SELECT_ID_SILLON: Final = "SELECT id FROM sillon WHERE nombre = ?"

_INSERTAR_PRESTACION: Final = """
    INSERT INTO prestacion (nombre, duracion_minutos, activa)
    VALUES (?, ?, 1)
    ON CONFLICT(nombre) DO NOTHING
"""
_SELECT_ID_PRESTACION: Final = "SELECT id FROM prestacion WHERE nombre = ?"

_INSERTAR_PACIENTE: Final = """
    INSERT INTO paciente (nombre, apellido, dni, telefono, obra_social, nro_afiliado)
    VALUES (?, ?, ?, NULL, ?, NULL)
    ON CONFLICT(dni) DO NOTHING
"""
_SELECT_ID_PACIENTE: Final = "SELECT id FROM paciente WHERE dni = ?"

_DIAS_HABILES: Final = (0, 1, 2, 3, 4)
_FRANJAS_DEMO: Final = (("09:00", "13:00"), ("14:00", "18:00"))


@dataclass(frozen=True)
class DatosDemo:
    """Identificadores del catálogo y usuarios demo sembrados en la base."""

    profesional_a: int
    profesional_b: int
    sillon_1: int
    sillon_2: int
    consulta: int
    limpieza: int
    tratamiento: int
    paciente_1: int
    paciente_2: int
    admin_demo: int
    recepcion_demo: int | None
    odontologo_demo: int | None


def sembrar_admin_demo(conexion: sqlite3.Connection, password_hash: str) -> None:
    """Crea `admin_demo` (administración, activo) con `password_hash` si todavía no existe."""
    with transaccion(conexion):
        _insertar_usuario_demo(
            conexion,
            username=USERNAME_ADMIN_DEMO,
            password_hash=password_hash,
            rol=Rol.ADMINISTRACION,
            profesional_id=None,
        )


def sembrar_demo(
    conexion: sqlite3.Connection,
    *,
    password_hash_admin: str,
    password_hash_recepcion: str | None = None,
    password_hash_odontologo: str | None = None,
) -> DatosDemo:
    """Siembra de forma idempotente el catálogo demo (32 filas con las 3 claves) en una transacción."""
    with transaccion(conexion):
        profesional_a, profesional_b = _sembrar_profesionales(conexion)
        _sembrar_horarios(conexion, (profesional_a, profesional_b))
        sillon_1, sillon_2 = _sembrar_sillones(conexion)
        consulta, limpieza, tratamiento = _sembrar_prestaciones(conexion)
        paciente_1, paciente_2 = _sembrar_pacientes(conexion)
        admin_id, recepcion_id, odontologo_id = _sembrar_usuarios(
            conexion,
            profesional_a=profesional_a,
            password_hash_admin=password_hash_admin,
            password_hash_recepcion=password_hash_recepcion,
            password_hash_odontologo=password_hash_odontologo,
        )
    return DatosDemo(
        profesional_a=profesional_a,
        profesional_b=profesional_b,
        sillon_1=sillon_1,
        sillon_2=sillon_2,
        consulta=consulta,
        limpieza=limpieza,
        tratamiento=tratamiento,
        paciente_1=paciente_1,
        paciente_2=paciente_2,
        admin_demo=admin_id,
        recepcion_demo=recepcion_id,
        odontologo_demo=odontologo_id,
    )


def _sembrar_profesionales(conexion: sqlite3.Connection) -> tuple[int, int]:
    id_a = _asegurar_profesional(
        conexion,
        nombre="Odontólogo",
        apellido="Ficticio A",
        matricula="0001 (ficticia)",
    )
    id_b = _asegurar_profesional(
        conexion,
        nombre="Odontóloga",
        apellido="Ficticia B",
        matricula="0002 (ficticia)",
    )
    return id_a, id_b


def _asegurar_profesional(
    conexion: sqlite3.Connection, *, nombre: str, apellido: str, matricula: str
) -> int:
    clave = (nombre, apellido, matricula)
    conexion.execute(_INSERTAR_PROFESIONAL_SI_NO_EXISTE, (*clave, *clave))
    fila = conexion.execute(_SELECT_ID_PROFESIONAL, clave).fetchone()
    if fila is None:
        raise RuntimeError("No se encontró el profesional demo tras la siembra.")
    return int(fila[0])


def _sembrar_horarios(
    conexion: sqlite3.Connection, profesionales: tuple[int, int]
) -> None:
    for profesional_id in profesionales:
        for dia_semana in _DIAS_HABILES:
            for hora_desde, hora_hasta in _FRANJAS_DEMO:
                clave = (profesional_id, dia_semana, hora_desde, hora_hasta)
                conexion.execute(_INSERTAR_HORARIO_SI_NO_EXISTE, (*clave, *clave))


def _sembrar_sillones(conexion: sqlite3.Connection) -> tuple[int, int]:
    return (
        _asegurar_sillon(conexion, "Sillón 1"),
        _asegurar_sillon(conexion, "Sillón 2"),
    )


def _asegurar_sillon(conexion: sqlite3.Connection, nombre: str) -> int:
    conexion.execute(_INSERTAR_SILLON, (nombre,))
    fila = conexion.execute(_SELECT_ID_SILLON, (nombre,)).fetchone()
    if fila is None:
        raise RuntimeError("No se encontró el sillón demo tras la siembra.")
    return int(fila[0])


def _sembrar_prestaciones(conexion: sqlite3.Connection) -> tuple[int, int, int]:
    return (
        _asegurar_prestacion(conexion, "Consulta ficticia", 30),
        _asegurar_prestacion(conexion, "Limpieza ficticia", 45),
        _asegurar_prestacion(conexion, "Tratamiento ficticio", 60),
    )


def _asegurar_prestacion(
    conexion: sqlite3.Connection, nombre: str, duracion_minutos: int
) -> int:
    conexion.execute(_INSERTAR_PRESTACION, (nombre, duracion_minutos))
    fila = conexion.execute(_SELECT_ID_PRESTACION, (nombre,)).fetchone()
    if fila is None:
        raise RuntimeError("No se encontró la prestación demo tras la siembra.")
    return int(fila[0])


def _sembrar_pacientes(conexion: sqlite3.Connection) -> tuple[int, int]:
    id_1 = _asegurar_paciente(
        conexion,
        nombre="Paciente",
        apellido="Ficticio 1",
        dni="00000001 (ficticio)",
        obra_social="Obra Social Ficticia A",
    )
    id_2 = _asegurar_paciente(
        conexion,
        nombre="Paciente",
        apellido="Ficticio 2",
        dni="00000002 (ficticio)",
        obra_social=None,
    )
    return id_1, id_2


def _asegurar_paciente(
    conexion: sqlite3.Connection,
    *,
    nombre: str,
    apellido: str,
    dni: str,
    obra_social: str | None,
) -> int:
    conexion.execute(_INSERTAR_PACIENTE, (nombre, apellido, dni, obra_social))
    fila = conexion.execute(_SELECT_ID_PACIENTE, (dni,)).fetchone()
    if fila is None:
        raise RuntimeError("No se encontró el paciente demo tras la siembra.")
    return int(fila[0])


def _sembrar_usuarios(
    conexion: sqlite3.Connection,
    *,
    profesional_a: int,
    password_hash_admin: str,
    password_hash_recepcion: str | None,
    password_hash_odontologo: str | None,
) -> tuple[int, int | None, int | None]:
    admin_id = _insertar_usuario_demo(
        conexion,
        username=USERNAME_ADMIN_DEMO,
        password_hash=password_hash_admin,
        rol=Rol.ADMINISTRACION,
        profesional_id=None,
    )
    recepcion_id = (
        None
        if password_hash_recepcion is None
        else _insertar_usuario_demo(
            conexion,
            username=USERNAME_RECEPCION_DEMO,
            password_hash=password_hash_recepcion,
            rol=Rol.RECEPCION,
            profesional_id=None,
        )
    )
    odontologo_id = (
        None
        if password_hash_odontologo is None
        else _insertar_usuario_demo(
            conexion,
            username=USERNAME_ODONTOLOGO_DEMO,
            password_hash=password_hash_odontologo,
            rol=Rol.ODONTOLOGO,
            profesional_id=profesional_a,
        )
    )
    return admin_id, recepcion_id, odontologo_id


def _insertar_usuario_demo(
    conexion: sqlite3.Connection,
    *,
    username: str,
    password_hash: str,
    rol: Rol,
    profesional_id: int | None,
) -> int:
    conexion.execute(
        _INSERTAR_USUARIO_DEMO,
        (username, password_hash, rol.value, profesional_id),
    )
    fila = conexion.execute(_SELECT_ID_USUARIO, (username,)).fetchone()
    if fila is None:
        raise RuntimeError("No se encontró el usuario demo tras la siembra.")
    return int(fila[0])
