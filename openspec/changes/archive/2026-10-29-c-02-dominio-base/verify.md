# Verify — C-02 dominio-base

- **Fecha:** 2026-10-29
- **Responsable:** Hernán
- **Comando:** `pytest tests -v`
- **Entorno:** Windows, Python 3.13.5, pytest 9.2.0, FastAPI 0.162.0, Starlette 1.10.0, PyJWT 2.15.1, pwdlib 0.3.1
- **Resultado:** `475 passed in 39.41s` (369 en `tests/api/` + 106 en `tests/domain/`), 1 warning. Sin tests fallidos ni salteados.
  - Por origen: 467 del baseline (`C-01`, `C-10`, `C-03`, `C-04`, `C-05`, `C-06` y `C-07`) + 8 nuevos de `C-02` (4 en `tests/domain/test_intervalos.py`, 3 en `tests/domain/test_estructura.py` y 1 en `tests/api/test_errores.py`).

## Cobertura de los escenarios del spec (`dominio-base` y delta `errores-api`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Turnos contiguos no se superponen | `tests/domain/test_intervalos.py::test_turnos_contiguos_no_solapan` | PASSED |
| Solapamiento parcial entre dos intervalos | `tests/domain/test_intervalos.py::test_solapamiento_parcial_solapa` | PASSED |
| Intervalo completamente contenido dentro de otro | `tests/domain/test_intervalos.py::test_intervalo_contenido_solapa` | PASSED |
| Intervalos con el mismo instante de inicio | `tests/domain/test_intervalos.py::test_intervalos_con_mismo_inicio_solapan` | PASSED |
| Turno con inicio posterior al reloj inyectado es futuro | `tests/domain/test_intervalos.py::test_es_futuro_con_reloj_antes_del_inicio_devuelve_true` | PASSED |
| Turno con inicio igual al reloj inyectado no es futuro | `tests/domain/test_intervalos.py::test_es_futuro_con_reloj_igual_al_inicio_devuelve_false` | PASSED |
| Turno con inicio anterior al reloj inyectado no es futuro | `tests/domain/test_intervalos.py::test_es_futuro_con_reloj_despues_del_inicio_devuelve_false` | PASSED |
| Instanciación de modelos y jerarquía de errores sin dependencias externas | `tests/domain/test_estructura.py::test_errores_base_de_dominio_heredan_de_error_dominio`, `tests/domain/test_estructura.py::test_modelos_base_de_agenda_son_inmutables`, `tests/domain/test_estructura.py::test_dominio_no_importa_framework_ni_capas_externas_ni_reloj_del_sistema` | PASSED |
| Código 409 por turno no modificable | `tests/api/test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje[/prueba/error/turno-no-modificable-409-turno_no_modificable-...]` | PASSED |

## Chequeos adicionales

- **Límites de imports entre capas (regla dura 1 de `AGENTS.md`):** verificado mediante AST en `test_dominio_no_importa_framework_ni_capas_externas_ni_reloj_del_sistema` que ningún módulo de `app/domain/` importa `fastapi`, `pydantic`, `sqlite3`, `starlette`, `app.db` ni `app.api`.
- **Reloj inyectado (regla dura 2 de `AGENTS.md`):** verificado mediante AST que ningún módulo de `app/domain/` invoca `now()`, `today()` ni `utcnow()`.
- **Intervalos semiabiertos (regla dura 3 de `AGENTS.md`):** `solapan(a, b)` evalúa `[inicio, fin)` y acepta turnos contiguos (`a.fin == b.inicio`).
- **Mapeo global de errores (`RN-GLO-01`, regla dura 7):** `test_todo_error_de_dominio_de_la_app_tiene_entrada_en_el_mapeo` pasa en verde incluyendo `TurnoNoModificable -> (409, "turno_no_modificable")`.
