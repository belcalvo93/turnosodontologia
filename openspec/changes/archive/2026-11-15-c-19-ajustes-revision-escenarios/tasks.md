# Tasks — C-19 ajustes-revision-escenarios

> Todos los tests nuevos son de **caracterización** (design D-A): se escriben, se corren (pasan), se demuestra el rojo con una mutación temporal mínima, se revierte con `git checkout -- <archivo>` y se confirma que el test vuelve a verde y que el archivo mutado no aparece en `git diff --stat`. Si un test nuevo falla **sin** mutación, es un bug real: parar y reportar al equipo (no se toca `app/`).

## 0. Red de seguridad

- [x] 0.1 Correr la suite **completa** con `python -m pytest -q` y registrar el total de la línea de base ("N passed", 0 fallos; se espera 789 passed). Si el total difiere de 789, registrar el valor real y usarlo en 5.1; si algo falla, parar y reportarlo como falla preexistente

## 1. Trazabilidad: RN-TUR-13 con test distinto (H4, `base-tecnica`)

- [x] 1.1 Agregar en `tests/test_trazabilidad.py` el test `test_rn_tur_13_con_un_test_distinto_del_de_rn_tur_04_falla_nombrando_rn_tur_13` (docstring con el escenario "RN-TUR-13 con un test distinto del de RN-TUR-04 hace fallar la verificación"): KB sintética con `RN-TUR-04` y `RN-TUR-13`, tabla con dos nodos distintos y ambos en `existentes` (design D-B); afirmar `len(problemas) == 1` y `"RN-TUR-13" in problemas[0]`. Correrlo y verificar que pasa
- [x] 1.2 Rojo por mutación: comentar temporalmente el bloque `if "RN-TUR-13" in filas and "RN-TUR-04" in filas:` de `tests/trazabilidad.py` (~`:124-128`), correr el test de 1.1 y verificar que **falla** en `len(problemas) == 1`; revertir con `git checkout -- tests/trazabilidad.py`, verificar que `tests/test_trazabilidad.py` queda 6/6 en verde y que `git diff --stat tests/trazabilidad.py` está vacío

## 2. Seed con una sola contraseña de rol (H9, `acceso-usuarios`)

- [x] 2.1 Agregar en `tests/api/test_seed_demo.py` los tests de unidad sobre `sembrar_demo` (design D-C): `test_sembrar_demo_solo_con_hash_de_odontologo_crea_solo_odontologo_demo` (`password_hash_recepcion=None`: usernames `["admin_demo", "odontologo_demo"]`, `odontologo_demo` con rol `odontologo`, activo y `profesional_id == datos.profesional_a`, `datos.recepcion_demo is None`) y `test_sembrar_demo_solo_con_hash_de_recepcion_crea_solo_recepcion_demo` (`password_hash_odontologo=None`: usernames `["admin_demo", "recepcion_demo"]`, rol `recepcion`, `profesional_id` nulo, `datos.odontologo_demo is None`). Correrlos y verificar que pasan
- [x] 2.2 Agregar los tests de arranque con `create_app`, reutilizando `_config_arranque_demo` y `_conteos_por_tabla`: `test_arranque_solo_con_contrasena_de_odontologo_crea_solo_odontologo_demo` y `test_arranque_solo_con_contrasena_de_recepcion_crea_solo_recepcion_demo` (docstrings con los escenarios "Solo la contraseña de odontología crea solo odontologo_demo" y "Solo la contraseña de recepción crea solo recepcion_demo"): usernames exactos, catálogo sembrado (2/2/3/20/2 y `usuario` = 2) y `POST /auth/login` `200` con el usuario creado. Usar solo las contraseñas ficticias de la fixture `entorno_tres_claves_demo`. Correrlos y verificar que pasan
- [x] 2.3 Rojo por mutación: en `app/db/seed.py` (`_sembrar_usuarios`, ~`:243-281`) hacer temporalmente que el usuario ausente se cree igual con `password_hash_admin` (por ejemplo `password_hash_recepcion or password_hash_admin` y quitar el `None if …`); correr los 4 tests de 2.1 y 2.2 y verificar que **fallan** porque aparece el usuario que no debía existir. Repetir con la mutación simétrica para `odontologo_demo`. Revertir con `git checkout -- app/db/seed.py`, verificar que `tests/api/test_seed_demo.py` queda todo en verde y que `git diff --stat app/` está vacío

## 3. Recurso desactivado: auditoría del profesional (H10, `turnos`)

