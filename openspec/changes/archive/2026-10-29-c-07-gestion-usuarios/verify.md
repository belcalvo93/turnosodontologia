# Verify — C-07 gestion-usuarios

- **Fecha:** 2026-10-29
- **Responsable:** Equipo Active-Stack (C-07)
- **Comando:** `.venv\Scripts\python -m pytest -q`
- **Entorno:** Windows 11, Python 3.14.7, pytest 9.2.0, FastAPI 0.162.0, Starlette 1.10.0, Pydantic 2.14.1, PyJWT 2.15.1, pwdlib 0.3.1, httpx 0.28.1
- **Resultado:** `467 passed, 1 warning in 20.88s` (sin fallos, salteados ni errores).
  - Por origen: 393 del baseline (`C-01` a `C-06`) + 74 nuevos de `C-07` (19 en `tests/domain/test_usuarios_gestion.py`, 11 en `tests/api/test_repositorio_usuarios.py` y 44 en `tests/api/test_usuarios.py`).

## Cobertura de los escenarios del spec (`usuarios`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta de recepción | `tests/api/test_usuarios.py::test_post_usuarios_recepcion_responde_201_sin_profesional` | PASSED |
| Alta de odontólogo vinculado a un profesional activo | `tests/api/test_usuarios.py::test_post_usuarios_odontologo_con_profesional_activo_responde_201` | PASSED |
| Username duplicado | `tests/api/test_usuarios.py::test_post_usuarios_username_duplicado_responde_409`, `tests/api/test_repositorio_usuarios.py::test_crear_usuario_username_duplicado_lanza_username_duplicado` | PASSED |
| Contraseña vacía | `tests/api/test_usuarios.py::test_post_usuarios_password_vacia_responde_422` | PASSED |
| Username vacío o solo con espacios | `tests/api/test_usuarios.py::test_post_usuarios_username_vacio_responde_422[]`, `…[   ]`, `tests/domain/test_usuarios_gestion.py::test_validar_username_rechaza_vacio[]`, `…[   ]` | PASSED |
| Rol fuera de los tres roles del MVP | `tests/api/test_usuarios.py::test_post_usuarios_rol_fuera_del_mvp_responde_422` | PASSED |
| La respuesta no expone el hash | `tests/api/test_usuarios.py::test_post_usuarios_no_expone_el_hash` | PASSED |
| Odontólogo sin profesional | `tests/api/test_usuarios.py::test_post_usuarios_odontologo_sin_profesional_responde_422`, `tests/domain/test_usuarios_gestion.py::test_validar_datos_usuario_odontologo_sin_profesional_id` | PASSED |
| Odontólogo con profesional inexistente | `tests/api/test_usuarios.py::test_post_usuarios_odontologo_con_profesional_inexistente_responde_422`, `tests/domain/test_usuarios_gestion.py::test_validar_datos_usuario_odontologo_con_profesional_inexistente` | PASSED |
| Odontólogo con profesional inactivo | `tests/api/test_usuarios.py::test_post_usuarios_odontologo_con_profesional_inactivo_responde_422`, `tests/domain/test_usuarios_gestion.py::test_validar_datos_usuario_odontologo_con_profesional_inactivo` | PASSED |
| Rol sin vínculo con profesional | `tests/api/test_usuarios.py::test_post_usuarios_rol_sin_vinculo_con_profesional_responde_422`, `tests/domain/test_usuarios_gestion.py::test_validar_datos_usuario_rol_sin_vinculo_rechaza_profesional[administracion]`, `…[recepcion]` | PASSED |
| Usuario administrativo sin profesional | `tests/api/test_usuarios.py::test_post_usuarios_administracion_sin_profesional_responde_201`, `tests/domain/test_usuarios_gestion.py::test_validar_datos_usuario_rol_sin_vinculo_devuelve_sin_profesional[administracion-administracion]`, `…[recepcion-recepcion]` | PASSED |
| Listado ordenado que incluye inactivos | `tests/api/test_usuarios.py::test_get_usuarios_lista_ordenado_e_incluye_inactivos`, `tests/api/test_repositorio_usuarios.py::test_listar_usuarios_devuelve_ordenados_por_id_e_incluye_inactivos`, `…::test_listar_usuarios_sin_filas_devuelve_lista_vacia` | PASSED |
| El listado no expone el hash | `tests/api/test_usuarios.py::test_get_usuarios_no_expone_el_hash` | PASSED |
| Recepción consulta el listado | `tests/api/test_usuarios.py::test_get_usuarios_rol_sin_permiso_responde_403[recepcion]`, `…::test_rutas_usuarios_rol_sin_permiso_responde_403[recepcion-get]` | PASSED |
| Desactivar un usuario con PATCH | `tests/api/test_usuarios.py::test_patch_usuarios_desactiva_y_reactiva` | PASSED |
| Reactivar un usuario con PATCH | `tests/api/test_usuarios.py::test_patch_usuarios_desactiva_y_reactiva` | PASSED |
| Rol nulo en la edición | `tests/api/test_usuarios.py::test_patch_usuarios_campo_nulo_responde_422_sin_modificar[rol]` | PASSED |
| Estado activo nulo en la edición | `tests/api/test_usuarios.py::test_patch_usuarios_campo_nulo_responde_422_sin_modificar[activo]` | PASSED |
| Intento de cambiar el username | `tests/api/test_usuarios.py::test_patch_usuarios_username_presente_responde_422_sin_modificar` | PASSED |
| Edición de un usuario inexistente | `tests/api/test_usuarios.py::test_patch_usuarios_inexistente_responde_404`, `tests/api/test_repositorio_usuarios.py::test_actualizar_usuario_inexistente_devuelve_none` | PASSED |
| De recepción a odontólogo con profesional válido | `tests/api/test_usuarios.py::test_patch_usuarios_recepcion_a_odontologo_con_profesional`, `tests/domain/test_usuarios_gestion.py::test_aplicar_cambios_usuario_entrar_a_odontologo_con_profesional` | PASSED |
| De recepción a odontólogo sin profesional | `tests/api/test_usuarios.py::test_patch_usuarios_recepcion_a_odontologo_sin_profesional_responde_422`, `tests/domain/test_usuarios_gestion.py::test_aplicar_cambios_usuario_entrar_a_odontologo_sin_profesional_falla_al_validar` | PASSED |
| De odontólogo a recepción limpia el vínculo | `tests/api/test_usuarios.py::test_patch_usuarios_salir_de_odontologo_limpia_el_profesional[recepcion]`, `tests/domain/test_usuarios_gestion.py::test_aplicar_cambios_usuario_al_salir_de_odontologo_limpia_el_vinculo` | PASSED |
| De odontólogo a administración limpia el vínculo | `tests/api/test_usuarios.py::test_patch_usuarios_salir_de_odontologo_limpia_el_profesional[administracion]`, `tests/domain/test_usuarios_gestion.py::test_aplicar_cambios_usuario_al_pasar_a_administracion_limpia_el_vinculo` | PASSED |
| Cambio de profesional sin cambiar el rol | `tests/api/test_usuarios.py::test_patch_usuarios_cambia_profesional_conservando_el_rol`, `tests/domain/test_usuarios_gestion.py::test_aplicar_cambios_usuario_cambia_profesional_sin_cambiar_rol` | PASSED |
| Cambio a un profesional inactivo sin cambiar el rol | `tests/api/test_usuarios.py::test_patch_usuarios_profesional_inactivo_responde_422_sin_modificar` | PASSED |
| Reset de contraseña cambia el hash | `tests/api/test_usuarios.py::test_patch_usuarios_reset_de_password_cambia_el_hash_y_habilita_el_login`, `tests/api/test_repositorio_usuarios.py::test_actualizar_usuario_reemplaza_el_hash` | PASSED |
| La contraseña nueva permite login | `tests/api/test_usuarios.py::test_patch_usuarios_reset_de_password_cambia_el_hash_y_habilita_el_login` | PASSED |
| La contraseña anterior ya no sirve | `tests/api/test_usuarios.py::test_patch_usuarios_reset_de_password_cambia_el_hash_y_habilita_el_login` | PASSED |
| PATCH sin password conserva el hash | `tests/api/test_usuarios.py::test_patch_usuarios_sin_password_conserva_el_hash`, `tests/api/test_repositorio_usuarios.py::test_actualizar_usuario_sin_hash_conserva_el_original` | PASSED |
| Contraseña vacía en la edición | `tests/api/test_usuarios.py::test_patch_usuarios_password_vacia_responde_422_sin_cambiar_el_hash` | PASSED |
| La respuesta del reset no expone secretos | `tests/api/test_usuarios.py::test_patch_usuarios_no_expone_el_hash` | PASSED |
| Usuario desactivado no puede loguear | `tests/api/test_usuarios.py::test_usuario_desactivado_no_puede_loguear` | PASSED |
| Token vigente tras la desactivación | `tests/api/test_usuarios.py::test_token_emitido_antes_de_la_desactivacion_deja_de_servir` | PASSED |
| El usuario desactivado sigue en el listado | `tests/api/test_usuarios.py::test_get_usuarios_lista_ordenado_e_incluye_inactivos`, `…::test_patch_usuarios_desactiva_y_reactiva` | PASSED |
| No existe borrado físico | `tests/api/test_usuarios.py::test_delete_usuarios_responde_405_y_conserva_el_usuario` | PASSED |
| Recepción intenta crear un usuario | `tests/api/test_usuarios.py::test_rutas_usuarios_rol_sin_permiso_responde_403[recepcion-post]` | PASSED |
| Odontólogo intenta editar un usuario | `tests/api/test_usuarios.py::test_rutas_usuarios_rol_sin_permiso_responde_403[odontologo-patch]` | PASSED |
| Consulta de usuarios sin autenticación | `tests/api/test_usuarios.py::test_rutas_usuarios_sin_token_responde_401[get]` | PASSED |
| Alta de usuario sin autenticación | `tests/api/test_usuarios.py::test_rutas_usuarios_sin_token_responde_401[post]` | PASSED |
| Edición de usuario sin autenticación | `tests/api/test_usuarios.py::test_rutas_usuarios_sin_token_responde_401[patch]` | PASSED |

