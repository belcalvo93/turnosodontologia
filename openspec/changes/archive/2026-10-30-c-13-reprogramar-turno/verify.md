# Verify — C-13 reprogramar-turno

- **Fecha:** 2026-10-30
- **Comando:** `.venv/Scripts/python.exe -m pytest`. OpenSpec no ofrece una fase de verificación propia en esta instalación, así que la suite se ejecutó a mano.
- **Entorno:** Windows 11, Python 3.13.7, pytest 9.1.1. Rama `joaquin-c13-reprogramar-turno`, HEAD `22f8535`. El árbol de trabajo tiene archivos sin commitear: `tests/api/test_reprogramar_turno.py` (refuerzo de los mensajes 422 y los tests de las tareas 3.5 y 3.6) y `openspec/changes/c-13-reprogramar-turno/tasks.md`. Este `verify.md` también queda sin commitear.
- **Resultado:** `701 passed, 1 warning in 61.78s (0:01:01)`. No hay tests fallidos, con error, salteados ni `xfail`. El warning es el aviso de `httpx` de Starlette, ajeno al cambio.
  - Por origen: 650 del baseline y 51 nuevos de C-13.
  - Desglose de los 51 (conteo con `pytest --collect-only -q` por archivo, contra el estado en `3789d8d`):

    | Archivo | Tests nuevos |
    |---|---|
    | `tests/api/test_reprogramar_turno.py` | 29 (archivo nuevo) |
    | `tests/domain/test_reprogramar_turno.py` | 16 (el archivo pasó de 9 a 25) |
    | `tests/api/test_repositorio_turnos.py` | 6 (los `test_reprogramar_turno_*`) |
    | **Total** | **51** |

  - La cuenta cierra: 650 + 51 = 701. Por grupo: 650 → 666 (grupo 1) → 672 (grupo 2) → 699 (grupo 3) → 701 (tareas 3.5 y 3.6).
- **`openspec validate c-13-reprogramar-turno --strict`:** `Change 'c-13-reprogramar-turno' is valid`.

## Cobertura de los escenarios del spec

El spec `reprogramar-turno` tiene 6 requisitos y 9 escenarios; todos tienen al menos un test aprobado. Nombres en `tests/api/test_reprogramar_turno.py` (API) y `tests/domain/test_reprogramar_turno.py` (dominio) salvo que se indique otro archivo. Un `[...]` marca un test parametrizado y significa que pasaron todos sus casos.

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Reprogramación válida de un turno futuro | API: `test_reprogramar_recepcion_mueve_el_turno_200_conservando_el_id`, `test_reprogramar_registra_auditoria_reprogramar_con_antes_y_despues`. Dominio: `test_reprogramar_turno_futuro_exitoso_mantiene_id_y_recalcula_intervalo`. Repositorio: `test_repositorio_turnos.py::test_reprogramar_turno_actualiza_horario_y_registra_auditoria_reprogramar` | PASSED |
| Reprogramación que solapa parcialmente con el horario anterior | API: `test_reprogramar_sobre_su_propio_horario_previo_200`. Dominio: `test_reprogramar_sobre_propio_horario_anterior_no_genera_conflicto` | PASSED |
| Conflicto con otro turno activo | API: `test_reprogramar_sobre_otro_turno_del_profesional_409_conflicto_agenda` (verifica turno intacto y sin fila nueva en `auditoria_turno`). Dominio: `test_reprogramar_solapa_con_otro_turno_activo_lanza_conflicto_agenda`, `test_reprogramar_solapa_con_turno_del_mismo_sillon_otro_profesional_lanza_conflicto`, `test_reprogramar_solapa_con_turno_del_mismo_paciente_lanza_conflicto` | PASSED |
| Intento de reprogramar un turno pasado (en curso y pasado) | API: `test_reprogramar_turno_pasado_en_hora_local_409`, `test_reprogramar_turno_futuro_en_hora_local_aunque_en_utc_ya_pasaria_200`. Dominio: `test_reprogramar_turno_pasado_lanza_turno_no_modificable`, `test_reprogramar_turno_en_curso_instante_exacto_lanza_turno_no_modificable` | PASSED |
| Intento de reprogramar un turno cancelado | API: `test_reprogramar_turno_cancelado_409_turno_no_modificable`. Dominio: `test_reprogramar_turno_cancelado_lanza_turno_no_modificable` | PASSED |
| Odontólogo intentando reprogramar | API: `test_reprogramar_odontologo_403_sin_permiso_y_no_cambia_nada`, `test_reprogramar_odontologo_sobre_turno_inexistente_responde_403_antes_que_404` | PASSED |
| Nuevo profesional inexistente | API: `test_reprogramar_con_recurso_nuevo_inexistente_422_dato_invalido[nuevo_profesional_id-...]` (mensaje "El profesional indicado no existe."). Dominio: `test_nuevo_profesional_inexistente_o_inactivo_lanza_dato_invalido[None-no existe]` | PASSED |
| Nuevo sillón inactivo | API: `test_reprogramar_con_recurso_nuevo_inactivo_422_dato_invalido[sillon-...]` (mensaje "El sillón indicado está inactivo."). Dominio: `test_nuevo_sillon_inexistente_o_inactivo_lanza_dato_invalido[...]` | PASSED |
| Turno cancelado con nuevo sillón inactivo | API: `test_reprogramar_turno_cancelado_con_nuevo_sillon_inactivo_409_y_sin_auditoria`. Dominio: `test_turno_cancelado_con_nuevo_sillon_inactivo_lanza_turno_no_modificable` | PASSED |

