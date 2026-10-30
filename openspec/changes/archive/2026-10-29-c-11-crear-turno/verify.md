# Verify — C-11 crear-turno

- **Fecha:** 2026-10-29
- **Responsable:** Joaquín Moran
- **Comando:** `.venv/Scripts/python.exe -m pytest -q`. OpenSpec no ofrece una fase de verificación propia en esta instalación, así que la suite se ejecutó a mano.
- **Entorno:** Windows 11, Python 3.13.7, pytest 9.1.1. Rama `joaquin-c11-crear-turno`, commit `80275d7`, árbol de trabajo limpio.
- **Resultado:** `625 passed in 51.57s`, 1 warning. No hay tests fallidos, con error, salteados ni `xfail`.
  - Por origen: 524 del baseline (`main`) y 101 nuevos de C-11.
  - Desglose de los 101 (conteo con `pytest --collect-only -q` por archivo):

    | Archivo | Tests nuevos |
    |---|---|
    | `tests/api/test_turnos.py` | 45 |
    | `tests/api/test_repositorio_turnos.py` | 30 |
    | `tests/domain/test_recursos_alta.py` | 10 |
    | `tests/api/test_repositorio_bloqueos.py` | 4 (el archivo pasó de 4 a 8; los nuevos son los `test_listar_bloqueos_de_recursos_*`) |
    | `tests/domain/test_permisos_turno.py` | 7 |
    | `tests/api/test_hora_local.py` | 5 |
    | **Total** | **101** |

  - `tests/domain/test_estructura.py` (4 tests) no cambió: ya existía en el baseline y sigue en verde. `tests/api/rutas_prueba.py` sí cambió (ruta `/prueba/ahora-local`), pero no es un archivo de tests.
  - La cuenta cierra: 524 + 101 = 625.

## Cobertura de los escenarios del spec

Hay 46 escenarios en dos specs (31 en `turnos` y 15 en `auditoria-turnos`), y todos tienen al menos un test aprobado. Los nombres son de `tests/api/test_turnos.py` salvo que se indique otro archivo. Un `[...]` marca un test parametrizado y significa que pasaron todos sus casos.

