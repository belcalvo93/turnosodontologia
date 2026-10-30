"""Acceso a la tabla `bloqueo` (C-09). Solo consultas parametrizadas (regla dura 4)."""

import sqlite3
from dataclasses import replace
from datetime import datetime
from typing import Final, cast

from app.domain.errores import DatoInvalido
from app.domain.models import AlcanceBloqueo, Bloqueo

_EXISTE_PROFESIONAL: Final = "SELECT 1 FROM profesional WHERE id = ?"
_EXISTE_SILLON: Final = "SELECT 1 FROM sillon WHERE id = ?"
_INSERTAR_BLOQUEO: Final = """
    INSERT INTO bloqueo (alcance, recurso_id, inicio, fin, motivo)
    VALUES (?, ?, ?, ?, ?)
"""
_SELECT_TODOS: Final = """
    SELECT id, alcance, recurso_id, inicio, fin, motivo
    FROM bloqueo
    ORDER BY inicio ASC, id ASC
"""
_DELETE_POR_ID: Final = "DELETE FROM bloqueo WHERE id = ?"

_FilaBloqueo = tuple[int, str, int, str, str, str]


def _existe_recurso(
    conexion: sqlite3.Connection, alcance: AlcanceBloqueo, recurso_id: int
) -> bool:
    consulta = _EXISTE_PROFESIONAL if alcance == "profesional" else _EXISTE_SILLON
    try:
        fila = conexion.execute(consulta, (recurso_id,)).fetchone()
    except sqlite3.OperationalError:
        return False
    return fila is not None


def crear_bloqueo(conexion: sqlite3.Connection, bloqueo: Bloqueo) -> Bloqueo:
    """Verifica que el recurso exista e inserta el bloqueo devolviéndolo con su id."""
    if not _existe_recurso(conexion, bloqueo.alcance, bloqueo.recurso_id):
        raise DatoInvalido("El recurso indicado para el bloqueo no existe.")
    cursor = conexion.execute(
        _INSERTAR_BLOQUEO,
        (
            bloqueo.alcance,
            bloqueo.recurso_id,
            bloqueo.inicio.isoformat(timespec="seconds"),
            bloqueo.fin.isoformat(timespec="seconds"),
            bloqueo.motivo,
        ),
    )
    if cursor.lastrowid is None:
        raise RuntimeError("SQLite no devolvió el id del bloqueo insertado.")
    return replace(bloqueo, id=cursor.lastrowid)


def listar_bloqueos(conexion: sqlite3.Connection) -> list[Bloqueo]:
    """Devuelve todos los bloqueos registrados ordenados por inicio e id."""
    filas = conexion.execute(_SELECT_TODOS).fetchall()
    return [_bloqueo_desde_fila(fila) for fila in filas]


def eliminar_bloqueo(conexion: sqlite3.Connection, id_bloqueo: int) -> bool:
    """Elimina el bloqueo por id y devuelve True si existía o False si no."""
    cursor = conexion.execute(_DELETE_POR_ID, (id_bloqueo,))
    return cursor.rowcount > 0


def _bloqueo_desde_fila(fila: _FilaBloqueo) -> Bloqueo:
    id_bloqueo, alcance, recurso_id, inicio, fin, motivo = fila
    return Bloqueo(
        id=id_bloqueo,
        alcance=cast(AlcanceBloqueo, alcance),
        recurso_id=recurso_id,
        inicio=datetime.fromisoformat(inicio),
        fin=datetime.fromisoformat(fin),
        motivo=motivo,
    )


_SELECT_DE_RECURSOS: Final = """
    SELECT id, alcance, recurso_id, inicio, fin, motivo
    FROM bloqueo
    WHERE ((alcance = 'profesional' AND recurso_id = ?) OR (alcance = 'sillon' AND recurso_id = ?))
      AND inicio < ? AND fin > ?
    ORDER BY inicio ASC, id ASC
"""


def listar_bloqueos_de_recursos(
    conexion: sqlite3.Connection,
    *,
    profesional_id: int,
    sillon_id: int,
    desde: datetime,
    hasta: datetime,
) -> list[Bloqueo]:
    """Bloqueos del profesional o del sillón que intersectan la ventana `[desde, hasta)` (C-11).

    Incluye bloqueos de varios días que cubren la ventana; los contiguos (que terminan en
    `desde` o empiezan en `hasta`) quedan fuera por el intervalo semiabierto.
    """
    filas = conexion.execute(
        _SELECT_DE_RECURSOS,
        (
            profesional_id,
            sillon_id,
            hasta.isoformat(timespec="seconds"),
            desde.isoformat(timespec="seconds"),
        ),
    ).fetchall()
    return [_bloqueo_desde_fila(fila) for fila in filas]