Además de los 9 escenarios, las tareas 3.5 y 3.6 agregaron dos tests que el spec no describe como escenarios: `test_reprogramar_como_administracion_a_un_hueco_ocupado_409_conflicto_agenda` (RN-TUR-11) y `test_dos_reprogramaciones_concurrentes_al_mismo_hueco_una_200_y_la_otra_409` (SE-06, C-11 D1).

Los escenarios de rechazo (conflicto, 422 y cancelado con sillón inactivo) comprueban por SQL que el turno quedó igual y que la cantidad de filas de `auditoria_turno` no cambió (`_assert_rechazo_sin_cambios`).

## Cobertura de las RN tocadas

| RN | Tests principales |
|---|---|
| RN-TUR-01 (fin recalculado según la prestación) | `test_reprogramar_recepcion_mueve_el_turno_200_conservando_el_id` (fin 11:30), `test_reprogramar_turno_futuro_exitoso_mantiene_id_y_recalcula_intervalo` |
| RN-TUR-03, RN-TUR-12 (solapamiento por profesional, sillón y paciente) | `test_reprogramar_solapa_con_otro_turno_activo_lanza_conflicto_agenda`, `..._del_mismo_sillon_otro_profesional_...`, `..._del_mismo_paciente_...` (dominio); `test_reprogramar_sobre_otro_turno_del_profesional_409_conflicto_agenda` (API) |
| RN-TUR-05 (bloqueos) | `test_reprogramar_dentro_de_bloqueo_lanza_dentro_de_bloqueo`, `test_reprogramar_dentro_de_bloqueo_de_sillon_lanza_dentro_de_bloqueo`, `test_reprogramar_dentro_de_un_bloqueo_409_dentro_de_bloqueo` |
| RN-TUR-07 (validar en el nuevo horario) | `test_reprogramar_a_otro_profesional_valida_el_horario_de_ese_profesional`, `test_reprogramar_fuera_de_horario_409_fuera_de_horario`, `test_reprogramar_contiguo_a_otro_turno_200` |
| RN-TUR-08 (el propio turno y los cancelados no ocupan agenda) | `test_reprogramar_sobre_propio_horario_anterior_no_genera_conflicto`, `test_reprogramar_ignora_turno_cancelado_del_mismo_paciente`, `test_reprogramar_sobre_su_propio_horario_previo_200` |
| RN-TUR-09 (no reprogramar pasados) | `test_reprogramar_turno_pasado_lanza_turno_no_modificable`, `test_reprogramar_turno_en_curso_instante_exacto_...`, `test_reprogramar_turno_pasado_en_hora_local_409` |
| RN-TUR-10 (no reprogramar cancelados) | `test_reprogramar_turno_cancelado_lanza_turno_no_modificable`, `test_reprogramar_turno_cancelado_409_turno_no_modificable` |
| RN-TUR-11 (nadie fuerza solapamientos) | `test_reprogramar_como_administracion_a_un_hueco_ocupado_409_conflicto_agenda` |
| RN-PRO-01 (horario de atención) | `test_reprogramar_fuera_de_horario_atencion_lanza_fuera_de_horario`, `test_reprogramar_fuera_de_horario_409_fuera_de_horario` |
| RN-REC-03 (recursos activos) | `test_nuevo_profesional_inexistente_o_inactivo_lanza_dato_invalido[...]`, `test_nuevo_sillon_inexistente_o_inactivo_lanza_dato_invalido[...]`, `test_recurso_nuevo_inactivo_con_conflicto_...` (dominio); los 422 del API |
| RN-ACC-01, RN-ACC-02 (token y rol) | `test_reprogramar_sin_token_401_no_autenticado`, `test_reprogramar_odontologo_403_sin_permiso_y_no_cambia_nada`, `test_reprogramar_administracion_tambien_puede_200` |
| RN-AUD-01 (auditoría con antes y después) | `test_reprogramar_registra_auditoria_reprogramar_con_antes_y_despues`, `test_reprogramar_turno_actualiza_horario_y_registra_auditoria_reprogramar` |
| RN-AUD-03 (atomicidad) y SE-06 (doble reserva del mismo hueco) | `test_dos_reprogramaciones_concurrentes_al_mismo_hueco_una_200_y_la_otra_409`, `test_reprogramar_turno_con_usuario_inexistente_revierte_el_cambio`, `test_reprogramar_turno_si_falla_la_auditoria_revierte_tambien_el_update`, y los rechazos 409/422 del API con conteo de auditoría |
| RN-GLO-01 (errores en español con código) | Los tests del API verifican `codigo` (`conflicto_agenda`, `dentro_de_bloqueo`, `fuera_de_horario`, `turno_no_modificable`, `dato_invalido`, `sin_permiso`, `no_autenticado`, `no_encontrado`) y los 422 de recurso verifican el `mensaje` exacto |