### `turnos`

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Recepción crea un turno válido | `test_turnos.py::test_post_turnos_recepcion_crea_turno_reservado_201` | PASSED |
| El fin depende de la duración de la prestación | `test_turnos.py::test_post_turnos_con_limpieza_de_45_minutos_calcula_fin_10_45` | PASSED |
| Administración también puede crear turnos | `test_turnos.py::test_post_turnos_administracion_tambien_crea_turno_201` | PASSED |
| El turno creado queda persistido | `test_turnos.py::test_post_turnos_el_turno_creado_queda_persistido_en_la_base` (lectura por SQL), `test_turnos.py::test_get_turno_recepcion_existente_200` (ver observaciones) | PASSED |
| Solapamiento por profesional | `test_turnos.py::test_post_turnos_solapado_por_un_recurso_compartido_responde_409_conflicto_agenda[por_profesional]` | PASSED |
| Solapamiento por sillón | `test_turnos.py::test_post_turnos_solapado_por_un_recurso_compartido_responde_409_conflicto_agenda[por_sillon]` | PASSED |
| Solapamiento por paciente | `test_turnos.py::test_post_turnos_solapado_por_un_recurso_compartido_responde_409_conflicto_agenda[por_paciente]` | PASSED |
| Turnos contiguos aceptados | `test_turnos.py::test_post_turnos_contiguos_antes_y_despues_se_aceptan[...]` (10:30 y 09:30) | PASSED |
| Un minuto de superposición se rechaza | `test_turnos.py::test_post_turnos_con_un_minuto_de_superposicion_responde_409` | PASSED |
| Un turno cancelado no ocupa agenda | `test_turnos.py::test_post_turnos_en_el_hueco_de_un_turno_cancelado_responde_201`, `test_repositorio_turnos.py::test_listar_turnos_activos_excluye_cancelados_otro_dia_y_sin_recurso_compartido` | PASSED |
| Turno que termina después del fin de la franja | `test_turnos.py::test_post_turnos_que_cruza_el_fin_de_la_franja_responde_409_fuera_de_horario` | PASSED |
| Turno en un día sin horario | `test_turnos.py::test_post_turnos_en_dia_sin_horario_responde_409_fuera_de_horario` | PASSED |
| Turno dentro de un bloqueo del sillón | `test_turnos.py::test_post_turnos_dentro_de_un_bloqueo_de_sillon_solo_afecta_a_ese_sillon_y_horario`, `test_repositorio_bloqueos.py::test_listar_bloqueos_de_recursos_excluye_los_contiguos_a_la_ventana` | PASSED |
| Turno dentro de un bloqueo del profesional | `test_turnos.py::test_post_turnos_dentro_de_un_bloqueo_de_profesional_de_todo_el_dia_responde_409`, `test_repositorio_bloqueos.py::test_listar_bloqueos_de_recursos_incluye_un_bloqueo_de_varios_dias_que_cubre_la_ventana` | PASSED |
| Falta el sillón | `test_turnos.py::test_post_turnos_sin_sillon_id_responde_422_con_detalle_del_campo`, `test_repositorio_turnos.py::test_tabla_turno_rechaza_filas_invalidas[...]` (a nivel de tabla) | PASSED |
| Sillón inactivo | `test_turnos.py::test_post_turnos_con_recurso_inactivo_responde_422_y_no_escribe[sillon-sillon_id-sillon_2]` | PASSED |
| Profesional inactivo o prestación inactiva | `test_turnos.py::test_post_turnos_con_recurso_inactivo_responde_422_y_no_escribe[profesional-...]`, `[prestacion-...]`, `test_recursos_alta.py::test_validar_recursos_alta_con_recurso_invalido_lanza_dato_invalido_en_espanol[...]` | PASSED |
| Recurso inexistente | `test_turnos.py::test_post_turnos_con_recurso_inexistente_responde_422_y_no_escribe[...]` (los 4 ids), `test_recursos_alta.py::test_validar_recursos_alta_con_recurso_invalido_lanza_dato_invalido_en_espanol[...]` | PASSED |
| Inicio con zona horaria | `test_turnos.py::test_post_turnos_con_inicio_con_zona_horaria_responde_422_en_el_campo_inicio[...]` (`-03:00` y `Z`) | PASSED |
| La segunda reserva del mismo hueco se rechaza | `test_turnos.py::test_post_turnos_doble_reserva_del_mismo_hueco_la_segunda_responde_409`, `test_repositorio_turnos.py::test_transaccion_de_otra_conexion_espera_el_lock_y_despues_ve_el_turno_confirmado` | PASSED |
| Solo queda un turno y una auditoría | `test_turnos.py::test_post_turnos_doble_reserva_del_mismo_hueco_la_segunda_responde_409` (cuenta por SQL), `test_turnos.py::test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias` | PASSED |
| Administración tampoco puede superponer | `test_turnos.py::test_post_turnos_administracion_tampoco_puede_superponer_un_turno` | PASSED |
| Odontólogo intenta crear un turno | `test_turnos.py::test_post_turnos_odontologo_responde_403_sin_permiso_y_no_escribe` | PASSED |
| Sin token | `test_turnos.py::test_post_turnos_sin_token_responde_401_no_autenticado` | PASSED |
| Recepción tiene permiso | `test_turnos.py::test_post_turnos_recepcion_crea_turno_reservado_201` | PASSED |
| Recepción consulta un turno existente | `test_turnos.py::test_get_turno_recepcion_existente_200` | PASSED |
| Turno inexistente | `test_turnos.py::test_get_turno_inexistente_responde_404_no_encontrado`, `test_get_turno_inexistente_responde_404_tambien_al_odontologo` | PASSED |
| Consulta sin token | `test_turnos.py::test_get_turno_sin_token_responde_401_no_autenticado` | PASSED |
| Odontólogo consulta un turno propio | `test_turnos.py::test_get_turno_odontologo_ve_su_propio_turno_200`, `test_permisos_turno.py::test_puede_ver_turno_odontologo_del_mismo_profesional_devuelve_true` | PASSED |
| Odontólogo consulta un turno de otro profesional | `test_turnos.py::test_get_turno_odontologo_de_otro_profesional_responde_403_sin_datos_del_turno`, `test_permisos_turno.py::test_puede_ver_turno_odontologo_de_otro_profesional_devuelve_false` | PASSED |
| Administración consulta un turno de cualquier profesional | `test_turnos.py::test_get_turno_administracion_ve_el_turno_de_la_profesional_b_200`, `test_permisos_turno.py::test_puede_ver_turno_administracion_y_recepcion_ven_cualquier_profesional[...]` | PASSED |

