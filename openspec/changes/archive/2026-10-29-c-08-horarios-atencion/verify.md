# Verify — C-08 horarios-atencion

- **Fecha:** 2026-10-29
- **Responsable:** Hernán
- **Comando:** `pytest tests -v`
- **Entorno:** Windows, Python 3.13.5, pytest 9.2.0, FastAPI 0.162.0, Starlette 1.10.0, PyJWT 2.15.1, pwdlib 0.3.1
- **Resultado:** `497 passed in 42.86s` (381 en `tests/api/` + 116 en `tests/domain/`), 1 warning. Sin tests fallidos ni salteados.
  - Por origen: 475 del baseline (`C-01`, `C-02`, `C-03`, `C-04`, `C-05`, `C-06`, `C-07`, `C-10`) + 22 nuevos de `C-08` (10 en `tests/domain/test_horarios.py`, 4 en `tests/api/test_repositorio_horarios.py` y 8 en `tests/api/test_horarios.py`).

## Cobertura de los escenarios del spec (`horarios-atencion`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta válida de franja horaria | `tests/api/test_horarios.py::test_post_horario_valido_responde_201` | PASSED |
| Franja invertida o con inicio igual a fin es rechazada | `tests/domain/test_horarios.py::test_validar_datos_horario_con_franja_invertida_o_igual_lanza_dato_invalido`, `tests/api/test_horarios.py::test_post_horario_con_franja_invertida_responde_422` | PASSED |
| Franja superpuesta en el mismo día es rechazada | `tests/domain/test_horarios.py::test_dos_franjas_en_el_mismo_dia_superpuestas_lanzan_dato_invalido`, `tests/api/test_horarios.py::test_post_horario_superpuesto_en_mismo_dia_responde_422` | PASSED |
| Dos franjas en el mismo día disjuntas o contiguas son aceptadas | `tests/domain/test_horarios.py::test_dos_franjas_en_el_mismo_dia_disjuntas_son_validas`, `tests/domain/test_horarios.py::test_dos_franjas_en_el_mismo_dia_contiguas_son_validas`, `tests/api/test_horarios.py::test_post_dos_horarios_disjuntos_en_mismo_dia_responde_201` | PASSED |
| Alta para profesional inexistente devuelve 422 | `tests/api/test_horarios.py::test_post_horario_con_profesional_inexistente_responde_422`, `tests/api/test_repositorio_horarios.py::test_crear_horario_con_profesional_inexistente_lanza_dato_invalido` | PASSED |
| Odontólogo consulta sus propios horarios | `tests/api/test_horarios.py::test_get_horarios_consulta_y_permisos` | PASSED |
| Odontólogo intenta consultar horarios de otro profesional | `tests/api/test_horarios.py::test_get_horarios_consulta_y_permisos` | PASSED |
| Recepción consulta horarios de cualquier profesional | `tests/api/test_horarios.py::test_get_horarios_consulta_y_permisos` | PASSED |
| Consulta sin autenticación | `tests/api/test_horarios.py::test_get_horarios_consulta_y_permisos` | PASSED |

## Chequeos adicionales

- **Límites de imports entre capas (regla dura 1 de `AGENTS.md`):** verificado en `tests/domain/test_estructura.py` que ningún módulo de `app/domain/` importa capas externas ni frameworks.
- **SQL parametrizado (regla dura 4 de `AGENTS.md`):** todas las consultas en `app/db/repositorio_horarios.py` utilizan exclusivamente marcadores `?`.
- **Formato de errores en español (`RN-GLO-01`, regla dura 7):** todos los rechazos de validación y permisos responden JSON `{codigo, mensaje}` en español.