## Chequeos adicionales

- **Reglas duras** (tarea 4.2). Las 14 reglas de `CLAUDE.md`, contra los commits propios de C-13 (`git diff 3789d8d HEAD`, que toca `app/api/turnos.py`, `app/db/repositorio_turnos.py`, `app/domain/reglas_turno.py`, tests y `openspec/changes/c-13-reprogramar-turno/`) más el árbol de trabajo. El rango `c16f40e...HEAD` pedido incluye además la fusión de C-14 (`app/api/agenda.py`, `app/db/repositorio_agenda.py`, `app/domain/usuarios.py`, `CHANGES.md`, `docs/bitacora/`), que es de Hernán y no de este cambio; ahí aparece un cambio en `CHANGES.md` que no hizo C-13.

| # | Regla | Evidencia |
|---|---|---|
| 1 | Dominio puro | `rg "fastapi\|starlette\|app\.db\|app\.api" app/domain` sin coincidencias. `app/domain/reglas_turno.py` solo importa de `app.domain`. `tests/domain/test_estructura.py` sigue en verde. |
| 2 | Sin `datetime.now()` en el dominio | `rg "datetime.now\|date.today\|utcnow" app/domain` sin coincidencias. `validar_reprogramacion` recibe `ahora`; el router usa `obtener_ahora_local`. Los tests no usan `now`, `today` ni `sleep` y usan `RelojFijo`. |
| 3 | Intervalos semiabiertos | `validar_reprogramacion` delega en `validar_alta` y `solapan` (`[inicio, fin)`). Tests: `test_reprogramar_contiguo_al_turno_del_mismo_sillon_es_valido` (dominio) y `test_reprogramar_contiguo_a_otro_turno_200` (API). |
| 4 | Sin SQL interpolado | El único SQL nuevo es `UPDATE turno SET inicio = ?, fin = ?, profesional_id = ?, sillon_id = ? WHERE id = ?` (`_ACTUALIZAR_REPROGRAMACION`, parametrizado). El filtro de `git diff` sobre `app/` para `execute` con f-string, `+`, `%` o `.format` no encuentra nada. |
| 5 | Turno y auditoría en una transacción | `post_reprogramar_turno` abre un único `with transaccion(conexion):` que incluye `obtener_turno`, la carga de contexto, la validación y `reprogramar_turno`; esta no abre transacción propia y llama a `registrar_auditoria`. Tests: `test_reprogramar_turno_si_falla_la_auditoria_revierte_tambien_el_update`, `test_reprogramar_turno_con_usuario_inexistente_revierte_el_cambio`. |
| 6 | `auditoria_turno` solo INSERT | `rg "(UPDATE\|DELETE FROM) auditoria_turno" app` sin coincidencias. `reprogramar_turno` solo inserta vía `registrar_auditoria`. Los triggers de C-11 siguen protegiendo la tabla (sus tests no cambiaron y están en verde). |
| 7 | Errores JSON en español con código | Sin handlers nuevos: se reusan los de C-03 y C-11. El 404 es `HTTPException(404)` → `no_encontrado`. Los tests verifican `codigo` y `mensaje`. |
| 8 | Sin reglas de negocio en el router | El router solo hace Pydantic en la frontera, abre la transacción, carga contexto y llama a `validar_reprogramacion`. Los `if` nuevos del router son: 404 si el turno no existe, elegir el id de profesional o sillón a consultar (enviado o actual), no cargar un recurso cuyo id no se envió, y un guard de invariante de la prestación (ver adiciones). Ninguno decide estado, recursos activos ni agenda. |
| 9 | Sin `.env` ni secretos | `.env` no está en `git ls-files`. C-13 no agregó variables de entorno ni dependencias. |
| 10 | Datos ficticios | Los tests reusan la fixture `contexto_turnos` ("Paciente Ficticio 1/2", DNI `"00000001 (ficticio)"` y `"00000002 (ficticio)"`, "Odontólogo Ficticio A", "Odontóloga Ficticia B"). Los tests de dominio usan "Consulta ficticia", "Odontóloga Ficticia B" y "Mantenimiento ficticio". |
| 11 | Cada RN-xx con test | Ver "Cobertura de las RN tocadas"; todas tienen al menos un test explícito. Los tests de `tests/domain/` corren sin base de datos ni HTTP. |
| 12 | `snake_case` y type hints | Las funciones públicas nuevas (`reprogramar_turno`, `post_reprogramar_turno`, `validar_reprogramacion`) y los helpers privados `_exigir_*` están tipados. El helper de tests `_reprogramar` no declara tipo de retorno (lleva `# type: ignore[no-untyped-def]`, igual que `reservar` en `tests/api/test_turnos.py`); no es una función pública de `app/`. No hay linter ni `mypy` instalado en el entorno, así que el chequeo fue manual. |
| 13 | Sin commit ni push sin pedido | Los cuatro commits de C-13 (`91763bf`, `59bfd96`, `e685049`, `22f8535`) los hizo el usuario, por grupos, a su nombre (Joaquin Moran), en español y sin línea de coautoría (`git log` sin "Co-Authored-By"). El apply no hizo commits, ni `git add`. |
| 14 | No tocar `knowledge-base/`, `CHANGES.md`, `docs/discovery/` | `git diff 3789d8d HEAD -- knowledge-base CHANGES.md docs .active-orchestrator-state.json` está vacío: los cambios de C-13 se limitan a `app/`, `tests/` y `openspec/changes/c-13-reprogramar-turno/`. |