El spec `turnos` tiene 8 requisitos y 31 escenarios; la tabla los lista a todos.

### `auditoria-turnos`

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta registrada con usuario y fecha | `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo`, `test_repositorio_turnos.py::test_crear_turno_guarda_turno_y_un_unico_registro_de_auditoria_crear` | PASSED |
| Antes nulo y después con el turno creado | `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo` (`antes is None`, `despues == creado`) | PASSED |
| El turno guarda su creador | `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo` (`creado_por`, `creado_en`), `test_repositorio_turnos.py::test_crear_turno_guarda_turno_y_un_unico_registro_de_auditoria_crear` | PASSED |
| Conversión de UTC a hora local | `test_hora_local.py::test_a_hora_local_convierte_utc_a_buenos_aires_sin_tzinfo`, `test_obtener_ahora_local_devuelve_la_hora_local_del_reloj_fijo`, `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo` | PASSED |
| Cambio de día al convertir | `test_hora_local.py::test_a_hora_local_cambia_de_dia_al_convertir`, `test_turnos.py::test_post_turnos_la_hora_local_cruza_de_dia_respecto_de_utc` | PASSED |
| Sin offset en el texto guardado | `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo`, `test_post_turnos_la_hora_local_cruza_de_dia_respecto_de_utc` (ver observaciones) | PASSED |
| Claves exactas del snapshot | `test_repositorio_turnos.py::test_snapshot_turno_tiene_exactamente_las_8_claves_en_orden_y_fechas_iso`, `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo` (`list(json.loads(despues)) == CLAVES_SNAPSHOT`) | PASSED |
| Valores coinciden con el turno | `test_repositorio_turnos.py::test_snapshot_turno_tiene_exactamente_las_8_claves_en_orden_y_fechas_iso`, `test_snapshot_turno_cancelado_de_tarde_con_otros_ids`, `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo` (`despues == creado`) | PASSED |
| El snapshot no incluye datos personales | `test_turnos.py::test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo`, `test_repositorio_turnos.py::test_snapshot_turno_tiene_exactamente_las_8_claves_en_orden_y_fechas_iso` (ver observaciones) | PASSED |
| Rechazo 409 sin auditoría | `test_turnos.py::test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias` | PASSED |
| Rechazo 422 sin auditoría | `test_turnos.py::test_post_turnos_con_recurso_inactivo_responde_422_y_no_escribe[...]`, `test_post_turnos_con_recurso_inexistente_responde_422_y_no_escribe[...]` (verifican por SQL que no quedó turno ni auditoría) | PASSED |
| Falla al escribir la auditoría | `test_repositorio_turnos.py::test_crear_turno_con_creado_por_inexistente_no_deja_turno_ni_auditoria`, `test_crear_turno_si_falla_la_auditoria_revierte_tambien_el_turno` | PASSED |
| La base rechaza la modificación | `test_repositorio_turnos.py::test_auditoria_turno_rechaza_update_y_el_registro_queda_igual` | PASSED |
| La base rechaza el borrado | `test_repositorio_turnos.py::test_auditoria_turno_rechaza_delete_y_el_registro_queda_igual` | PASSED |
| Sin rutas de escritura de auditoría | `test_turnos.py::test_no_hay_rutas_para_modificar_o_borrar_turnos_ni_auditoria[...]` (PUT, PATCH y DELETE sobre `/turnos/{id}` y `/auditoria/turnos/{id}`, 6 casos) | PASSED |

