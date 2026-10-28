# Verify — C-03 auth-login-roles

- **Fecha:** 2026-10-28
- **Responsable:** Joaquín Moran
- **Comando:** `pytest tests -v`. OpenSpec no ofrece una fase de verificación propia en esta instalación, así que la suite se ejecutó a mano.
- **Entorno:** Windows 11, Python 3.13.7, pytest 9.1.1, FastAPI 0.162.0, Starlette 1.10.0, PyJWT 2.15.1, pwdlib 0.3.1. Rama `joaquin-c03-auth-login-roles`, commit `2b41955`.
- **Resultado:** `194 passed in 6.05s`, 1 warning. No hay tests fallidos, con error, salteados ni `xfail`.
  - Por directorio: 154 en `tests/api/` y 40 en `tests/domain/`.
  - Por origen: 44 del baseline (C-01 y C-10), 149 nuevos de C-03, y 1 de Belén del PR #31 (`test_abrir_conexion_se_puede_usar_desde_otro_hilo`).

## Cobertura de los escenarios del spec

Hay 53 escenarios en tres specs (27 en `acceso-usuarios`, 14 en `base-tecnica` y 12 en `errores-api`), y todos tienen al menos un test aprobado. Los nombres son de `tests/api/` salvo que se indique otro archivo. Un `[...]` marca un test parametrizado y significa que pasaron todos sus casos.

### `acceso-usuarios`

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| La base no contiene la contraseña original | `test_auth.py::test_la_contrasena_no_queda_en_la_base_ni_en_la_respuesta_del_login`, `test_seguridad.py::test_hash_no_es_ni_contiene_la_contrasena` | PASSED |
| Misma contraseña, hashes distintos | `test_seguridad.py::test_misma_contrasena_produce_hashes_distintos` (ver observaciones) | PASSED |
| El hash verifica solo la contraseña correcta | `test_seguridad.py::test_verificar_acepta_solo_la_contrasena_correcta` | PASSED |
| Username duplicado | `test_esquema_usuario.py::test_username_duplicado_lanza_integrity_error` | PASSED |
| Rol fuera de los tres roles | `test_esquema_usuario.py::test_rol_fuera_de_los_tres_roles_lanza_integrity_error` | PASSED |
| Usuario sin profesional asociado | `test_esquema_usuario.py::test_administrador_sin_profesional_se_inserta` | PASSED |
| Login correcto devuelve token | `test_auth.py::test_login_correcto_devuelve_un_token_bearer_con_id_y_rol` | PASSED |
| El token incluye usuario, rol y vencimiento | `test_auth.py::test_login_correcto_devuelve_un_token_bearer_con_id_y_rol`, `test_seguridad.py::test_el_token_dura_access_token_expire_minutes`, `test_usuario_actual.py::test_el_token_vence_al_mover_el_reloj_fijo_sin_esperar` | PASSED |
| Body de login incompleto | `test_auth.py::test_login_sin_password_detalla_password` | PASSED |
| Usuario inexistente | `test_auth.py::test_login_de_usuario_inexistente_responde_credenciales_invalidas` | PASSED |
| Contraseña incorrecta | `test_auth.py::test_login_con_contrasena_incorrecta_responde_credenciales_invalidas` | PASSED |
| Usuario inactivo | `test_auth.py::test_login_de_usuario_inactivo_responde_credenciales_invalidas` | PASSED |
| Los tres casos devuelven el mismo cuerpo | `test_auth.py::test_los_tres_logins_fallidos_devuelven_el_mismo_cuerpo` | PASSED |
| Sin token | `test_usuario_actual.py::test_sin_cabecera_authorization_responde_no_autenticado` | PASSED |
| Cabecera mal formada | `test_usuario_actual.py::test_cabecera_mal_formada_o_token_ilegible_responde_no_autenticado[...]` | PASSED |
| Token inválido | `test_usuario_actual.py::test_token_firmado_con_otra_clave_responde_no_autenticado`, `test_token_con_algoritmo_none_responde_no_autenticado`, `test_cabecera_mal_formada_o_token_ilegible_responde_no_autenticado[texto-arbitrario-como-bearer]` | PASSED |
| Token vencido | `test_usuario_actual.py::test_el_token_vence_al_mover_el_reloj_fijo_sin_esperar`, `test_seguridad.py::test_token_vencido_tambien_es_token_invalido` | PASSED |
| Límite del vencimiento | `test_usuario_actual.py::test_el_token_vence_al_mover_el_reloj_fijo_sin_esperar` (T+59 da 200, T+60 da 401), `test_seguridad.py::test_token_vence_en_el_instante_exacto_de_exp` | PASSED |
| Health sigue siendo público | `test_auth.py::test_health_sigue_respondiendo_200_sin_token`, `test_salud.py::test_health_responde_200_sin_autenticacion` | PASSED |
| Usuario desactivado después del login | `test_usuario_actual.py::test_token_valido_de_un_usuario_desactivado_despues_del_login_responde_no_autenticado` | PASSED |
| Cambio de rol después del login | `test_requiere_rol.py::test_usuario_cuyo_rol_cambio_despues_del_login_recibe_403` | PASSED |
| Rol sin permiso | `test_requiere_rol.py::test_recepcion_no_puede_entrar_a_una_ruta_solo_admin` | PASSED |
| Rol permitido | `test_requiere_rol.py::test_recepcion_entra_a_una_ruta_de_admin_o_recepcion` | PASSED |
| Creación en development | `test_seed.py::test_en_development_con_la_variable_crea_admin_demo_y_permite_el_login` | PASSED |
| Arranque repetido idempotente | `test_seed.py::test_dos_arranques_sobre_la_misma_base_dejan_un_solo_admin_demo`, `test_la_segunda_llamada_no_duplica_ni_cambia_el_hash` | PASSED |
| Sin seed fuera de development | `test_seed.py::test_en_test_con_la_variable_no_crea_usuarios`, `test_en_production_con_la_variable_no_crea_usuarios` | PASSED |
| Sin seed si falta la contraseña | `test_seed.py::test_en_development_sin_la_variable_arranca_y_no_crea_usuarios` | PASSED |