- **Orden de rechazo (spec).** Estado del turno (409), recursos nuevos (422) y agenda (409) se verifican en dominio (`test_turno_cancelado_con_nuevo_sillon_inactivo_...`, `test_recurso_nuevo_inactivo_con_conflicto_...`) y por API (`test_reprogramar_recurso_nuevo_inactivo_con_conflicto_responde_422_antes_que_409`).
- **Concurrencia (tarea 3.6).** `test_dos_reprogramaciones_concurrentes_al_mismo_hueco_una_200_y_la_otra_409` lanza dos requests reales sobre dos conexiones a la misma base. Detiene a A dentro de su transacción con un `Event`, comprueba con una tercera conexión (`busy_timeout` de 50 ms) que A conserva el lock, lanza B y espera a que su conexión ejecute `BEGIN IMMEDIATE` (`set_trace_callback`) antes de dejar que A confirme. Resultado: A 200, B 409 `conflicto_agenda`, una sola auditoría `reprogramar`. Sin `sleep`; los `Event` tienen un tope de 10 s solo para no colgar la suite. Se ejecutó 15 veces seguidas sin fallar. Mutación: validar antes de abrir `with transaccion(conexion):` hace fallar solo este test (`assert 200 == 409`: ambas solicitudes se aplicaron).
- **Reloj.** `test_reprogramar_turno_futuro_en_hora_local_aunque_en_utc_ya_pasaria_200` falla si el router usara el instante UTC (lunes 11:00Z es 08:00 local, y el turno es de las 10:00); `test_reprogramar_turno_pasado_en_hora_local_409` cubre el caso contrario.
- **Suite completa.** `701 passed`. `git status` no muestra archivos generados por la suite.

## Observaciones del apply

### Tests sin RED propio

Debajo de cada tarea de `tasks.md` quedó el detalle, con la mutación que prueba que pueden fallar. Las mutaciones se restauraron editando el archivo.