## Cobertura de los escenarios del spec (`errores-api`)

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta de un usuario con username ya existente | `tests/api/test_usuarios.py::test_post_usuarios_username_duplicado_responde_409`, `tests/api/test_repositorio_usuarios.py::test_crear_usuario_username_duplicado_lanza_username_duplicado` | PASSED |

> Los 42 escenarios de `usuarios` y el único de `errores-api` tienen al menos un test que los cubre. Las validaciones puras de los requirements de alta y edición también están cubiertas por los 19 tests de `tests/domain/test_usuarios_gestion.py` (`validar_username`, `validar_datos_usuario`, `aplicar_cambios_usuario`).

## Chequeos adicionales

- **Límites de imports entre capas (regla dura 1):** `app/domain/usuarios.py` solo importa `dataclasses`, `enum`, `app.domain.errores` y `app.domain.models`; no importa `fastapi`, `sqlite3`, `app.db` ni `app.api`. `test_modulo_usuarios_no_importa_capas_externas` (`tests/domain/test_usuarios.py`) sigue verde.
- **SQL parametrizado (regla dura 4):** `app/db/repositorio_usuarios.py` usa constantes de módulo (`_SELECT_TODOS`, `_UPDATE_CON_HASH`, `_UPDATE_SIN_HASH`) con marcadores `?`; el alta delega en `insertar_usuario` de `repositorio.py`. Sin f-strings, `+`, `.format()` ni `%` en SQL.
- **Errores en español con código (RN-GLO-01, regla dura 7):** el único código nuevo es `409 username_duplicado` (`UsernameDuplicado` → `MAPEO_DOMINIO`). `422` (`DatoInvalido`), `404` (`HTTPException(404)`), `403` (`SinPermiso`), `401` (`NoAutenticado`) y `405` (`metodo_no_permitido`) usan los manejadores globales. El `409` no repite el username ni expone el error de SQLite.
- **Hash de contraseñas (RN-ACC-04):** alta y reset usan `hashear()` (Argon2id con sal). Las respuestas de `POST`, `GET` y `PATCH` no contienen `password` ni `password_hash` (tests explícitos). El hash se conserva sin reescribirse cuando el `PATCH` no lo envía (dos `UPDATE` literales).
- **Datos ficticios (RN-PAC-03, regla dura 10):** todos los fixtures usan `admin_ficticio`, `recepcion_ficticia`, `odontologo_ficticio`, `"0001 (ficticia)"`, `"Odontóloga Ficticia A"` y las claves `"clave-ficticia-123"` / `"otra-clave-ficticia-456"` / `"nueva-clave-ficticia-789"`. No hay credenciales reales.
- **Sin cambios de esquema ni de login:** `git status`/`git diff` no muestran cambios en `app/db/esquema.sql`, `app/db/repositorio.py`, `app/db/seed.py`, `app/api/auth.py` ni `app/api/seguridad.py`. Los 20 tests de `tests/api/test_auth.py` siguen verdes.
- **Sin auditoría de usuarios ni borrado físico (IF-06):** no se agregó tabla de auditoría ni `DELETE`; `DELETE /usuarios/{id}` responde `405` y el usuario sigue existiendo.
- **Validación OpenSpec:** `openspec validate c-07-gestion-usuarios --strict` → `Change 'c-07-gestion-usuarios' is valid` (exit code 0).
- **Integración pendiente con `C-09`/`C-12`:** por el riesgo documentado en `design.md`, antes de cerrar el apply corresponde `git merge origin/main` y volver a correr la suite completa. No se ejecutó: la rama de trabajo tiene los cambios sin commitear.
