# Verify — C-09 bloqueos

- **Fecha:** 2026-10-29
- **Responsable:** Bruno Fiouchetta
- **Comando:** `pytest tests -v`
- **Entorno:** Windows 10, Python 3.13.5, pytest 9.2.0, FastAPI 0.162.0, Starlette 1.10.0, PyJWT 2.15.1, pwdlib 0.3.1
- **Resultado:** `524 passed in 53.91s` (394 en `tests/api/` + 130 en `tests/domain/`), 1 warning. Sin tests fallidos ni salteados.
  - Por origen: 506 del baseline en `main` (`C-01` a `C-08`, `C-10` y dominio de `C-13`) + 18 nuevos de `C-09` (5 en `tests/domain/test_bloqueos.py`, 4 en `tests/api/test_repositorio_bloqueos.py` y 9 en `tests/api/test_bloqueos.py`).

## Cobertura de los escenarios del spec (`bloqueos`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta válida de bloqueo para un profesional | `tests/api/test_bloqueos.py::test_post_bloqueos_para_profesional_y_sillon_responde_201` | PASSED |
| Rechazo por intervalo inválido (inicio mayor o igual que fin) | `tests/domain/test_bloqueos.py::test_validar_datos_bloqueo_con_inicio_mayor_o_igual_que_fin_lanza_dato_invalido[...]`, `tests/api/test_bloqueos.py::test_post_bloqueos_con_inicio_mayor_o_igual_que_fin_responde_422[...]` | PASSED |
| Rechazo por recurso inexistente | `tests/api/test_repositorio_bloqueos.py::test_crear_bloqueo_con_profesional_inexistente_lanza_dato_invalido`, `tests/api/test_bloqueos.py::test_post_bloqueos_con_recurso_inexistente_responde_422[...]` | PASSED |
| Eliminar bloqueo existente libera el registro | `tests/api/test_bloqueos.py::test_delete_bloqueo_elimina_registro_y_404_si_no_existe` | PASSED |
| Eliminar bloqueo inexistente | `tests/api/test_bloqueos.py::test_delete_bloqueo_elimina_registro_y_404_si_no_existe` | PASSED |
| Recepción intenta crear un bloqueo | `tests/api/test_bloqueos.py::test_recepcion_y_odontologo_reciben_403_al_crear_o_eliminar_y_200_al_listar[recepcion]` | PASSED |
| Odontólogo intenta eliminar un bloqueo | `tests/api/test_bloqueos.py::test_recepcion_y_odontologo_reciben_403_al_crear_o_eliminar_y_200_al_listar[odontologo]` | PASSED |
| Consulta sin autenticación | `tests/api/test_bloqueos.py::test_rutas_bloqueos_sin_token_responden_401` | PASSED |

## Chequeos adicionales

- **Límites de imports entre capas (regla dura 1 de `AGENTS.md`):** verificado en `tests/domain/test_estructura.py` que ningún módulo de `app/domain/` importa `fastapi`, `app.db`, `app.api` ni `sqlite3`.
- **SQL parametrizado (regla dura 4 de `AGENTS.md`):** todas las consultas en `app/db/repositorio_bloqueos.py` utilizan exclusivamente marcadores `?`.
- **Formato de errores en español (`RN-GLO-01`, regla dura 7):** los rechazos `422` (`DatoInvalido`), `404` (`HTTPException(404)`), `403` (`SinPermiso`) y `401` (`NoAutenticado`) pasan por los manejadores globales de `app/api/errores.py` devolviendo `{codigo, mensaje, detalles?}` en español.
- **Datos ficticios (regla dura 10):** todos los tests utilizan nombres ficticios (`"Odontólogo Ficticio A"`, `"admin_ficticio"`, `"Sillón 1"`).
- **Validación OpenSpec:** `openspec validate c-09-bloqueos --strict` → `Change 'c-09-bloqueos' is valid`.