| Tarea | Tests | Motivo y mutación |
|---|---|---|
| 1.3 | `test_solo_cambio_de_horario_sin_enviar_recursos_no_revalida_nada` y los ya existentes del grupo 1 | Verifican comportamiento ya cubierto por el GREEN de 1.4. |
| 1.5 | Los 6 tests nuevos de sillón y paciente | Las reglas ya estaban en `validar_alta` (C-10). Mutaciones: desactivar el conflicto por sillón, el conflicto por paciente y los bloqueos de sillón hace fallar los tests correspondientes. |
| 2.1 | `test_reprogramar_turno_con_usuario_inexistente_revierte_el_cambio`, `test_reprogramar_turno_si_falla_la_auditoria_revierte_tambien_el_update` | `transaccion()` (C-01) ya hacía rollback. Mutación: `conexion.commit()` antes de auditar hace fallar ambos. |
| 3.1 | `test_reprogramar_turno_inexistente_404_no_encontrado` | Pasó con la ruta inexistente por la razón equivocada. Mutación: quitar el `HTTPException(404)` lo hace fallar. |
| 3.1 (refuerzo) | Los dos tests de 422 por recurso nuevo inactivo | Ahora exigen el mensaje "…está inactivo.". Mutación: no cargar los recursos nuevos (siempre `None`, mensaje "no existe") hace fallar los dos, más `..._los_persiste_200` y `..._valida_el_horario_de_ese_profesional` (4 fallos). |
| 3.5 | `test_reprogramar_como_administracion_a_un_hueco_ocupado_409_conflicto_agenda` | Pasó en el primer intento: la regla vive en `validar_alta` y no depende del rol. Mutación: pasar `[]` como turnos activos hace fallar 3 tests (este, `test_reprogramar_sobre_otro_turno_del_profesional_409_conflicto_agenda` y el de concurrencia). |
| 3.6 | `test_dos_reprogramaciones_concurrentes_al_mismo_hueco_una_200_y_la_otra_409` | Pasó en el primer intento: `transaccion()` ya usaba `BEGIN IMMEDIATE` y el router ya leía el contexto dentro de ella. Mutación: validar fuera de la transacción hace fallar solo este test (1 failed, 28 passed en el archivo). |

### Adiciones fuera de las tareas

1. **Guarda de ids en `reprogramar_turno`:** lanza `ValueError` si el turno anterior no tiene id o si el nuevo tiene otro. Test: `test_reprogramar_turno_con_id_distinto_o_sin_id_lanza_value_error_y_no_escribe`. El usuario decidió mantenerla y se documentó en `design.md`.
2. **`Path(ge=1)` en `turno_id`** del endpoint, igual que `GET /turnos/{id}`. Un id 0 o negativo da 422 en lugar de 404; no hay un test propio para ese caso (ver gap 2).
3. **`RuntimeError` en el router** si el turno referencia una prestación inexistente. Es una invariante garantizada por la clave foránea, por lo que no hay test que la alcance (ver gap 3).
4. **Seis tests extra del API** que ninguna tarea listaba: `test_reprogramar_odontologo_sobre_turno_inexistente_responde_403_antes_que_404`, `test_reprogramar_sin_nuevo_inicio_422_en_el_campo`, `test_reprogramar_contiguo_a_otro_turno_200`, `test_reprogramar_turno_cancelado_409_turno_no_modificable`, `test_reprogramar_a_otro_profesional_valida_el_horario_de_ese_profesional` y `test_reprogramar_con_sillon_vigente_inactivo_que_no_se_envia_200`.
5. **Refuerzo de los mensajes 422** (también los de "no existe") en los tests de recurso nuevo, pedido después del grupo 3. Sin cambios en código de producción.

### Gaps

1. **`Path(ge=1)` sin test.** El comportamiento de id 0 o negativo (422) no está verificado.
2. **El `RuntimeError` de prestación inexistente** no tiene test: no se puede alcanzar con las claves foráneas activas de la base.
3. **Escenario "turno pasado" en el API:** el API cubre solo un turno ya pasado (10:30 local sobre un turno de las 10:00); el caso "en curso" exacto está cubierto solo en el dominio (`test_reprogramar_turno_en_curso_instante_exacto_...`).
4. **Límite del test de concurrencia (3.6):** el aviso de B se emite cuando su conexión empieza `BEGIN IMMEDIATE`; si A confirmara antes de que B llegue a esperar, el resultado sería el mismo y el test pasaría igual. Lo que garantiza es que B lee el contexto después de ese aviso y que A sigue sin confirmar hasta entonces; por eso detecta la validación fuera de la transacción, pero no mide cuánto esperó B.
5. **Sin linter ni `mypy`** en el entorno; los type hints se revisaron a mano.

Ningún escenario del spec quedó sin test. Ninguna regla dura se rompe en el diff. Los gaps de RN-TUR-11 y de concurrencia reales de la versión anterior de este informe quedaron cerrados con las tareas 3.5 y 3.6.
