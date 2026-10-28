"""Router solo de test: rutas que lanzan errores para probar el mapeo a JSON (C-03).

Ninguna de estas rutas existe en `app/`; la fixture `cliente_con_rutas_prueba`
las monta sobre una app de test.
"""

from fastapi import APIRouter

from app.domain.errores import ConflictoAgenda, DatoInvalido, DentroDeBloqueo, FueraDeHorario

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
