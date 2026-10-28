"""Router solo de test: rutas para probar el mapeo de errores y las dependencias (C-03).

Ninguna de estas rutas existe en `app/`; la fixture `cliente_con_rutas_prueba`
las monta sobre una app de test.
"""

import sqlite3
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.auth import requiere_rol, usuario_actual
from app.api.dependencias import obtener_ahora, obtener_conexion
from app.api.errores import CredencialesInvalidas, NoAutenticado, SinPermiso
from app.domain.errores import ConflictoAgenda, DatoInvalido, DentroDeBloqueo, FueraDeHorario
from app.domain.usuarios import Rol, Usuario

MENSAJE_CONFLICTO_AGENDA = "El profesional ya tiene un turno en ese horario (ficticio)."
MENSAJE_FUERA_DE_HORARIO = "El turno no encaja en una franja de atención (ficticio)."
MENSAJE_DENTRO_DE_BLOQUEO = "El turno cae dentro de un bloqueo (ficticio)."
MENSAJE_DATO_INVALIDO = "La duración del turno debe ser positiva (ficticio)."

router = APIRouter(prefix="/prueba")


@router.get("/error/conflicto-agenda")
def lanzar_conflicto_agenda() -> None:
    raise ConflictoAgenda(MENSAJE_CONFLICTO_AGENDA)


@router.get("/error/fuera-de-horario")
def lanzar_fuera_de_horario() -> None:
    raise FueraDeHorario(MENSAJE_FUERA_DE_HORARIO)


@router.get("/error/dentro-de-bloqueo")
def lanzar_dentro_de_bloqueo() -> None:
    raise DentroDeBloqueo(MENSAJE_DENTRO_DE_BLOQUEO)


@router.get("/error/dato-invalido")
def lanzar_dato_invalido() -> None:
    raise DatoInvalido(MENSAJE_DATO_INVALIDO)


@router.get("/error/no-autenticado")
def lanzar_no_autenticado() -> None:
    raise NoAutenticado()


@router.get("/error/credenciales-invalidas")
def lanzar_credenciales_invalidas() -> None:
    raise CredencialesInvalidas()


@router.get("/error/sin-permiso")
def lanzar_sin_permiso() -> None:
    raise SinPermiso()


class CuerpoPrueba(BaseModel):
    """Body con la forma del login, para probar la validación de entrada."""

    username: str
    password: str


@router.post("/validacion")
def validar_cuerpo(cuerpo: CuerpoPrueba) -> dict[str, str]:
    return {"username": cuerpo.username}


Conexion = Annotated[sqlite3.Connection, Depends(obtener_conexion)]
_TABLAS = "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"


# Las rutas guardan la conexión en `app.state` para que el test verifique que quedó cerrada.
@router.get("/conexion")
def usar_conexion(request: Request, conexion: Conexion) -> dict[str, list[str]]:
    request.app.state.conexion_prueba = conexion
    return {"tablas": [nombre for (nombre,) in conexion.execute(_TABLAS)]}


@router.get("/conexion/error")
def usar_conexion_y_fallar(request: Request, conexion: Conexion) -> None:
    request.app.state.conexion_prueba = conexion
    raise SinPermiso()


@router.get("/ahora")
def devolver_ahora(ahora: Annotated[datetime, Depends(obtener_ahora)]) -> dict[str, str]:
    return {"ahora": ahora.isoformat()}


@router.get("/autenticado")
def solo_autenticado(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> dict[str, object]:
    return {"id": usuario.id, "rol": usuario.rol.value}


@router.get("/solo-admin")
def solo_admin(
    usuario: Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))],
) -> dict[str, str]:
    return {"rol": usuario.rol.value}


@router.get("/admin-o-recepcion")
def admin_o_recepcion(
    usuario: Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION))],
) -> dict[str, str]:
    return {"rol": usuario.rol.value}


@router.get("/solo-recepcion")
def solo_recepcion(
    usuario: Annotated[Usuario, Depends(requiere_rol(Rol.RECEPCION))],
) -> dict[str, str]:
    return {"rol": usuario.rol.value}