El spec `auditoria-turnos` tiene 5 requisitos y 15 escenarios; la tabla los lista a todos.

Ningún escenario quedó sin test.

## Cobertura de las RN tocadas

| RN | Tests principales |
|---|---|
| RN-TUR-01, RN-TUR-14 (estado `reservado`, fin calculado) | `test_post_turnos_recepcion_crea_turno_reservado_201`, `test_post_turnos_con_limpieza_de_45_minutos_calcula_fin_10_45` |
| RN-TUR-02 (sillón obligatorio) | `test_post_turnos_sin_sillon_id_responde_422_con_detalle_del_campo`, `test_tabla_turno_rechaza_filas_invalidas[...]` |
| RN-TUR-03, RN-TUR-12 (solapamiento por profesional, sillón, paciente) | `test_post_turnos_solapado_por_un_recurso_compartido_responde_409_conflicto_agenda[...]` |
| RN-TUR-04 (semiabierto) | `test_post_turnos_contiguos_antes_y_despues_se_aceptan[...]`, `test_post_turnos_con_un_minuto_de_superposicion_responde_409` |
| RN-TUR-05 (horario y bloqueos) | `test_post_turnos_que_cruza_el_fin_de_la_franja_responde_409_fuera_de_horario`, `test_post_turnos_en_dia_sin_horario_responde_409_fuera_de_horario`, `test_post_turnos_dentro_de_un_bloqueo_de_sillon_solo_afecta_a_ese_sillon_y_horario` |
| RN-TUR-08 (cancelado no ocupa agenda) | `test_post_turnos_en_el_hueco_de_un_turno_cancelado_responde_201` |
| RN-TUR-11 (nadie fuerza solapamientos) | `test_post_turnos_administracion_tampoco_puede_superponer_un_turno`, `test_post_turnos_doble_reserva_del_mismo_hueco_la_segunda_responde_409` |
| RN-REC-03 (recursos activos) | `test_validar_recursos_alta_*`, `test_post_turnos_con_recurso_inactivo_responde_422_y_no_escribe[...]` |
| RN-ACC-01, RN-ACC-02 (token y rol) | `test_post_turnos_odontologo_responde_403_sin_permiso_y_no_escribe`, `test_post_turnos_sin_token_responde_401_no_autenticado`, `test_get_turno_sin_token_responde_401_no_autenticado` |
| RN-ACC-03 (odontólogo solo ve lo suyo) | `test_puede_ver_turno_*` (7 casos), `test_get_turno_odontologo_*` |
| RN-AUD-01 (auditoría del alta) | `test_crear_turno_guarda_turno_y_un_unico_registro_de_auditoria_crear`, `test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo` |
| RN-AUD-02 (solo agregado) | `test_auditoria_turno_rechaza_update_y_el_registro_queda_igual`, `test_auditoria_turno_rechaza_delete_y_el_registro_queda_igual`, `test_no_hay_rutas_para_modificar_o_borrar_turnos_ni_auditoria[...]` |
| RN-AUD-03 (atomicidad) | `test_crear_turno_con_creado_por_inexistente_no_deja_turno_ni_auditoria`, `test_crear_turno_si_falla_la_auditoria_revierte_tambien_el_turno`, `test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias` |
| RN-GLO-01 (errores en español con código) | los tests 409, 422, 403, 401 y 404 de `test_turnos.py` verifican `codigo` y `mensaje`; `test_validar_recursos_alta_*` |

El mapeo completo está en la tarea 7.2 de `tasks.md`.

## Chequeos adicionales

- **Reglas duras** (tarea 7.3). Las 14 reglas de `CLAUDE.md`:

| # | Regla | Cómo la cumple C-11 y evidencia |
|---|---|---|
| 1 | Dominio puro | `app/domain/` no importa `fastapi`, `starlette`, `app.db` ni `app.api`. `rg` sobre `app/domain` no encuentra coincidencias; `tests/domain/test_estructura.py::test_dominio_no_importa_framework_ni_capas_externas_ni_reloj_del_sistema` sigue en verde. |
| 2 | Sin `datetime.now()`/`date.today()` en el dominio | `rg "datetime.now\|date.today\|utcnow" app/domain` sin coincidencias. `ahora` llega por `obtener_ahora_local` (dependencia del router) y los tests usan `RelojFijo`. `tests/` no usa `sleep`, `datetime.now` ni `date.today` salvo el doble de `test_dependencias.py` heredado de C-03. |
| 3 | Intervalos semiabiertos | `validar_alta` (C-10) y las consultas `listar_turnos_activos_del_dia` y `listar_bloqueos_de_recursos` usan `[inicio, fin)`. Tests: `test_post_turnos_contiguos_antes_y_despues_se_aceptan[...]`, `test_post_turnos_con_un_minuto_de_superposicion_responde_409`, `test_listar_bloqueos_de_recursos_excluye_los_contiguos_a_la_ventana`, bloqueo de sillón que termina a las 12:00 y turno a las 12:00 con `201`. |
| 4 | Sin SQL interpolado | Búsqueda de f-strings, `%`, `.format()` y concatenación en `execute*` de `app/` y `tests/` sin coincidencias. El único `+` de `repositorio_turnos.py` es aritmética de fechas con `timedelta`. Los `PRAGMA busy_timeout` del test 5.8 son literales. |
| 5 | Turno y auditoría en una transacción | `POST /turnos` abre un único `with transaccion(conexion):` (`app/api/turnos.py`) y `crear_turno` escribe la fila y `registrar_auditoria` dentro de él. Tests: `test_crear_turno_si_falla_la_auditoria_revierte_tambien_el_turno`, `test_crear_turno_con_creado_por_inexistente_no_deja_turno_ni_auditoria`, `test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias`. |
| 6 | `auditoria_turno` solo INSERT | Triggers `auditoria_turno_sin_update` y `auditoria_turno_sin_delete` en `app/db/esquema.sql`. `rg "(UPDATE\|DELETE FROM) auditoria_turno" app` sin coincidencias; en `tests/` solo aparecen en los dos tests que verifican que la base los rechaza. Tests: `test_auditoria_turno_rechaza_update_y_el_registro_queda_igual`, `test_auditoria_turno_rechaza_delete_y_el_registro_queda_igual`. |
| 7 | Errores JSON en español con código | Sin handlers nuevos: se reusan los de C-03 (`ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo` → 409; `DatoInvalido` y validación Pydantic → 422; `SinPermiso` → 403; `NoAutenticado` → 401; `HTTPException(404)` → `no_encontrado`). Los tests de `test_turnos.py` verifican `codigo` y `mensaje` en cada caso. |
| 8 | Sin reglas de negocio en el router | `app/api/turnos.py` solo hace Pydantic en la frontera, abre la transacción, carga el contexto, llama a `validar_recursos_alta`, `validar_alta` y `puede_ver_turno` (en `app/domain/`) y traduce `None` a 404 (tarea 6.4). |
| 9 | Sin `.env` versionado ni secretos | `.env` no está en `git ls-files` y `.gitignore` lo excluye (línea 4). C-11 no agregó variables de entorno; la única dependencia nueva es `tzdata`. |
| 10 | Datos ficticios | Los tests usan "Paciente Ficticio 1/2" con DNI `"00000001 (ficticio)"` y `"00000002 (ficticio)"`, profesionales "Odontólogo Ficticio A" y "Odontóloga Ficticia B", y usuarios `admin_ficticio`, `recepcion_ficticia`, `odontologo_a_ficticio`. |
| 11 | Cada RN-xx con test | Ver "Cobertura de las RN tocadas" y tarea 7.2. Los tests de `tests/domain/` (`test_recursos_alta.py`, `test_permisos_turno.py`) corren sin base de datos ni HTTP. |
| 12 | `snake_case` y type hints | Revisado en la tarea 6.4: funciones públicas de `app/api/turnos.py`, `app/db/repositorio_turnos.py` y `app/domain/reglas_turno.py` con type hints y `snake_case`; dependencias con `Annotated`. |
| 13 | Sin commit ni push sin pedido | El apply no hizo commits por su cuenta: los commits del historial (`423fc53` a `80275d7`) se hicieron a pedido del usuario, por grupos de tareas. Este `verify.md` no se commiteó. |
| 14 | No tocar `knowledge-base/`, `CHANGES.md`, `docs/discovery/` | `git diff 3a8e516..HEAD` sobre `knowledge-base/` y `CHANGES.md` está vacío. Los cambios de C-11 se limitan a `app/`, `tests/`, `requirements.txt` y `openspec/changes/c-11-crear-turno/`. |

