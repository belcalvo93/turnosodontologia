"""Mapeo global de errores a JSON `{codigo, mensaje, detalles?}` (C-03, RN-GLO-01)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errores import (
    ConflictoAgenda,
    DatoInvalido,
    DentroDeBloqueo,
    ErrorDominio,
    FueraDeHorario,
)

# Cada error de dominio se traduce a (status HTTP, codigo); el mensaje es str(exc),
# que el dominio ya trae en español.
MAPEO_DOMINIO: dict[type[ErrorDominio], tuple[int, str]] = {
    ConflictoAgenda: (409, "conflicto_agenda"),
    FueraDeHorario: (409, "fuera_de_horario"),
    DentroDeBloqueo: (409, "dentro_de_bloqueo"),
    DatoInvalido: (422, "dato_invalido"),
}

# Errores HTTP del framework (ruta inexistente, método no admitido): status → (codigo, mensaje).
_MAPEO_HTTP: dict[int, tuple[str, str]] = {
    404: ("no_encontrado", "El recurso solicitado no existe."),
    405: ("metodo_no_permitido", "El método HTTP no está permitido para este recurso."),
}
# Cualquier otro status conserva su número; el `detail` del framework no se expone.
_ERROR_HTTP_GENERICO = ("error_http", "No se pudo procesar la solicitud.")


def registrar_manejadores(aplicacion: FastAPI) -> None:
    """Registra los handlers que convierten las excepciones en el formato de error."""
    aplicacion.add_exception_handler(ErrorDominio, _manejar_error_dominio)
    aplicacion.add_exception_handler(StarletteHTTPException, _manejar_error_http)


async def _manejar_error_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    codigo, mensaje = _MAPEO_HTTP.get(exc.status_code, _ERROR_HTTP_GENERICO)
    respuesta = _respuesta_error(exc.status_code, codigo, mensaje)
    # Conserva cabeceras como `Allow` en el 405.
    respuesta.headers.update(exc.headers or {})
    return respuesta


async def _manejar_error_dominio(_: Request, exc: ErrorDominio) -> JSONResponse:
    mapeo = MAPEO_DOMINIO.get(type(exc))
    if mapeo is None:
        # Red de seguridad: un error de dominio sin mapeo no expone su mensaje interno.
        return _respuesta_error(500, "error_interno", "Error interno.")
    status, codigo = mapeo
    return _respuesta_error(status, codigo, str(exc))


def _respuesta_error(status: int, codigo: str, mensaje: str) -> JSONResponse:
    """Arma el cuerpo de error común a todos los handlers."""
    return JSONResponse(status_code=status, content={"codigo": codigo, "mensaje": mensaje})
