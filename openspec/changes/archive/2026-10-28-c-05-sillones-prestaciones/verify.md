# Verify — C-05 sillones-prestaciones

- **Fecha:** 2026-10-28
- **Responsable:** Belén Calvo
- **Comando:** `pytest tests -v`
- **Entorno:** Windows 11 Home (10.0.26300), Python 3.14.7, pytest 9.1.1, FastAPI 0.141.1, Starlette 1.7.0, Pydantic 2.13.5, PyJWT 2.15.1, pwdlib 0.3.1, httpx 0.28.1
- **Resultado:** `314 passed, 1 warning in 16.38s` (253 en `tests/api/` + 61 en `tests/domain/`). Sin tests fallidos, salteados ni errores.
  - Por origen: 220 del baseline (`C-01`, `C-10`, `C-03` y `C-04`) + 94 nuevos de `C-05` (5 en `tests/domain/test_sillones.py`, 7 en `tests/domain/test_prestaciones.py`, 16 en `tests/api/test_repositorio_sillones.py`, 21 en `tests/api/test_repositorio_prestaciones.py`, 19 en `tests/api/test_sillones.py`, 25 en `tests/api/test_prestaciones.py` y 1 caso parametrizado nuevo en `tests/api/test_errores.py`).

## Cobertura de los escenarios del spec (`sillones`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta válida de sillón | `tests/api/test_sillones.py::test_post_sillones_alta_valida_normaliza_el_nombre` | PASSED |
| Nombre de sillón duplicado | `tests/api/test_sillones.py::test_post_sillones_con_nombre_duplicado_responde_409`, `tests/api/test_repositorio_sillones.py::test_crear_sillon_con_nombre_duplicado_lanza_nombre_duplicado` | PASSED |
| Nombre de sillón vacío | `tests/api/test_sillones.py::test_post_sillones_con_nombre_vacio_responde_422`, `tests/api/test_sillones.py::test_post_sillones_con_nombre_solo_espacios_responde_422`, `tests/domain/test_sillones.py::test_validar_datos_sillon_con_nombre_vacio_lanza_dato_invalido[   ]` | PASSED |
| Listado incluye sillones desactivados | `tests/api/test_repositorio_sillones.py::test_listar_sillones_devuelve_activos_e_inactivos_ordenados_por_id`, `tests/api/test_sillones.py::test_patch_sillones_desactiva_y_el_sillon_sigue_en_el_listado`, `tests/api/test_sillones.py::test_get_sillones_permitido_para_los_tres_roles[administracion]` | PASSED |
| Desactivación lógica conserva el sillón | `tests/api/test_sillones.py::test_patch_sillones_desactiva_y_el_sillon_sigue_en_el_listado`, `tests/api/test_repositorio_sillones.py::test_baja_logica_de_sillon_conserva_la_fila` | PASSED |
| Renombrar a un nombre ya usado | `tests/api/test_sillones.py::test_patch_sillones_a_nombre_existente_responde_409`, `tests/api/test_repositorio_sillones.py::test_actualizar_sillon_a_nombre_existente_lanza_nombre_duplicado` | PASSED |
| Edición de sillón inexistente | `tests/api/test_sillones.py::test_patch_sillones_inexistente_responde_404` | PASSED |
| Edición con nombre vacío | `tests/api/test_sillones.py::test_patch_sillones_con_nombre_solo_espacios_responde_422_sin_modificar` | PASSED |
| Edición con nombre nulo | `tests/api/test_sillones.py::test_patch_sillones_con_nombre_null_responde_422_sin_modificar` | PASSED |
| Recepción intenta crear un sillón | `tests/api/test_sillones.py::test_recepcion_post_sillones_recibe_403` | PASSED |
| Odontología intenta modificar un sillón | `tests/api/test_sillones.py::test_odontologo_patch_sillones_recibe_403` | PASSED |
| Consulta de sillones sin autenticación | `tests/api/test_sillones.py::test_get_sillones_sin_token_responde_401` | PASSED |

