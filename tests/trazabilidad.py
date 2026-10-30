"""Helpers puros de verificación de trazabilidad RN -> test (C-17, design D-F/D-G)."""

import ast
from dataclasses import dataclass
from pathlib import Path
import re

_PATRON_REGLA_KB = re.compile(r"^\s*-\s*\*\*(RN-[A-Z]{3}-\d{2})\*\*:", re.MULTILINE)
_PATRON_CODIGO_RN = re.compile(r"^RN-[A-Z]{3}-\d{2}$")
_UNICA_REGLA_NO_APLICA = "RN-GLO-02"


@dataclass(frozen=True)
class FilaTrazabilidad:
    """Una fila de la tabla de trazabilidad RN -> test."""

    codigo: str
    regla: str
    test: str
    estado: str
    motivo: str


def codigos_de_reglas(texto_kb: str) -> list[str]:
    """Extrae los códigos `RN-XXX-NN` declarados en `knowledge-base/05_reglas_de_negocio.md`."""
    vistos: set[str] = set()
    codigos: list[str] = []
    for coincidencia in _PATRON_REGLA_KB.finditer(texto_kb):
        codigo = coincidencia.group(1)
        if codigo not in vistos:
            vistos.add(codigo)
            codigos.append(codigo)
    return codigos


def filas_de_tabla(texto_tabla: str) -> dict[str, FilaTrazabilidad]:
    """Parsea la tabla markdown `| RN | Regla | Test | Estado |` y devuelve las filas por código."""
    filas: dict[str, FilaTrazabilidad] = {}
    for linea in texto_tabla.splitlines():
        limpia = linea.strip()
        if not limpia.startswith("|") or not limpia.endswith("|"):
            continue
        celdas = [celda.strip() for celda in limpia.strip("|").split("|")]
        if len(celdas) < 4:
            continue
        codigo = celdas[0].strip("` ").strip()
        if not _PATRON_CODIGO_RN.match(codigo):
            continue
        regla = celdas[1]
        test = celdas[2].strip("` ").strip()
        estado = celdas[3]
        motivo = _extraer_motivo_no_aplica(estado)
        filas[codigo] = FilaTrazabilidad(
            codigo=codigo,
            regla=regla,
            test=test,
            estado=estado,
            motivo=motivo,
        )
    return filas


def _extraer_motivo_no_aplica(estado: str) -> str:
    prefijo = "no aplica"
    texto = estado.strip()
    if not texto.lower().startswith(prefijo):
        return ""
    resto = texto[len(prefijo) :].strip()
    if resto.startswith(":"):
        return resto[1:].strip()
    if resto.startswith("(") and resto.endswith(")"):
        return resto[1:-1].strip()
    if resto.startswith("-") or resto.startswith("—"):
        return resto[1:].strip()
    return resto


def tests_existentes(raiz: Path) -> set[str]:
    """Recorre `tests/**/test_*.py` con `ast` y devuelve el conjunto `ruta_posix::funcion`."""
    carpeta_tests = raiz / "tests"
    nodos: set[str] = set()
    for archivo in carpeta_tests.rglob("test_*.py"):
        rel_posix = archivo.relative_to(raiz).as_posix()
        arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=rel_posix)
        for nodo in arbol.body:
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.name.startswith(
                "test_"
            ):
                nodos.add(f"{rel_posix}::{nodo.name}")
    return nodos


# Evita que pytest colecte este helper como test al importarlo en `test_*.py`.
tests_existentes.__test__ = False  # type: ignore[attr-defined]


def hallazgos(
    reglas: list[str],
    filas: dict[str, FilaTrazabilidad],
    existentes: set[str],
) -> list[str]:
    """Devuelve la lista de problemas de trazabilidad encontrados (vacía si todo es válido)."""
    problemas: list[str] = []
    for codigo in reglas:
        if codigo not in filas:
            problemas.append(f"Falta la regla {codigo} en la tabla de trazabilidad.")
            continue
        fila = filas[codigo]
        if fila.estado.strip().lower().startswith("no aplica"):
            if codigo != _UNICA_REGLA_NO_APLICA:
                problemas.append(
                    f"La regla {codigo} no puede figurar como 'No aplica' (solo {_UNICA_REGLA_NO_APLICA})."
                )
            elif not fila.motivo:
                problemas.append(
                    f"La regla {codigo} figura como 'No aplica' sin motivo explícito."
                )
            continue
        if "::" not in fila.test or fila.test not in existentes:
            problemas.append(
                f"La regla {codigo} cita un test inexistente o sin nodo exacto: {fila.test!r}."
            )

    if "RN-TUR-13" in filas and "RN-TUR-04" in filas:
        if filas["RN-TUR-13"].test != filas["RN-TUR-04"].test:
            problemas.append(
                "RN-TUR-13 debe citar exactamente el mismo test que RN-TUR-04."
            )
    return problemas
