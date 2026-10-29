import ast
import importlib
from pathlib import Path

from app.domain.errores import (
    ConflictoAgenda,
    DatoInvalido,
    DentroDeBloqueo,
    ErrorDominio,
    FueraDeHorario,
    TurnoNoModificable,
)
from app.domain.models import Bloqueo, HorarioAtencion, Prestacion, Turno

MODULOS_PROHIBIDOS = {"fastapi", "pydantic", "sqlite3", "starlette"}
LLAMADAS_RELOJ_PROHIBIDAS = {"now", "today", "utcnow"}


def test_paquete_dominio_es_importable() -> None:
    modulo = importlib.import_module("app.domain")
    assert modulo.__name__ == "app.domain"


def test_errores_base_de_dominio_heredan_de_error_dominio() -> None:
    for clase_error in (
        DatoInvalido,
        ConflictoAgenda,
        FueraDeHorario,
        DentroDeBloqueo,
        TurnoNoModificable,
    ):
        assert issubclass(clase_error, ErrorDominio)


def test_modelos_base_de_agenda_son_inmutables() -> None:
    for modelo in (Turno, Prestacion, HorarioAtencion, Bloqueo):
        assert modelo.__dataclass_params__.frozen is True


def test_dominio_no_importa_framework_ni_capas_externas_ni_reloj_del_sistema() -> None:
    carpeta_dominio = Path(__file__).resolve().parents[2] / "app" / "domain"
    archivos_py = list(carpeta_dominio.glob("*.py"))
    assert archivos_py

    for ruta in archivos_py:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    raiz = alias.name.split(".")[0]
                    assert raiz not in MODULOS_PROHIBIDOS, f"{ruta.name} importa {alias.name}"
                    assert not alias.name.startswith(("app.api", "app.db"))
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                raiz = nodo.module.split(".")[0]
                assert raiz not in MODULOS_PROHIBIDOS, f"{ruta.name} importa {nodo.module}"
                assert not nodo.module.startswith(("app.api", "app.db"))
            elif isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                assert (
                    nodo.func.attr not in LLAMADAS_RELOJ_PROHIBIDAS
                ), f"{ruta.name} invoca {nodo.func.attr}()"