### `base-tecnica`

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Defaults de autenticación en desarrollo | `test_config.py::test_entorno_vacio_usa_defaults_de_autenticacion` | PASSED |
| Secreto aleatorio por proceso | `test_config.py::test_sin_jwt_secret_en_test_genera_un_secreto_aleatorio_por_carga` | PASSED |
| Secreto explícito | `test_config.py::test_jwt_secret_explicito_se_respeta_tal_cual`, `test_jwt_secret_definido_en_production_se_acepta` | PASSED |
| Falta JWT_SECRET fuera de development y test | `test_config.py::test_sin_jwt_secret_en_production_falla_nombrando_la_variable`, `test_sin_jwt_secret_fuera_de_development_y_test_falla[...]`, `test_create_app_no_arranca_sin_jwt_secret_en_production` | PASSED |
| Duración del token inválida | `test_config.py::test_duracion_del_token_invalida_falla_nombrando_la_variable[...]` | PASSED |
| Algoritmo no admitido | `test_config.py::test_algoritmo_no_hmac_falla_nombrando_la_variable[...]` | PASSED |
| Docs disponibles en development | `test_main.py::test_documentacion_disponible_en_development[...]` | PASSED |
| Docs ocultas fuera de development | `test_main.py::test_documentacion_oculta_fuera_de_development[...]`, `test_errores.py::test_docs_fuera_de_development_responde_el_404_propio` | PASSED |
| Claves foráneas activas | `test_conexion.py::test_abrir_conexion_hace_cumplir_las_claves_foraneas` | PASSED |
| Commit al cerrar la transacción | `test_conexion.py::test_transaccion_confirma_al_salir_sin_excepcion` | PASSED |
| Rollback ante excepción | `test_conexion.py::test_transaccion_revierte_ante_excepcion_y_propaga` | PASSED |
| Uso desde otro hilo | `test_conexion.py::test_abrir_conexion_se_puede_usar_desde_otro_hilo` (Belén, PR #31), `test_abrir_conexion_se_puede_cerrar_desde_otro_hilo`, `test_dependencias.py::test_la_ruta_consulta_la_base_configurada_sin_error_de_hilo` | PASSED |
| Arranque con esquema vacío | `test_main.py::test_arranque_inicializa_el_esquema`, `test_esquema_usuario.py::test_la_tabla_usuario_existe_despues_del_arranque` | PASSED |
| Aplicación repetida del esquema | `test_conexion.py::test_inicializar_esquema_se_puede_aplicar_dos_veces`, `test_esquema_usuario.py::test_aplicar_el_esquema_dos_veces_no_falla_ni_borra_usuarios` | PASSED |

### `errores-api`

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Error sin detalles por campo | `test_errores.py::test_errores_de_autenticacion_responden_401_con_www_authenticate[...]`, `test_usuario_actual.py::test_sin_cabecera_authorization_responde_no_autenticado` (ver observaciones) | PASSED |
| Error con detalles por campo | `test_errores.py::test_body_vacio_responde_422_con_un_detalle_por_campo_faltante`, `test_auth.py::test_login_con_body_vacio_detalla_username_y_password` | PASSED |
| Código 401 por falta de token | `test_usuario_actual.py::test_sin_cabecera_authorization_responde_no_autenticado`, `test_errores.py::test_errores_de_autenticacion_responden_401_con_www_authenticate[...no-autenticado...]` | PASSED |
| Código 401 por login fallido | `test_auth.py::test_login_de_usuario_inexistente_responde_credenciales_invalidas`, `test_errores.py::test_errores_de_autenticacion_responden_401_con_www_authenticate[...credenciales-invalidas...]` | PASSED |
| Código 403 | `test_errores.py::test_sin_permiso_responde_403_sin_www_authenticate`, `test_requiere_rol.py::test_recepcion_no_puede_entrar_a_una_ruta_solo_admin` | PASSED |
| Código 409 por solapamiento | `test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje[...conflicto-agenda...]` | PASSED |
| Código 409 fuera de horario | `test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje[...fuera-de-horario...]` | PASSED |
| Código 409 dentro de un bloqueo | `test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje[...dentro-de-bloqueo...]` | PASSED |
| Código 422 por validación de entrada | `test_auth.py::test_login_con_password_numerico_detalla_password`, `test_errores.py::test_tipo_incorrecto_responde_422_con_el_campo_sin_prefijo_body` | PASSED |
| Código 422 por regla de dominio | `test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje[...dato-invalido...]` | PASSED |
| Ruta inexistente | `test_errores.py::test_ruta_inexistente_responde_404_no_encontrado` | PASSED |
| Método no admitido | `test_errores.py::test_metodo_no_admitido_responde_405_metodo_no_permitido` | PASSED |

## Cobertura de las RN tocadas

| RN | Archivo de tests | Tests |
|---|---|---|
| RN-ACC-01 (rutas protegidas exigen token válido) | `test_usuario_actual.py` | 14 |
| RN-ACC-02 (mecanismo de chequeo de rol) | `test_requiere_rol.py` | 7 |
| RN-ACC-04 (contraseñas con hash y sal) | `test_seguridad.py`, `test_auth.py`, `test_seed.py` | 18 relevantes |
| RN-GLO-01 (errores en JSON en español con código) | `test_errores.py` | 17 |

## Chequeos adicionales

- **Baseline intacto.** Extraje con `git archive` el merge-base con `main` (`d2041ee`) a una carpeta temporal, y ahí la suite da `44 passed`. Los 44 IDs de ese baseline están todos entre los aprobados de la suite actual, sin renombres ni bajas (tarea 9.1).
- **Límites de imports entre capas** (regla dura 1):
  - `app/domain/` no importa `fastapi`, `starlette`, `jwt`, `pwdlib`, `app.db` ni `app.api`.
  - `app/db/` no importa `fastapi`, `starlette` ni `app.api`; de `app.domain` importa solo los tipos `Rol` y `Usuario`.
  - No hay imports relativos ni dinámicos.
  - Control del patrón: la misma búsqueda sobre `app/api/` encuentra 16 imports (tarea 9.2).
- **Sin secretos ni datos reales** (reglas duras 9 y 10):
  - `.env` no está versionado: `.gitignore` lo excluye en la línea 4.
  - `app/` no tiene secretos ni contraseñas literales.
  - Los secretos, contraseñas y usuarios de `tests/` están rotulados como ficticios, salvo `admin_demo`, cuyo nombre fija la KB 04 (seed). Su contraseña sí está rotulada: `clave-demo-ficticia`.
  - En el historial `main..HEAD` solo se agregaron placeholders (tarea 9.3).
- **Sin hora real en los tests** (regla dura 2 / RN-TUR-09): `tests/` no usa `sleep`, `datetime.now`, `datetime.utcnow`, `date.today` ni `time.time`. La única lectura de la hora real en `app/` es `_hora_real()` en `app/main.py`, el reloj por defecto de `create_app` (tarea 9.4).
- **Suite sobre una copia limpia del commit.** Extraje `HEAD` (`2b41955`) con `git archive` a una carpeta temporal y la suite dio `194 passed`, así que no depende de archivos sin versionar. Usé el `.venv` del repo: no fue un clon con un entorno virtual nuevo.
- **La suite no crea `turnos.db` en la raíz**, porque los tests usan una SQLite temporal por test. Después de correrla, `git status` quedó limpio.
- **Verificación manual contra `uvicorn app.main:app`** (tarea 8.2), con `APP_ENV=development`, `SEED_ADMIN_PASSWORD=clave-demo-ficticia` y una base temporal fuera del repo:
  - el login de `admin_demo` con curl y con `Invoke-RestMethod`, copiados tal cual del README, dio `200`, `token_type` `bearer`;
  - una contraseña incorrecta dio `401` `credenciales_invalidas` con `WWW-Authenticate: Bearer`;
  - un login sin `password` dio `422` `dato_invalido` con `detalles`;
  - `GET /health` dio `200` sin token y también con un token inválido;
  - `/docs` dio `200` en development y `404` en test;
  - con `APP_ENV=production` y sin `JWT_SECRET`, la app no arranca (`ConfigInvalida`).
- **`openspec validate c-03-auth-login-roles --strict`** respondió `Change 'c-03-auth-login-roles' is valid`, con `"issues": []`.

## Observaciones del apply

### Desvíos acordados con el equipo

- **Campo `"body"` en los 422 de todo el cuerpo (tarea 3.4).** Cuando el error de validación afecta a todo el body (body que no es un objeto o JSON mal formado), `detalles[].campo` vale `"body"`. Antes quedaba vacío o con un índice. Se agregó a `design.md` §7 y a la tarea 3.4, con su test.
- **El test del 403 por cambio de rol pasó de la 6.6 a la 6.7**, porque necesita `requiere_rol`, que se implementa en la 6.7. En la 6.6 quedó el test del usuario desactivado. Que se usa el rol guardado y no el del token se verificó ahí sobre `/prueba/autenticado`.
- **Reescritura del test del reloj por defecto (tarea 9.4).** El test de la 6.1b acotaba el reloj por defecto entre dos llamadas a `datetime.now(UTC)`, y la 9.4 no admite lecturas de la hora real en los tests. Se reescribió como `test_sin_reloj_inyectado_la_app_usa_datetime_now_en_utc`, con un doble de `datetime` en `app.main` inyectado con `monkeypatch`.
- **README, "Estado actual" (tarea 8.2).** Además de lo que pedía la tarea, se sumó C-03 y se cambió `44 passed` por `194 passed`, que estaba desactualizado.
- **`admin_demo` sin rótulo "ficticio" (tarea 9.3).** Se dejó así porque el nombre lo fija la KB 04 (seed) y es un usuario de demostración.

### Defecto encontrado durante el apply

- **Token con `sub` no numérico.** Lo encontró la triangulación de la 6.5. Un token firmado con la clave del sistema pero con `sub` no numérico hacía que `int(sub)` lanzara `ValueError`, y la respuesta habría sido un 500. Se corrigió en `usuario_actual`, que ahora responde `401` `no_autenticado`.

### Tests sin RED propio

Debajo de cada tarea de `tasks.md` quedó el detalle. En resumen:

- **RED compartido por `ImportError`/`ModuleNotFoundError`:** los tests iniciales de la 6.5 (6), la 6.7 (4) y la 7.1 (2) fallaron juntos porque el módulo o la función todavía no existía, no por su comportamiento particular.
- **Tareas de verificación sin RED:**
  - 6.4: los 422 del login, que ya cubrían el handler del grupo 3 y el modelo de la 6.2.
  - 6.5b: el vencimiento moviendo el reloj fijo.
  - 6.8: punta a punta de RN-ACC-04 y `/health`.
- **Pasaron en el primer intento:**
  - 6.3: los tests de usuario inexistente y de contraseña incorrecta, porque la 6.2 ya rechazaba esos casos. El de cuerpo idéntico tuvo RED, pero solo por el caso del usuario inactivo.
  - 7.2: los dos tests que verifican que *no* hay seed (`test`, y `development` sin la variable).
  - Los tests de triangulación de 6.3, 6.5, 6.6, 6.7, 6.8, 7.1 y 7.2.

### Pruebas de mutación manuales

Se usaron donde un test no tenía RED propio, para comprobar que detecta el defecto que dice cubrir. Todas se restauraron editando el archivo, **salvo la de la 6.4, que se restauró con `git checkout`**. A pedido del equipo, desde la 6.5 se restauran editando el archivo.

| Tarea | Mutación en `app/` | Test que la detectó |
|---|---|---|
| 6.4 | Quitar `Field(min_length=1)` de `CredencialesEntrada` | `test_login_con_username_y_password_vacios_responde_que_no_pueden_estar_vacios` |
| 6.5b | `exp <= instante` → `exp < instante` en `decodificar_token` | `test_el_token_vence_al_mover_el_reloj_fijo_sin_esperar` (`200 == 401` en T+60) |
| 6.8 | El login devuelve `access_token=credenciales.password` | `test_la_contrasena_no_queda_en_la_base_ni_en_la_respuesta_del_login` |
| 7.2 | El `lifespan` pasa `seed_admin_password` sin hashear | 3 tests de `test_seed.py`: login, bytes del archivo y rearranque |
| 9.4 | `datetime.now(UTC)` → `datetime.now()` en `_hora_real()` | `test_sin_reloj_inyectado_la_app_usa_datetime_now_en_utc` (`[None] == [UTC]`) |

### Límites conocidos

- **La transacción del seed no se prueba con un test.** Que `sembrar_admin_demo` escribe dentro de `transaccion()` se verifica leyendo `app/db/seed.py`. Como la conexión está en autocommit, el test de "otra conexión ve la fila" pasaría igual sin la transacción.
- **El ejemplo de `Authorization: Bearer` del README no se pudo ejecutar.** Usa `<ruta-protegida>`, porque `app/` todavía no tiene rutas protegidas; llegan desde C-04. El mecanismo lo cubren `test_usuario_actual.py` y `test_requiere_rol.py`, sobre las rutas de `tests/api/rutas_prueba.py`.
- **Escenarios cubiertos por una combinación de tests:**
  - *Misma contraseña, hashes distintos* se verifica sobre `hashear` dos veces, no sobre dos filas de la tabla. La fixture `crear_usuario` usa la misma función.
  - *Error sin detalles por campo* verifica las claves exactas `{codigo, mensaje}` sobre la ruta de prueba que lanza `NoAutenticado`. Sobre una ruta protegida real sin token, el test verifica `codigo` y la cabecera `WWW-Authenticate`. Las dos pasan por el mismo handler.

### Mejoras futuras (fuera del alcance de C-03)

- **La config no valida el largo de `JWT_SECRET` para `HS512`.** Acepta `JWT_ALGORITHM=HS512` con un secreto de 32 caracteres, y en ese caso PyJWT emite `InsecureKeyLengthWarning` (pide 64 bytes para SHA-512). Por ahora solo lo advierten `.env.example` y el README ("64+ si usás `HS512`").
- **No hay límite de intentos de login**, así que el login admite fuerza bruta. Está registrado como deuda explícita fuera del MVP en los riesgos de `design.md`.

### Otras

- **Warning de Starlette sobre `httpx2`** (`StarletteDeprecationWarning`). Viene de C-01: los tests pasan y sigue como deuda en `requirements.txt`.
- **No se probó con Python 3.11**, el mínimo declarado en `AGENTS.md`. La verificación se hizo con Python 3.13.7.
- **Finales de línea.** Con `core.autocrlf=true`, `git checkout` reescribió `app/api/auth.py` con CRLF en la copia de trabajo. No afecta al repo, porque git lo guarda normalizado en LF.