- **Transacción en el router (D1).** La transacción vive en `post_turno` (`app/api/turnos.py:85`, `with transaccion(conexion):`) y `transaccion()` emite `BEGIN IMMEDIATE` (`app/db/conexion.py:40`). El contexto se lee con el lock de escritura ya tomado, así que dos altas del mismo hueco no pasan juntas.
- **Concurrencia real (tarea 5.8).** `test_transaccion_de_otra_conexion_espera_el_lock_y_despues_ve_el_turno_confirmado` y `test_transaccion_de_otra_conexion_toma_el_lock_cuando_a_revierte` usan dos conexiones a la misma base temporal, sin hilos ni `sleep`. El `busy_timeout` corto (50 ms) se fija solo en la conexión B del test; producción sigue en 5000 ms. Verificado por mutación (ver más abajo).
- **Suite completa.** `625 passed`, igual que el conteo de la tarea 7.1. `git status` quedó limpio después de correrla (la suite no crea `turnos.db` en la raíz).
- **`openspec validate c-11-crear-turno --strict`** respondió `Change 'c-11-crear-turno' is valid`.

## Observaciones del apply

### Tests sin RED propio

Debajo de cada tarea de `tasks.md` quedó el detalle. Todos pasaron en el primer intento, porque el comportamiento ya existía o el GREEN anterior ya implementaba la lógica general:

