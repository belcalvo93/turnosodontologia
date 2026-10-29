# Verify — C-06 pacientes

- **Fecha:** 2026-10-29
- **Responsable:** Belén Calvo
- **Comando:** `pytest tests -v`
- **Entorno:** Windows 11 Home (10.0.26300), Python 3.14.7, pytest 9.1.1, FastAPI 0.141.1, Starlette 1.7.0, Pydantic 2.13.5, PyJWT 2.15.1, pwdlib 0.3.1, httpx 0.28.1
- **Resultado:** `393 passed, 1 warning in 27.98s` (313 en `tests/api/` + 80 en `tests/domain/`). Sin tests fallidos, salteados ni errores.
  - Por origen: 314 del baseline (`C-01`, `C-10`, `C-03`, `C-04` y `C-05`) + 79 nuevos de `C-06` (19 en `tests/domain/test_pacientes.py`, 24 en `tests/api/test_repositorio_pacientes.py`, 35 en `tests/api/test_pacientes.py` y 1 caso parametrizado nuevo en `tests/api/test_errores.py`).

## Cobertura de los escenarios del spec (`pacientes`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta válida con obra social y número de afiliado | `tests/api/test_pacientes.py::test_post_pacientes_alta_valida_con_obra_social`, `tests/api/test_repositorio_pacientes.py::test_crear_y_obtener_paciente_por_id` | PASSED |
| Alta válida sin datos opcionales | `tests/api/test_pacientes.py::test_post_pacientes_alta_valida_sin_opcionales`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_deja_opcionales_omitidos_en_none` | PASSED |
| Normalización del DNI con espacios laterales | `tests/api/test_pacientes.py::test_post_pacientes_normaliza_dni_con_espacios`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_normaliza_espacios_en_dni` | PASSED |
| Nombre de paciente vacío | `tests/api/test_pacientes.py::test_post_pacientes_con_nombre_vacio_responde_422`, `tests/api/test_pacientes.py::test_post_pacientes_con_nombre_solo_espacios_responde_422`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_con_nombre_vacio_lanza_dato_invalido`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_con_nombre_solo_espacios_lanza_dato_invalido` | PASSED |
| Apellido de paciente vacío | `tests/api/test_pacientes.py::test_post_pacientes_con_apellido_vacio_responde_422`, `tests/api/test_pacientes.py::test_post_pacientes_con_apellido_solo_espacios_responde_422`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_con_apellido_vacio_lanza_dato_invalido`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_con_apellido_solo_espacios_lanza_dato_invalido` | PASSED |
| DNI vacío | `tests/api/test_pacientes.py::test_post_pacientes_con_dni_vacio_responde_422`, `tests/api/test_pacientes.py::test_post_pacientes_con_dni_solo_espacios_responde_422`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_con_dni_vacio_lanza_dato_invalido`, `tests/domain/test_pacientes.py::test_validar_datos_paciente_con_dni_solo_espacios_lanza_dato_invalido` | PASSED |
| DNI duplicado | `tests/api/test_pacientes.py::test_post_pacientes_con_dni_duplicado_responde_409_sin_repetir_el_dni`, `tests/api/test_repositorio_pacientes.py::test_crear_paciente_con_dni_duplicado_lanza_dni_duplicado`, `tests/api/test_repositorio_pacientes.py::test_mensaje_de_dni_duplicado_no_contiene_el_dni_recibido` | PASSED |
| Número de afiliado sin obra social | `tests/api/test_pacientes.py::test_post_pacientes_con_nro_afiliado_sin_obra_social_responde_201` | PASSED |
| Listado de pacientes ordenado por id | `tests/api/test_pacientes.py::test_get_pacientes_devuelve_listado_ordenado_por_id`, `tests/api/test_repositorio_pacientes.py::test_listar_pacientes_devuelve_ordenados_por_id` | PASSED |
| Recepción consulta el listado | `tests/api/test_pacientes.py::test_recepcion_get_pacientes_responde_200` | PASSED |
| Odontología consulta el listado | `tests/api/test_pacientes.py::test_odontologo_get_pacientes_recibe_403` | PASSED |
| Edición de nombre, apellido y DNI | `tests/api/test_pacientes.py::test_patch_pacientes_actualiza_nombre_apellido_y_dni`, `tests/api/test_repositorio_pacientes.py::test_actualizar_paciente_modifica_nombre_y_apellido`, `tests/api/test_repositorio_pacientes.py::test_actualizar_paciente_modifica_dni` | PASSED |
| Edición de datos opcionales | `tests/api/test_pacientes.py::test_patch_pacientes_actualiza_telefono_obra_social_y_nro_afiliado`, `tests/api/test_repositorio_pacientes.py::test_actualizar_paciente_modifica_telefono_obra_social_y_nro_afiliado` | PASSED |
| Limpieza del teléfono | `tests/api/test_pacientes.py::test_patch_pacientes_limpia_telefono_con_null`, `tests/api/test_repositorio_pacientes.py::test_actualizar_paciente_limpia_opcional_con_none` | PASSED |
| Limpieza de la obra social | `tests/api/test_pacientes.py::test_patch_pacientes_limpia_obra_social_con_null` | PASSED |
| Limpieza del número de afiliado | `tests/api/test_pacientes.py::test_patch_pacientes_limpia_nro_afiliado_con_null` | PASSED |
| Edición con nombre nulo | `tests/api/test_pacientes.py::test_patch_pacientes_con_nombre_null_responde_422_sin_modificar` | PASSED |
| Edición con apellido nulo | `tests/api/test_pacientes.py::test_patch_pacientes_con_apellido_null_responde_422_sin_modificar` | PASSED |
| Edición con DNI nulo | `tests/api/test_pacientes.py::test_patch_pacientes_con_dni_null_responde_422_sin_modificar` | PASSED |
| Edición con nombre solo de espacios | `tests/api/test_pacientes.py::test_patch_pacientes_con_nombre_solo_espacios_responde_422_sin_modificar` | PASSED |
| Edición con apellido solo de espacios | `tests/api/test_pacientes.py::test_patch_pacientes_con_apellido_solo_espacios_responde_422_sin_modificar` | PASSED |
| Edición con DNI solo de espacios | `tests/api/test_pacientes.py::test_patch_pacientes_con_dni_solo_espacios_responde_422_sin_modificar` | PASSED |
| Edición con el mismo DNI del paciente | `tests/api/test_pacientes.py::test_patch_pacientes_con_el_mismo_dni_del_paciente_responde_200_sin_conflicto`, `tests/api/test_repositorio_pacientes.py::test_actualizar_paciente_a_su_mismo_dni_no_lanza_conflicto` | PASSED |
| Edición con DNI de otro paciente | `tests/api/test_pacientes.py::test_patch_pacientes_a_dni_de_otro_paciente_responde_409_sin_repetir_el_dni_y_conserva_el_anterior`, `tests/api/test_repositorio_pacientes.py::test_actualizar_paciente_a_dni_existente_lanza_dni_duplicado`, `tests/api/test_repositorio_pacientes.py::test_fila_conserva_valores_previos_tras_intento_de_dni_duplicado` | PASSED |
| Edición de paciente inexistente | `tests/api/test_pacientes.py::test_patch_pacientes_inexistente_responde_404`, `tests/api/test_repositorio_pacientes.py::test_actualizar_paciente_inexistente_devuelve_none` | PASSED |
| Recepción crea un paciente | `tests/api/test_pacientes.py::test_recepcion_post_pacientes_responde_201` | PASSED |
| Odontología intenta crear un paciente | `tests/api/test_pacientes.py::test_odontologo_post_pacientes_recibe_403_y_no_crea_el_paciente` | PASSED |
| Recepción edita un paciente | `tests/api/test_pacientes.py::test_recepcion_patch_pacientes_responde_200` | PASSED |
| Odontología intenta editar un paciente | `tests/api/test_pacientes.py::test_odontologo_patch_pacientes_recibe_403_y_no_modifica` | PASSED |
| Consulta de pacientes sin autenticación | `tests/api/test_pacientes.py::test_get_pacientes_sin_token_responde_401` | PASSED |
| Alta de paciente sin autenticación | `tests/api/test_pacientes.py::test_post_pacientes_sin_token_responde_401` | PASSED |
| Edición de paciente sin autenticación | `tests/api/test_pacientes.py::test_patch_pacientes_sin_token_responde_401` | PASSED |

## Cobertura de los escenarios del spec (`errores-api`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta de un paciente con DNI ya existente | `tests/api/test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje[/prueba/error/dni-duplicado-409-dni_duplicado-Ya existe un paciente con ese DNI (ficticio).]`, `tests/api/test_pacientes.py::test_post_pacientes_con_dni_duplicado_responde_409_sin_repetir_el_dni` | PASSED |
| Edición de un paciente con el DNI de otro | `tests/api/test_pacientes.py::test_patch_pacientes_a_dni_de_otro_paciente_responde_409_sin_repetir_el_dni_y_conserva_el_anterior` | PASSED |

> Todos los escenarios declarados en ambos specs (`32` en `pacientes` y `2` en `errores-api`) tienen al menos un test que los cubre. No se detectaron escenarios sin cobertura.

## Chequeos adicionales

- **Límites de imports entre capas (regla dura 1 de `AGENTS.md`):** `app/domain/models.py` y `app/domain/errores.py` no importan `fastapi`, `sqlite3`, `app.db` ni `app.api`; los únicos imports en `app/domain/` son de la biblioteca estándar (`dataclasses`, `datetime`, `typing`, `collections.abc`, `enum`) y módulos `app.domain.*`. `app/db/repositorio_pacientes.py` solo importa `sqlite3`, `typing`, `app.domain.errores.DniDuplicado` y `app.domain.models.Paciente`.
- **SQL parametrizado (regla dura 4):** todas las consultas de `app/db/repositorio_pacientes.py` (`_INSERTAR_PACIENTE`, `_SELECT_POR_ID`, `_SELECT_TODOS`, `_UPDATE_PACIENTE`) son constantes de módulo con marcadores `?` y reciben los valores como tupla en `execute()`; un grep de f-strings, concatenación (`+`), `.format()` y `%` sobre el archivo no devuelve coincidencias.
- **Formato de errores en español (`RN-GLO-01`, regla dura 7):** `422` (`DatoInvalido` → `dato_invalido`), `409` (`DniDuplicado` → `dni_duplicado`), `404` (`HTTPException(404)` → `no_encontrado`), `403` (`SinPermiso` → `sin_permiso`) y `401` (`NoAutenticado` → `no_autenticado`) pasan por los manejadores globales de `app/api/errores.py` y devuelven `{codigo, mensaje, detalles?}` en español, sin exponer mensajes ni nombres de restricción de SQLite.
- **Datos ficticios (`RN-PAC-03`, regla dura 10):** todos los tests de dominio, repositorio y API usan datos ficticios rotulados y DNI con el sufijo `"(ficticio)"` (`"30111222 (ficticio)"`, `"30222333 (ficticio)"`, `"30999888 (ficticio)"`, `"00.000.001 (ficticio)"`, `"Obra Social Norte (ficticia)"`, `"AF-001 (ficticio)"`, `"admin_ficticio"`, `"recepcion_ficticia"`, `"odontologo_ficticio"`). No hay datos de pacientes reales.
- **Privacidad de datos de pacientes (`design.md` D11, `IF-06`):**
  - El conflicto `409 / dni_duplicado` devuelve un mensaje genérico en español (`"Ya existe un paciente con ese DNI."`) que **no repite el DNI recibido** (verificado en repositorio y en `POST`/`PATCH` de API).
  - El handler de `422` (`RequestValidationError` y `DatoInvalido`) informa el campo y el motivo en español sin reflejar el valor enviado en la respuesta.
  - No existe tabla ni registro de auditoría sobre `paciente`: por decisión explícita de `IF-06`, el MVP audita únicamente las operaciones sobre turnos (`auditoria_turno`).
- **Nota pendiente para `C-11` (`crear-turno`):** en `C-06` el rol `odontologo` recibe `403` (`sin_permiso`) en `GET /pacientes` porque aún no existe la tabla `turno` para acotar el listado a los pacientes de sus propios turnos (`SE-12`). Al proponer e implementar `C-11`, se debe habilitar la lectura de `GET /pacientes` para `odontologo` acotada a sus turnos y agregar el test correspondiente.
- **Validación OpenSpec:** `openspec validate c-06-pacientes --strict` → `Change 'c-06-pacientes' is valid` (exit code 0).
