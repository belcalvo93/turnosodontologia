"""Tests del verificador de trazabilidad RN -> test (C-17, specs/base-tecnica/spec.md)."""

from pathlib import Path

from tests.trazabilidad import (
    codigos_de_reglas,
    filas_de_tabla,
    hallazgos,
    tests_existentes,
)

RAIZ_REPO = Path(__file__).resolve().parent.parent
RUTA_KB_REGLAS = RAIZ_REPO / "knowledge-base" / "05_reglas_de_negocio.md"
RUTA_TRAZABILIDAD = RAIZ_REPO / "docs" / "trazabilidad-rn-test.md"


def test_todas_las_reglas_del_repositorio_estan_mapeadas_sin_hallazgos() -> None:
    """Escenario 'Todas las reglas están mapeadas' (specs/base-tecnica/spec.md)."""
    reglas = codigos_de_reglas(RUTA_KB_REGLAS.read_text(encoding="utf-8"))
    filas = filas_de_tabla(RUTA_TRAZABILIDAD.read_text(encoding="utf-8"))
    existentes = tests_existentes(RAIZ_REPO)

    assert len(reglas) == 31
    assert hallazgos(reglas, filas, existentes) == []
    assert filas["RN-TUR-13"].test == filas["RN-TUR-04"].test
    assert filas["RN-GLO-02"].estado.startswith("No aplica")
    assert filas["RN-GLO-02"].motivo != ""


def test_una_regla_sin_fila_falla_nombrando_el_codigo() -> None:
    """Escenario 'Una regla sin fila hace fallar la verificación'."""
    texto_kb = "- **RN-PRO-01**: Regla A.\n- **RN-PRO-99**: Regla faltante.\n"
    texto_tabla = (
        "| RN | Regla | Test | Estado |\n"
        "|---|---|---|---|\n"
        "| RN-PRO-01 | Regla A | `tests/domain/test_algo.py::test_a` | cubierta |\n"
    )
    reglas = codigos_de_reglas(texto_kb)
    filas = filas_de_tabla(texto_tabla)
    existentes = {"tests/domain/test_algo.py::test_a"}

    problemas = hallazgos(reglas, filas, existentes)

    assert len(problemas) == 1
    assert "RN-PRO-99" in problemas[0]


def test_un_test_citado_inexistente_falla_nombrando_el_nodo() -> None:
    """Escenario 'Un test citado inexistente hace fallar la verificación'."""
    nodo_inexistente = "tests/api/test_fantasma.py::test_no_existe"
    texto_kb = "- **RN-PRO-01**: Regla A.\n"
    texto_tabla = (
        "| RN | Regla | Test | Estado |\n"
        "|---|---|---|---|\n"
        f"| RN-PRO-01 | Regla A | `{nodo_inexistente}` | cubierta |\n"
    )
    reglas = codigos_de_reglas(texto_kb)
    filas = filas_de_tabla(texto_tabla)

    problemas = hallazgos(reglas, filas, {"tests/domain/test_algo.py::test_a"})

    assert len(problemas) == 1
    assert nodo_inexistente in problemas[0]


def test_no_aplica_solo_vale_para_rn_glo_02_y_con_motivo() -> None:
    """Escenario 'No aplica solo vale para RN-GLO-02 y con motivo'."""
    texto_kb_pac = "- **RN-PAC-01**: Regla de paciente.\n"
    tabla_pac_no_aplica = (
        "| RN | Regla | Test | Estado |\n"
        "|---|---|---|---|\n"
        "| RN-PAC-01 | Paciente | — | No aplica (motivo impropio) |\n"
    )
    problemas_pac = hallazgos(
        codigos_de_reglas(texto_kb_pac),
        filas_de_tabla(tabla_pac_no_aplica),
        set(),
    )
    assert any("RN-PAC-01" in p for p in problemas_pac)

    texto_kb_glo = "- **RN-GLO-02**: Fuera del MVP.\n"
    tabla_glo_sin_motivo = (
        "| RN | Regla | Test | Estado |\n"
        "|---|---|---|---|\n"
        "| RN-GLO-02 | Fuera del MVP | — | No aplica |\n"
    )
    problemas_glo = hallazgos(
        codigos_de_reglas(texto_kb_glo),
        filas_de_tabla(tabla_glo_sin_motivo),
        set(),
    )
    assert any("RN-GLO-02" in p for p in problemas_glo)


def test_una_tabla_completa_con_rn_glo_02_con_motivo_no_reporta_nada() -> None:
    """Escenario 'Una regla sin test verificable no rompe la tabla'."""
    texto_kb = (
        "- **RN-TUR-04**: Intervalos semiabiertos.\n"
        "- **RN-TUR-13**: Sin margen de limpieza.\n"
        "- **RN-GLO-02**: Fuera del MVP.\n"
    )
    nodo = "tests/domain/test_intervalos.py::test_turnos_contiguos_no_solapan"
    texto_tabla = (
        "| RN | Regla | Test | Estado |\n"
        "|---|---|---|---|\n"
        f"| RN-TUR-04 | Intervalos semiabiertos | `{nodo}` | cubierta |\n"
        f"| RN-TUR-13 | Sin margen de limpieza | `{nodo}` | cubierta |\n"
        "| RN-GLO-02 | Fuera del MVP | — | No aplica: declara una ausencia de funcionalidad del MVP |\n"
    )

    problemas = hallazgos(
        codigos_de_reglas(texto_kb),
        filas_de_tabla(texto_tabla),
        {nodo},
    )

    assert problemas == []