| Tarea | Tests | Motivo |
|---|---|---|
| 4.4 | `test_crear_turno_con_creado_por_inexistente_no_deja_turno_ni_auditoria`, `test_crear_turno_si_falla_la_auditoria_revierte_tambien_el_turno` | `transaccion()` (C-01) ya hacía rollback ante cualquier excepción, como en C-03: verifican un comportamiento que ya existía. |
| 5.1 (triangulación) | `test_post_turnos_con_limpieza_de_45_minutos_calcula_fin_10_45`, `test_post_turnos_administracion_tambien_crea_turno_201`, `test_post_turnos_el_turno_creado_queda_persistido_en_la_base` | El GREEN de `test_post_turnos_recepcion_crea_turno_reservado_201` ya implementaba la lógica general. El de persistencia lee por SQL porque `GET /turnos/{id}` es la tarea 6.1. |
| 5.2 | `test_post_turnos_solapado_por_un_recurso_compartido_responde_409_conflicto_agenda` (3 casos), `test_post_turnos_contiguos_antes_y_despues_se_aceptan`, `test_post_turnos_con_un_minuto_de_superposicion_responde_409`, `test_post_turnos_en_el_hueco_de_un_turno_cancelado_responde_201` | Las reglas ya vivían en `validar_alta` (C-10) y en las consultas del grupo 4; el router solo las orquesta. Mutación: pasar `weekday() + 1` al repositorio de horarios hace fallar 18 tests. |
| 5.3 | `test_post_turnos_que_cruza_el_fin_de_la_franja_responde_409_fuera_de_horario`, `test_post_turnos_en_dia_sin_horario_responde_409_fuera_de_horario`, `test_post_turnos_dentro_de_un_bloqueo_de_sillon_solo_afecta_a_ese_sillon_y_horario`, `test_post_turnos_dentro_de_un_bloqueo_de_profesional_de_todo_el_dia_responde_409` | Las reglas ya estaban en `validar_alta` (C-10) y `listar_bloqueos_de_recursos` (4.6). |
| 5.4 | `test_post_turnos_sin_sillon_id_responde_422_con_detalle_del_campo`, `test_post_turnos_con_recurso_inactivo_responde_422_y_no_escribe` (3 casos), `test_post_turnos_con_recurso_inexistente_responde_422_y_no_escribe` (4 casos), `test_post_turnos_con_inicio_con_zona_horaria_responde_422_en_el_campo_inicio` (2 casos) | Los resuelven `CrearTurnoRequest` (Pydantic, `NaiveDatetime`) y `validar_recursos_alta` (2.1), ya implementados. |
| 5.5 | `test_post_turnos_doble_reserva_del_mismo_hueco_la_segunda_responde_409`, `test_post_turnos_administracion_tampoco_puede_superponer_un_turno` | La garantía viene de leer el contexto dentro de `transaccion()` (BEGIN IMMEDIATE), ya armado en 5.1; el test es secuencial, como pide el design. |
| 5.6 | `test_post_turnos_odontologo_responde_403_sin_permiso_y_no_escribe`, `test_post_turnos_sin_token_responde_401_no_autenticado` | `requiere_rol(ADMINISTRACION, RECEPCION)` ya estaba en la firma del endpoint desde 5.1 (`requiere_rol` es de C-03). |
| 5.7 | `test_post_turnos_registra_auditoria_crear_con_hora_local_y_snapshot_completo`, `test_post_turnos_la_hora_local_cruza_de_dia_respecto_de_utc`, `test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias` | `crear_turno` (4.3) y `obtener_ahora_local` (1.3) ya hacían el trabajo. Mutación: usar `creado_en=entrada.inicio` en el router hace fallar 2 tests. En el test de cruce de día se emite un token nuevo tras avanzar el reloj, porque el anterior vence. |
| 5.8 | `test_transaccion_de_otra_conexion_espera_el_lock_y_despues_ve_el_turno_confirmado`, `test_transaccion_de_otra_conexion_toma_el_lock_cuando_a_revierte` | `transaccion()` (C-01) ya usaba `BEGIN IMMEDIATE`. Mutación: `BEGIN IMMEDIATE` → `BEGIN DEFERRED` en `app/db/conexion.py` hace fallar el primero (B obtiene el lock). |
| 6.1 (triangulación) | `test_get_turno_administracion_ve_el_turno_de_la_profesional_b_200`, `test_get_turno_inexistente_responde_404_no_encontrado`, `test_get_turno_sin_token_responde_401_no_autenticado` | El GREEN de `test_get_turno_recepcion_existente_200` ya implementaba 404, 403 y 401. |
| 6.2 | `test_get_turno_odontologo_ve_su_propio_turno_200`, `test_get_turno_odontologo_de_otro_profesional_responde_403_sin_datos_del_turno`, `test_get_turno_inexistente_responde_404_tambien_al_odontologo` | `puede_ver_turno` (2.2) ya estaba conectado en 6.1 (404 antes que 403, D7). Mutación: reemplazar el chequeo `puede_ver_turno` por `if False` hace fallar 1 test. |
| 6.3 | `test_no_hay_rutas_para_modificar_o_borrar_turnos_ni_auditoria` (6 casos) | No existen esas rutas: `/turnos/{id}` responde 405 y `/auditoria/...` 404. |

### Pruebas de mutación manuales

Se usaron donde un test no tenía RED propio, para comprobar que detecta el defecto que dice cubrir. Todas se restauraron editando el archivo (nunca con `git checkout`). La de 6.2 se restauró desde una copia del archivo.

