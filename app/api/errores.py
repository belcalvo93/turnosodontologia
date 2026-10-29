"""Mapeo global de errores a JSON `{codigo, mensaje, detalles?}` (C-03, RN-GLO-01)."""

from collections.abc import Mapping, Sequence
from types import MappingProxyType

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errores import (
    ConflictoAgenda,
    DatoInvalido,
    DentroDeBloqueo,
    DniDuplicado,
    ErrorDominio,
    FueraDeHorario,
    NombreDuplicado,
    TurnoNoModificable,
    UsernameDuplicado,
)

# Los 401 indican el esquema de autenticación esperado (RFC 6750). Solo lectura: se comparte.
_CABECERAS_BEARER: Mapping[str, str] = MappingProxyType({"WWW-Authenticate": "Bearer"})
_SIN_CABECERAS: Mapping[str, str] = MappingProxyType({})


class ErrorApi(Exception):
    """Base de los errores propios de la capa API (autenticación y permisos), no de dominio."""

    status: int
    codigo: str
    mensaje: str
    cabeceras: Mapping[str, str] = _SIN_CABECERAS

    def __init__(self) -> None:
        super().__init__(self.mensaje)


class NoAutenticado(ErrorApi):
    """Falta el token, o no es válido o venció (401)."""

    status = 401
    codigo = "no_autenticado"
    mensaje = "Se requiere un token de acceso válido."
    cabeceras = _CABECERAS_BEARER


class CredencialesInvalidas(ErrorApi):
    """Login fallido: usuario inexistente o inactivo, o contraseña incorrecta (401)."""

    status = 401
    codigo = "credenciales_invalidas"
    mensaje = "Usuario o contraseña incorrectos."
    cabeceras = _CABECERAS_BEARER


class SinPermiso(ErrorApi):
    """El rol del usuario autenticado no puede hacer la operación (403)."""

    status = 403
    codigo = "sin_permiso"
    mensaje = "Tu rol no tiene permiso para esta operación."


# Cada error de dominio se traduce a (status HTTP, codigo); el mensaje es str(exc),
# que el dominio ya trae en español.
MAPEO_DOMINIO: dict[type[ErrorDominio], tuple[int, str]] = {
    NombreDuplicado: (409, "nombre_duplicado"),
    DniDuplicado: (409, "dni_duplicado"),
    UsernameDuplicado: (409, "username_duplicado"),
    ConflictoAgenda: (409, "conflicto_agenda"),
    FueraDeHorario: (409, "fuera_de_horario"),
    DentroDeBloqueo: (409, "dentro_de_bloqueo"),
    TurnoNoModificable: (409, "turno_no_modificable"),
    DatoInvalido: (422, "dato_invalido"),
}

# Errores HTTP del framework (ruta inexistente, método no admitido): status → (codigo, mensaje).
_MAPEO_HTTP: dict[int, tuple[str, str]] = {
    404: ("no_encontrado", "El recurso solicitado no existe."),
    405: ("metodo_no_permitido", "El método HTTP no está permitido para este recurso."),
}
# Cualquier otro status conserva su número; el `detail` del framework no se expone.
_ERROR_HTTP_GENERICO = ("error_http", "No se pudo procesar la solicitud.")

# Mensajes en español por `type` de error de Pydantic; el texto original (en inglés) no se expone.
_MENSAJES_VALIDACION: dict[str, str] = {
    "missing": "Campo obligatorio.",
    "string_type": "Debe ser un texto.",
    "string_too_short": "No puede estar vacío.",
    "json_invalid": "El cuerpo no es un JSON válido.",
}
_MENSAJE_VALIDACION_GENERICO = "Valor inválido."
# `campo` de los errores que afectan a todo el cuerpo y no a un campo concreto.
_CAMPO_CUERPO = "body"


def registrar_manejadores(aplicacion: FastAPI) -> None:
    """Registra los handlers que convierten las excepciones en el formato de error."""
    aplicacion.add_exception_handler(ErrorApi, _manejar_error_api)
    aplicacion.add_exception_handler(ErrorDominio, _manejar_error_dominio)
    aplicacion.add_exception_handler(StarletteHTTPException, _manejar_error_http)
    aplicacion.add_exception_handler(RequestValidationError, _manejar_error_validacion)


async def _manejar_error_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    detalles = [
        {
            "campo": _campo_de_validacion(error["loc"], error["type"]),
            "mensaje": _MENSAJES_VALIDACION.get(error["type"], _MENSAJE_VALIDACION_GENERICO),
        }
        for error in exc.errors()
    ]
    return _respuesta_error(
        422, "dato_invalido", "Los datos enviados no son válidos.", detalles=detalles
    )


def _campo_de_validacion(loc: Sequence[str | int], tipo: str) -> str:
    """Nombre del campo con error: el `loc` sin su prefijo ("body", "query"...).

    Si el error es de todo el cuerpo (no es un objeto, o es un JSON mal formado,
    cuyo `loc` trae la posición del carácter), el campo es "body".
    """
    resto = loc[1:]
    if not resto or tipo == "json_invalid":
        return _CAMPO_CUERPO
    return ".".join(str(parte) for parte in resto)


async def _manejar_error_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    codigo, mensaje = _MAPEO_HTTP.get(exc.status_code, _ERROR_HTTP_GENERICO)
    respuesta = _respuesta_error(exc.status_code, codigo, mensaje)
    # Conserva cabeceras como `Allow` en el 405.
    respuesta.headers.update(exc.headers or {})
    return respuesta


async def _manejar_error_api(_: Request, exc: ErrorApi) -> JSONResponse:
    respuesta = _respuesta_error(exc.status, exc.codigo, exc.mensaje)
    respuesta.headers.update(exc.cabeceras)
    return respuesta


async def _manejar_error_dominio(_: Request, exc: ErrorDominio) -> JSONResponse:
    mapeo = MAPEO_DOMINIO.get(type(exc))
    if mapeo is None:
        # Red de seguridad: un error de dominio sin mapeo no expone su mensaje interno.
        return _respuesta_error(500, "error_interno", "Error interno.")
    status, codigo = mapeo
    return _respuesta_error(status, codigo, str(exc))


def _respuesta_error(
    status: int, codigo: str, mensaje: str, detalles: list[dict[str, str]] | None = None
) -> JSONResponse:
    """Arma el cuerpo de error común a todos los handlers; `detalles` solo si hay por campo."""
    cuerpo: dict[str, object] = {"codigo": codigo, "mensaje": mensaje}
    if detalles is not None:
        cuerpo["detalles"] = detalles
    return JSONResponse(status_code=status, content=cuerpo)
