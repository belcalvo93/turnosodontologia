"""Mapeo global de errores a JSON `{codigo, mensaje, detalles?}` (C-03, RN-GLO-01)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


def registrar_manejadores(aplicacion: FastAPI) -> None:
    """Registra los handlers que convierten las excepciones en el formato de error."""
    aplicacion.add_exception_handler(ErrorDominio, _manejar_error_dominio)


async def _manejar_error_dominio(_: Request, exc: Exception) -> JSONResponse:
    mapeo = MAPEO_DOMINIO.get(type(exc))
    if mapeo is None:
        # Red de seguridad: un error de dominio sin mapeo no expone su mensaje interno.
        return _respuesta_error(500, "error_interno", "Error interno.")
    status, codigo = mapeo
    return _respuesta_error(status, codigo, str(exc))


def _respuesta_error(status: int, codigo: str, mensaje: str) -> JSONResponse:
    """Arma el cuerpo de error común a todos los handlers."""
    return JSONResponse(status_code=status, content={"codigo": codigo, "mensaje": mensaje})
