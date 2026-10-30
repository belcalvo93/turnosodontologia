"""Router de auditoría: consulta con GET /auditoria?turno_id= (C-15, US-014, Flujo 7).

El router solo orquesta: valida la forma de la entrada (Pydantic), consulta el
repositorio de lectura y serializa. La tabla es de solo agregado (RN-AUD-02), así
que este router no expone rutas de escritura.
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.auth import requiere_rol
from app.api.dependencias import obtener_conexion
from app.db.repositorio_auditoria import listar_auditoria_por_turno
from app.db.repositorio_turnos import obtener_turno
from app.domain.models import AccionAuditoria, RegistroAuditoria
from app.domain.usuarios import Rol, Usuario

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

ConexionDep = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
AdminDep = Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))]


class RegistroAuditoriaSalida(BaseModel):
    """Un registro del historial, sin datos sensibles del usuario ni del paciente."""

    id: int
    turno_id: int
    accion: AccionAuditoria
    usuario_id: int
    username: str | None
    ocurrio_en: str
    antes: dict[str, object] | None
    despues: dict[str, object]


class AuditoriaResponse(BaseModel):
    """Historial completo de un turno, envuelto con el id consultado (design D8)."""

    turno_id: int
    registros: list[RegistroAuditoriaSalida]


def _a_salida(registro: RegistroAuditoria) -> RegistroAuditoriaSalida:
    """Serializa `ocurrio_en` con el mismo formato ISO de segundos que los turnos."""
    return RegistroAuditoriaSalida(
        id=registro.id,
        turno_id=registro.turno_id,
        accion=registro.accion,
        usuario_id=registro.usuario_id,
        username=registro.username,
        ocurrio_en=registro.ocurrio_en.isoformat(timespec="seconds"),
        antes=registro.antes,
        despues=registro.despues,
    )


@router.get("")
def get_auditoria(
    turno_id: Annotated[int, Query(ge=1)],
    conexion: ConexionDep,
    usuario: AdminDep,
) -> AuditoriaResponse:
    """Devuelve el historial del turno en orden cronológico (solo administración).

    Un `turno_id` inexistente responde `404 no_encontrado` en vez de una lista vacía:
    un id mal tipeado no debe confundirse con un turno sin historial (design D6).
    """
    if obtener_turno(conexion, turno_id) is None:
        raise HTTPException(status_code=404)
    registros = listar_auditoria_por_turno(conexion, turno_id)
    return AuditoriaResponse(turno_id=turno_id, registros=[_a_salida(r) for r in registros])
