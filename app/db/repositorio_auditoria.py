"""Lectura de la tabla `auditoria_turno` (C-15). Solo SQL parametrizado (regla dura 4).

Importa de `app.domain` solo tipos (regla dura 1). `antes`/`despues` se guardan como
texto JSON y se devuelven parseados; `ocurrio_en` se guarda con
`isoformat(timespec="seconds")` y se lee con `datetime.fromisoformat()` (C-11 D4).
"""

import json
import sqlite3
from datetime import datetime
from typing import Final, cast

from app.domain.models import AccionAuditoria, RegistroAuditoria

_SELECT_POR_TURNO: Final = """
    SELECT a.id, a.turno_id, a.accion, a.usuario_id, u.username,
           a.ocurrio_en, a.antes, a.despues
    FROM auditoria_turno AS a
    LEFT JOIN usuario AS u ON u.id = a.usuario_id
    WHERE a.turno_id = ?
    ORDER BY a.ocurrio_en ASC, a.id ASC
"""

_FilaAuditoria = tuple[int, int, str, int, str | None, str, str | None, str]


def _registro_desde_fila(fila: _FilaAuditoria) -> RegistroAuditoria:
    """Convierte una fila en un `RegistroAuditoria` con JSON parseado y fecha naive."""
    id_registro, turno_id, accion, usuario_id, username, ocurrio_en, antes, despues = fila
    return RegistroAuditoria(
        id=id_registro,
        turno_id=turno_id,
        accion=cast(AccionAuditoria, accion),
        usuario_id=usuario_id,
        username=username,
        ocurrio_en=datetime.fromisoformat(ocurrio_en),
        antes=None if antes is None else json.loads(antes),
        despues=json.loads(despues),
    )


def listar_auditoria_por_turno(
    conexion: sqlite3.Connection, turno_id: int
) -> list[RegistroAuditoria]:
    """Devuelve el historial de un turno en orden cronológico, desempatado por `id`.

    El desempate por `id` es obligatorio: `ocurrio_en` solo tiene precisión de segundos,
    así que varias acciones del mismo turno pueden compartir instante (C-15 D5).
    """
    filas = conexion.execute(_SELECT_POR_TURNO, (turno_id,)).fetchall()
    return [_registro_desde_fila(cast(_FilaAuditoria, fila)) for fila in filas]
