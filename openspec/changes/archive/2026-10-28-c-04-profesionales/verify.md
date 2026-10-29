# Verify — C-04 profesionales

- **Fecha:** 2026-10-28
- **Responsable:** Bruno Fiouchetta
- **Comando:** `pytest tests -v`
- **Entorno:** Windows 10, Python 3.13.5, pytest 9.2.0, FastAPI 0.162.0, Starlette 1.10.0, PyJWT 2.15.1, pwdlib 0.3.1
- **Resultado:** `220 passed in 10.53s` (171 en `tests/api/` + 49 en `tests/domain/`), 1 warning. Sin tests fallidos ni salteados.
  - Por origen: 194 del baseline (`C-01`, `C-10` y `C-03`) + 26 nuevos de `C-04` (9 en `tests/domain/test_profesionales.py`, 5 en `tests/api/test_repositorio_profesionales.py` y 12 en `tests/api/test_profesionales.py`).

## Cobertura de los escenarios del spec (`profesionales`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta válida con matrícula opcional | `tests/api/test_profesionales.py::test_post_profesionales_alta_valida_con_matricula_responde_201` | PASSED |
| Alta válida sin matrícula | `tests/api/test_profesionales.py::test_post_profesionales_alta_valida_sin_matricula_responde_201` | PASSED |
| Rechazo por nombre o apellido vacío | `tests/domain/test_profesionales.py::test_validar_datos_profesional_con_nombre_o_apellido_vacio_lanza_dato_invalido[...]`, `tests/api/test_profesionales.py::test_post_profesionales_con_nombre_o_apellido_vacio_responde_422_y_no_persiste[...]` | PASSED |
| Listado incluye profesionales desactivados como inactivos | `tests/api/test_profesionales.py::test_patch_profesionales_desactivado_sigue_listandose_como_inactivo`, `tests/api/test_repositorio_profesionales.py::test_listar_profesionales_devuelve_activos_e_inactivos_ordenados_por_id` | PASSED |
| Desactivación lógica conserva el registro | `tests/api/test_profesionales.py::test_patch_profesionales_desactivado_sigue_listandose_como_inactivo` | PASSED |
| Edición de profesional inexistente | `tests/api/test_profesionales.py::test_patch_profesionales_inexistente_responde_404` | PASSED |
| Recepción intenta crear un profesional | `tests/api/test_profesionales.py::test_recepcion_y_odontologo_reciben_403_al_crear_o_editar_y_200_al_listar[recepcion]` | PASSED |
| Odontólogo intenta modificar un profesional | `tests/api/test_profesionales.py::test_recepcion_y_odontologo_reciben_403_al_crear_o_editar_y_200_al_listar[odontologo]` | PASSED |
| Consulta sin autenticación | `tests/api/test_profesionales.py::test_rutas_profesionales_sin_token_responden_401` | PASSED |

## Chequeos adicionales

- **Límites de imports entre capas (regla dura 1 de `AGENTS.md`):** `app/domain/` no importa `fastapi`, `app.db`, `app.api` ni `sqlite3`. `app/db/repositorio_profesionales.py` solo importa `sqlite3`, `typing` y `app.domain.models.Profesional`.
- **SQL parametrizado (regla dura 4):** todas las consultas en `app/db/repositorio_profesionales.py` usan marcadores `?`; sin concatenación ni interpolación de strings.
- **Formato de errores en español (`RN-GLO-01`, regla dura 7):** los `422` (`DatoInvalido`), `404` (`HTTPException(404)`), `403` (`SinPermiso`) y `401` (`NoAutenticado`) pasan por los manejadores globales de `app/api/errores.py` devolviendo `{codigo, mensaje, detalles?}` en español.
- **Datos ficticios (regla dura 10):** todos los tests emplean nombres y matrículas ficticias rotuladas (`"0001 (ficticia)"`, `"Odontólogo Ficticio A"`).
- **Validación OpenSpec:** `openspec validate c-04-profesionales --strict` → `Change 'c-04-profesionales' is valid`.