## Cobertura de los escenarios del spec (`prestaciones`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta válida de prestación | `tests/api/test_prestaciones.py::test_post_prestaciones_alta_valida_normaliza_el_nombre` | PASSED |
| Duración cero o negativa | `tests/api/test_prestaciones.py::test_post_prestaciones_con_duracion_cero_responde_422`, `tests/api/test_prestaciones.py::test_post_prestaciones_con_duracion_negativa_responde_422`, `tests/domain/test_prestaciones.py::test_validar_datos_prestacion_con_duracion_no_positiva_lanza_dato_invalido[0]` | PASSED |
| Nombre de prestación vacío | `tests/api/test_prestaciones.py::test_post_prestaciones_con_nombre_vacio_responde_422`, `tests/api/test_prestaciones.py::test_post_prestaciones_con_nombre_solo_espacios_responde_422`, `tests/domain/test_prestaciones.py::test_validar_datos_prestacion_con_nombre_vacio_lanza_dato_invalido[   ]` | PASSED |
| Nombre de prestación duplicado | `tests/api/test_prestaciones.py::test_post_prestaciones_con_nombre_duplicado_responde_409`, `tests/api/test_repositorio_prestaciones.py::test_crear_prestacion_con_nombre_duplicado_lanza_nombre_duplicado` | PASSED |
| Listado incluye prestaciones desactivadas | `tests/api/test_repositorio_prestaciones.py::test_listar_prestaciones_devuelve_activas_e_inactivas_ordenadas_por_id`, `tests/api/test_prestaciones.py::test_patch_prestaciones_desactiva_y_sigue_en_el_listado`, `tests/api/test_prestaciones.py::test_get_prestaciones_permitido_para_los_tres_roles[administracion]` | PASSED |
| Desactivación lógica conserva la prestación | `tests/api/test_prestaciones.py::test_patch_prestaciones_desactiva_y_sigue_en_el_listado`, `tests/api/test_repositorio_prestaciones.py::test_baja_logica_de_prestacion_conserva_la_fila` | PASSED |
| Cambio de duración inválida | `tests/api/test_prestaciones.py::test_patch_prestaciones_con_duracion_invalida_responde_422_y_conserva_la_anterior[0]`, `tests/api/test_prestaciones.py::test_patch_prestaciones_con_duracion_invalida_responde_422_y_conserva_la_anterior[-30]` | PASSED |
| Renombrar a un nombre ya usado | `tests/api/test_prestaciones.py::test_patch_prestaciones_a_nombre_existente_responde_409`, `tests/api/test_repositorio_prestaciones.py::test_actualizar_prestacion_a_nombre_existente_lanza_nombre_duplicado` | PASSED |
| Edición con nombre nulo | `tests/api/test_prestaciones.py::test_patch_prestaciones_con_nombre_null_responde_422_sin_modificar` | PASSED |
| Edición con duración nula | `tests/api/test_prestaciones.py::test_patch_prestaciones_con_duracion_null_responde_422_sin_modificar` | PASSED |
| Edición de prestación inexistente | `tests/api/test_prestaciones.py::test_patch_prestaciones_inexistente_responde_404` | PASSED |
| Recepción intenta crear una prestación | `tests/api/test_prestaciones.py::test_recepcion_post_prestaciones_recibe_403` | PASSED |
| Odontología intenta modificar una prestación | `tests/api/test_prestaciones.py::test_odontologo_patch_prestaciones_recibe_403` | PASSED |
| Consulta de prestaciones sin autenticación | `tests/api/test_prestaciones.py::test_get_prestaciones_sin_token_responde_401` | PASSED |

## Cobertura de los escenarios del spec (`errores-api`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta de un recurso con nombre ya existente | `tests/api/test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje[/prueba/error/nombre-duplicado-409-nombre_duplicado-Ya existe un recurso con ese nombre (ficticio).]`, `tests/api/test_sillones.py::test_post_sillones_con_nombre_duplicado_responde_409`, `tests/api/test_prestaciones.py::test_post_prestaciones_con_nombre_duplicado_responde_409` | PASSED |

> Todos los escenarios declarados en los tres specs tienen al menos un test que los cubre. No se detectaron escenarios sin cobertura.

## Chequeos adicionales

- **Límites de imports entre capas (regla dura 1 de `AGENTS.md`):** `app/domain/` no importa `fastapi`, `app.db`, `app.api` ni `sqlite3`; sus únicos imports son `dataclasses`, `datetime`, `typing`, `collections.abc`, `enum` y módulos `app.domain.*`. Un grep sobre `app/domain/` solo encuentra la mención del docstring de `app/domain/__init__.py` (`"Dominio puro: sin FastAPI, sin app/db ni app/api."`), no un import. `app/db/repositorio_sillones.py` y `app/db/repositorio_prestaciones.py` solo importan `sqlite3`, `typing`, `app.domain.errores.NombreDuplicado` y la entidad de `app.domain.models`.
- **SQL parametrizado (regla dura 4):** todas las consultas de `app/db/repositorio_sillones.py` y `app/db/repositorio_prestaciones.py` son constantes de módulo con marcadores `?` y reciben los valores como tupla en `execute()`; un grep de f-strings, concatenación, `.format()` y `%` sobre ambos archivos no devuelve coincidencias.
- **Formato de errores en español (`RN-GLO-01`, regla dura 7):** `422` (`DatoInvalido`), `409` (`NombreDuplicado`), `404` (`HTTPException(404)` → `no_encontrado`), `403` (`SinPermiso`) y `401` (`NoAutenticado`) pasan por los manejadores globales de `app/api/errores.py` y devuelven `{codigo, mensaje, detalles?}` en español. El caso parametrizado de `nombre_duplicado` en `tests/api/test_errores.py` compara el cuerpo completo (`{"codigo": ..., "mensaje": ...}`), lo que verifica que no se filtran claves ni mensajes del motor SQLite.
- **Datos ficticios (regla dura 10):** todos los tests usan nombres rotulados como ficticios (`"Sillón 1 (ficticio)"`, `"Box 2 (ficticio)"`, `"Consulta ficticia"`, `"Limpieza ficticia"`, `"admin_ficticio"`, `"recepcion_ficticia"`, `"odontologo_ficticio"`). No hay datos de pacientes reales.
- **Validación OpenSpec:** `openspec validate c-05-sillones-prestaciones --strict` → `Change 'c-05-sillones-prestaciones' is valid` (exit code 0).