| Tarea | Mutación en `app/` | Qué detectó |
|---|---|---|
| 5.2 | `weekday() + 1` al repositorio de horarios | 18 tests |
| 5.7 | `creado_en=entrada.inicio` en el router | 2 tests |
| 5.8 | `BEGIN IMMEDIATE` → `BEGIN DEFERRED` en `app/db/conexion.py` | `test_transaccion_de_otra_conexion_espera_el_lock_y_despues_ve_el_turno_confirmado` |
| 6.2 | chequeo `puede_ver_turno` reemplazado por `if False` | 1 test |

### Escenarios cubiertos por una combinación de tests o por una aserción indirecta

- **Sin offset en el texto guardado.** No hay un test con una expresión regular `YYYY-MM-DDTHH:MM:SS`. Lo cubre la igualdad exacta con cadenas como `"2026-01-05T09:00:00"` y `"2026-01-05T23:30:00"` sobre `ocurrio_en` y `creado_en`, que excluye cualquier `+`, `Z` o `-HH:MM`.
- **El snapshot no incluye datos personales.** No hay un test que busque nombre o DNI. Lo cubre la aserción de que las claves son exactamente las ocho del formato canónico (`list(json.loads(despues)) == CLAVES_SNAPSHOT`), todas ids, fechas y estado.
- **El turno creado queda persistido.** El test de la tarea 5.1 lee por SQL; la consulta por `GET /turnos/{id}` del escenario la cubre `test_get_turno_recepcion_existente_200`, pero no hay un único test que haga `POST` y luego `GET` con comparación campo por campo.
- **Solo queda un turno y una auditoría.** Se verifica con el test secuencial de doble reserva (cuenta por SQL) y no con hilos, como pide el design (no-goal de concurrencia real); la serialización real la cubren los tests de la tarea 5.8.

### Discrepancias

- Ninguna. El conteo de la tarea 7.1 se confirmó: 45 + 30 + 10 + 4 + 7 + 5 = 101 tests nuevos, 524 + 101 = 625.

### Límites conocidos

- **Altas en el pasado.** `POST /turnos` acepta un `inicio` anterior al momento actual: la KB no lo prohíbe y RN-TUR-09 aplica solo a cancelar y reprogramar (D9). Ningún test lo fija como comportamiento.
- **Sin concurrencia con hilos reales.** La serialización la garantiza `BEGIN IMMEDIATE` y se prueba con dos conexiones (tarea 5.8), no con dos hilos o procesos compitiendo.
- **Microsegundos en `inicio`.** `isoformat(timespec="seconds")` trunca; un `inicio` con fracciones se validaría con un valor y se guardaría con otro (riesgo aceptado en `design.md`).

### Mejoras futuras (fuera del alcance de C-11)

- **Rechazar altas en el pasado (D9).** `validar_alta` no recibe `ahora`. Si se decide prohibirlo, hace falta una regla de dominio que reciba `ahora` (de `obtener_ahora_local`) y lance `TurnoNoModificable` o `DatoInvalido`; requiere una RN nueva en la KB y un change propio.
- **Índice sobre `auditoria_turno (turno_id)`** cuando `C-15` defina su consulta.

### Pendientes del workflow

- **Pasar a los autores de `C-12`, `C-13` y `C-14` la sección "Ajustes para C-12/C-13/C-14" de `design.md`** antes de su `/opsx:apply`. Los designs de esos changes no se modificaron desde C-11.
- **Archivar y marcar `C-11` como `[x]` en `CHANGES.md`** solo con autorización explícita del usuario (regla dura 14). Este verify no archiva.
- **Lint no ejecutado.** `ruff` no está instalado en el entorno (`No module named ruff`), así que no se corrió ningún linter. El estilo (`snake_case`, type hints, `Annotated`) se revisó a mano en la tarea 6.4.
- **No se probó con Python 3.11**, el mínimo declarado en `CLAUDE.md`. La verificación se hizo con Python 3.13.7.
- **Warning de Starlette sobre `httpx2`** (`StarletteDeprecationWarning`). Viene de C-01: los tests pasan y sigue como deuda en `requirements.txt`.
- **No se hizo verificación manual contra `uvicorn`** de `POST /turnos` y `GET /turnos/{id}`: la cobertura es solo por `TestClient`.
