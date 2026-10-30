"""Acceso a las tablas `turno` y `auditoria_turno` (C-11). Solo SQL parametrizado (regla dura 4).

Importa de `app.domain` solo tipos (regla dura 1). Las fechas se guardan con
`isoformat(timespec="seconds")` y se leen con `datetime.fromisoformat()` (design D4).
"""

import json
import sqlite3
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from typing import Final, Literal, cast

from app.domain.models import EstadoTurno, Turno

# Orden de columnas que espera `turno_desde_fila`; lo reutilizan C-12, C-13 y C-14.
COLUMNAS_TURNO: Final = "id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado"

AccionAuditoria = Literal["crear", "cancelar", "reprogramar"]

# SQL como literales completos (sin armar texto con f-strings ni concatenación).
_SELECT_POR_ID: Final = """
    SELECT id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado
    FROM turno WHERE id = ?
"""

_INSERTAR_TURNO: Final = """
    INSERT INTO turno (paciente_id, profesional_id, sillon_id, prestacion_id,
                       inicio, fin, estado, creado_por, creado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
_INSERTAR_AUDITORIA: Final = """
    INSERT INTO auditoria_turno (turno_id, accion, usuario_id, ocurrio_en, antes, despues)
    VALUES (?, ?, ?, ?, ?, ?)
"""

_ACTUALIZAR_ESTADO: Final = "UPDATE turno SET estado = ? WHERE id = ?"

_SELECT_ACTIVOS_DEL_DIA: Final = """
    SELECT id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado
    FROM turno
    WHERE estado = 'reservado'
      AND (profesional_id = ? OR sillon_id = ? OR paciente_id = ?)
      AND inicio < ? AND fin > ?
    ORDER BY inicio ASC, id ASC
"""

_FilaTurno = tuple[int, int, int, int, int, str, str, str]


def turno_desde_fila(fila: _FilaTurno) -> Turno:
    """Convierte una fila (en el orden de `COLUMNAS_TURNO`) en un `Turno` con fechas naive."""
    id_turno, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado = fila
    return Turno(
        id=id_turno,
        paciente_id=paciente_id,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion_id=prestacion_id,
        inicio=datetime.fromisoformat(inicio),
        fin=datetime.fromisoformat(fin),
        estado=cast(EstadoTurno, estado),
    )


def obtener_turno(conexion: sqlite3.Connection, turno_id: int) -> Turno | None:
    """Devuelve el turno por id o None si no existe."""
    fila = conexion.execute(_SELECT_POR_ID, (turno_id,)).fetchone()
    return None if fila is None else turno_desde_fila(fila)


def snapshot_turno(turno: Turno) -> str:
    """JSON canónico de un turno para `antes`/`despues` de la auditoría (design D2).

    Exactamente 8 claves, en orden fijo; sin `creado_por`/`creado_en` ni datos personales.
    """
    return json.dumps(
        {
            "id": turno.id,
            "paciente_id": turno.paciente_id,
            "profesional_id": turno.profesional_id,
            "sillon_id": turno.sillon_id,
            "prestacion_id": turno.prestacion_id,
            "inicio": turno.inicio.isoformat(timespec="seconds"),
            "fin": turno.fin.isoformat(timespec="seconds"),
            "estado": turno.estado,
        },
        ensure_ascii=False,
    )


def registrar_auditoria(
    conexion: sqlite3.Connection,
    *,
    turno_id: int,
    accion: AccionAuditoria,
    usuario_id: int,
    ocurrio_en: datetime,
    antes: str | None,
    despues: str,
) -> None:
    """Agrega un registro a `auditoria_turno`. Solo INSERT: la tabla es append-only (RN-AUD-02).

    Precondición: se llama dentro de `transaccion(...)` junto con la escritura del turno (RN-AUD-03).
    """
    conexion.execute(
        _INSERTAR_AUDITORIA,
        (turno_id, accion, usuario_id, ocurrio_en.isoformat(timespec="seconds"), antes, despues),
    )


def crear_turno(
    conexion: sqlite3.Connection,
    turno: Turno,
    *,
    creado_por: int,
    creado_en: datetime,
) -> Turno:
    """Inserta el turno y su registro de auditoría `crear`, y devuelve el turno con su id.

    Precondición: se llama dentro de `transaccion(...)`; la atomicidad (RN-AUD-03) la da esa
    transacción. `ocurrio_en` de la auditoría es igual a `creado_en`.
    """
    cursor = conexion.execute(
        _INSERTAR_TURNO,
        (
            turno.paciente_id,
            turno.profesional_id,
            turno.sillon_id,
            turno.prestacion_id,
            turno.inicio.isoformat(timespec="seconds"),
            turno.fin.isoformat(timespec="seconds"),
            turno.estado,
            creado_por,
            creado_en.isoformat(timespec="seconds"),
        ),
    )
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id del turno insertado.")
    creado = replace(turno, id=cursor.lastrowid)
    registrar_auditoria(
        conexion,
        turno_id=cursor.lastrowid,
        accion="crear",
        usuario_id=creado_por,
        ocurrio_en=creado_en,
        antes=None,
        despues=snapshot_turno(creado),
    )
    return creado


def cancelar_turno(
    conexion: sqlite3.Connection,
    antes: Turno,
    despues: Turno,
    *,
    usuario_id: int,
    ocurrio_en: datetime,
) -> None:
    """Guarda la cancelación que ya validó el dominio y su registro de auditoría `cancelar` (C-12).

    No llama al dominio (regla dura 1): recibe el turno original y el devuelto por
    `validar_cancelacion`. Precondición: se llama dentro de `transaccion(...)` (RN-AUD-03).
    """
    if antes.id is None:
        raise RuntimeError("El turno a cancelar debe tener id.")
    conexion.execute(_ACTUALIZAR_ESTADO, (despues.estado, antes.id))
    registrar_auditoria(
        conexion,
        turno_id=antes.id,
        accion="cancelar",
        usuario_id=usuario_id,
        ocurrio_en=ocurrio_en,
        antes=snapshot_turno(antes),
        despues=snapshot_turno(despues),
    )


def listar_turnos_activos_del_dia(
    conexion: sqlite3.Connection,
    *,
    dia: date,
    profesional_id: int,
    sillon_id: int,
    paciente_id: int,
) -> list[Turno]:
    """Turnos `reservado` del día que comparten profesional, sillón o paciente.

    Usa la ventana semiabierta `[dia 00:00, dia+1 00:00)`. Se filtra por día y no por el
    intervalo exacto porque el `fin` lo calcula el dominio; el solapamiento lo decide el dominio.
    """
    desde = datetime.combine(dia, time.min)
    hasta = desde + timedelta(days=1)
    filas = conexion.execute(
        _SELECT_ACTIVOS_DEL_DIA,
        (
            profesional_id,
            sillon_id,
            paciente_id,
            hasta.isoformat(timespec="seconds"),
            desde.isoformat(timespec="seconds"),
        ),
    ).fetchall()
    return [turno_desde_fila(fila) for fila in filas]