- [x] 3.1 Confirmar (sin cambios) que `test_profesional_desactivado_despues_de_la_reserva_conserva_el_turno_y_rechaza_nuevos_422` sigue afirmando `estado == "reservado"` (design D-F) y que su docstring cita el escenario "Profesional desactivado después de la reserva"; no se agrega test para ese escenario
- [x] 3.2 Agregar en `tests/api/test_turnos.py`, debajo del test de auditoría del sillón, `test_desactivar_el_profesional_no_borra_ni_modifica_la_auditoria_del_turno` (docstring con el escenario "La desactivación del profesional no borra auditoría" y RN-REC-03): reservar, tomar `_auditorias(ctx)`, `PATCH /profesionales/{ctx.profesional_a}` con `activo = false` (`200`), verificar `_auditorias(ctx)` igual a la previa y `GET /auditoria?turno_id=…` `200` con un único registro de acción `crear`. Correrlo y verificar que pasa
- [x] 3.3 Rojo por mutación: en `app/db/repositorio_profesionales.py` (`actualizar_profesional`, ~`:69`) agregar temporalmente un `INSERT` de una fila extra en `auditoria_turno` para el turno existente (solo INSERT, nunca UPDATE ni DELETE: regla dura 6); correr el test de 3.2 y verificar que **falla** en la comparación de `_auditorias`. Revertir con `git checkout -- app/db/repositorio_profesionales.py`, verificar verde y `git diff --stat app/` vacío

## 4. Puntos solo de spec (H5, H7, H8)

- [x] 4.1 H5: verificar que `test_sembrar_demo_crea_catalogo_completo_con_duraciones_matriculas_y_obra_social` afirma `"(ficticia)"` en **ambas** matrículas, coherente con el escenario corregido "Catálogo completo al arrancar"; sin cambios de código ni de tests
- [x] 4.2 H7: verificar que el paso 2 de `tests/api/test_flujo_e2e.py` reserva `LUNES_DEMO` a las 10:00 con `RelojFijo` en lunes 09:00 local y `CLINIC_TIMEZONE` fija, y que el alta incluye `sillon_id` (`ids.sillon_1`, "Sillón 1", RN-TUR-02) y responde `201` con el turno completo: `sillon_id`, `inicio` a las 10:00, `fin` 10:30 y `estado` `reservado`. Verificar además que los pasos 3 (reprogramar) y 4 (cancelar) del mismo test se ejecutan con éxito sobre ese turno, lo que respalda que el turno futuro "admite cancelación o reprogramación" (RN-TUR-09). Coherente con el escenario corregido "Los recursos sembrados aceptan turnos"; sin cambios
- [x] 4.3 H8: verificar que `test_datos_ficticios_rotulados_en_pacientes_y_profesionales` evalúa `f"{nombre} {apellido}".lower()`, coherente con el escenario corregido "Los nombres demo están rotulados"; sin cambios

## 5. Verificación final

- [x] 5.1 Correr la suite completa `python -m pytest -q` y verificar 0 fallos y total = línea de base registrada en 0.1 + 6 tests nuevos (1 de trazabilidad, 4 de seed, 1 de turnos): 795 passed si la base es 789
- [x] 5.2 Correr `openspec validate c-19-ajustes-revision-escenarios --strict` y verificar que es válido sin errores ni warnings
- [x] 5.3 Esta verificación corre **antes** de agregar la fila de C-19 en `CHANGES.md` (esa fila se agrega después, en el cierre). Verificar con `git status` y `git --no-pager diff --stat` que solo cambian `tests/test_trazabilidad.py`, `tests/api/test_seed_demo.py`, `tests/api/test_turnos.py` y `openspec/changes/c-19-ajustes-revision-escenarios/`, y que **no** aparece ningún archivo de `app/`, `frontend/`, `knowledge-base/`, `docs/`, `openspec/specs/`, `openspec/changes/archive/` ni `tests/trazabilidad.py`
- [x] 5.4 Escribir `verify.md` con el resultado de la suite, la tabla escenario → test de los escenarios nuevos o modificados (con su RN-xx cuando corresponde), la evidencia de cada mutación (falló / revertida) y la confirmación de archivos protegidos

## Workflow follow-up

- No hacer commit ni push sin pedido explícito del equipo (regla dura 13); mensajes en español, sin línea de coautoría de IA.
- Correr `revisor-escenarios-sdd` sobre este change antes del apply, si el equipo lo pide.
- Archivar con `/opsx:archive c-19-ajustes-revision-escenarios` cuando la verificación esté en verde: el archive aplica los deltas a `openspec/specs/` (la única vía para cambiar los specs canónicos).
- Al cierre, agregar la fila de `C-19` en `CHANGES.md` y marcarla `[x]` (autorizado por el equipo para este cierre; fuera de eso, regla dura 14), una vez cumplida la verificación 5.3.