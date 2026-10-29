# Tasks — C-11 crear-turno

> **Governance CRÍTICO.** El apply avanza por checkpoints: al terminar cada grupo marcado con **[CHECKPOINT]**, PARAR, mostrar el diff y los tests en verde, y esperar la aprobación del usuario antes de seguir.
>
> **Strict TDD.** Cada tarea se hace en ciclo RED → GREEN → TRIANGULATE → REFACTOR: primero el test que falla (ejecutado y visto en rojo), después el código mínimo, luego un segundo caso con otros datos. Safety net: antes de tocar un archivo existente, correr sus tests y anotar el baseline (en `main`: **524 tests pasando**). Datos siempre ficticios (DNI con sufijo "(ficticio)"). Reloj siempre fijo (`RelojFijo` de `tests/conftest.py`, `INSTANTE_INICIAL = 2026-01-05T12:00Z` = lunes 09:00 local).

## 0. Safety net

- [x] 0.1 Correr `pytest tests` completo en la rama y verificar el baseline de 524 tests en verde; si algo falla, PARAR y reportarlo como falla previa (no arreglarla)

## 1. Dependencia y hora local del consultorio (D3, D4)

- [x] 1.1 Agregar `tzdata` a `requirements.txt`, instalarlo y verificar que `python -c "import zoneinfo; zoneinfo.ZoneInfo('America/Argentina/Buenos_Aires')"` termina sin error
- [x] 1.2 RED: en `tests/api/test_hora_local.py` escribir `test_a_hora_local_convierte_utc_a_buenos_aires_sin_tzinfo` (`2026-01-05T12:00Z` → `2026-01-05T09:00`, `tzinfo is None`) y ejecutarlo en rojo. GREEN: implementar `a_hora_local(instante, zona)` en `app/api/dependencias.py`. TRIANGULATE: `test_a_hora_local_cambia_de_dia_al_convertir` (`2026-01-06T02:30Z` → `2026-01-05T23:30`) y un instante con otra zona de origen; verificar en verde
- [x] 1.3 RED: test de la dependencia `obtener_ahora_local` sobre una ruta de `tests/api/rutas_prueba.py` (nueva ruta `/prueba/ahora-local`) con `RelojFijo`: devuelve `"2026-01-05T09:00:00"` y, tras `reloj.avanzar(minutes=90)`, `"2026-01-05T10:30:00"`. GREEN: implementar `obtener_ahora_local` con `Depends(obtener_ahora)` y `config.clinic_timezone`; verificar que los tests de `test_auth.py` y `test_dependencias.py` siguen en verde (`obtener_ahora` sin cambios)

## 2. Reglas de dominio nuevas (D7, D10) — sin DB ni HTTP

- [x] 2.1 RED: en `tests/domain/test_recursos_alta.py` escribir `test_validar_recursos_alta_con_todo_activo_devuelve_la_prestacion` y ejecutarlo en rojo. GREEN: implementar `validar_recursos_alta(prestacion, profesional, sillon, paciente)` en `app/domain/reglas_turno.py` sin tocar `validar_alta`. TRIANGULATE (RN-REC-03, RN-GLO-01): un test por caso que lanza `DatoInvalido` con mensaje en español — prestación inexistente, prestación inactiva, profesional inexistente, profesional inactivo, sillón inexistente, sillón inactivo, paciente inexistente; verificar que `tests/domain/test_reglas_turno.py` y `test_reprogramar_turno.py` siguen en verde
- [x] 2.2 RED: en `tests/domain/test_permisos_turno.py` escribir `test_puede_ver_turno_odontologo_de_otro_profesional_devuelve_false` y ejecutarlo en rojo. GREEN: implementar `puede_ver_turno(usuario, turno)` en `app/domain/usuarios.py`. TRIANGULATE (RN-ACC-03): odontólogo del mismo profesional → `True`; odontólogo con `profesional_id=None` → `False`; administración y recepción → `True` para cualquier profesional
- [x] 2.3 Verificar que `tests/domain/test_estructura.py` sigue en verde (`app/domain/` no importa FastAPI ni `app.db`/`app.api`, y no llama a `datetime.now()`/`date.today()`) — **[CHECKPOINT 1: grupos 1 y 2]**

## 3. Esquema SQLite (D11)

- [x] 3.1 RED: en `tests/api/test_repositorio_turnos.py` escribir tests de esquema sobre SQLite temporal y ejecutarlos en rojo: `inicializar_esquema` crea `turno`, `auditoria_turno`, los índices `idx_turno_profesional_inicio`, `idx_turno_sillon_inicio`, `idx_turno_paciente_inicio` y los dos triggers, y es idempotente. GREEN: agregar el DDL de design D11 a `app/db/esquema.sql`
- [x] 3.2 TRIANGULATE restricciones: `INSERT` con `inicio >= fin` → `IntegrityError`; `estado = 'confirmado'` → `IntegrityError`; `accion = 'borrar'` → `IntegrityError`; `sillon_id` nulo → `IntegrityError` (RN-TUR-02); `profesional_id` inexistente → error de clave foránea
- [x] 3.3 RN-AUD-02: tests de que `UPDATE` y `DELETE` sobre un registro de `auditoria_turno` lanzan `sqlite3.IntegrityError` y el registro queda igual; verificar en verde

## 4. Repositorios (D2, D4, D8)

- [x] 4.1 RED: test de `turno_desde_fila` + `obtener_turno` (fila insertada → `Turno` con `datetime` naive; id inexistente → `None`). GREEN: crear `app/db/repositorio_turnos.py` con `COLUMNAS_TURNO`, `turno_desde_fila` y `obtener_turno` (SQL parametrizado, regla dura 4)
- [x] 4.2 RED: test de `snapshot_turno`: JSON con exactamente las 8 claves de D2, en orden, fechas `YYYY-MM-DDTHH:MM:SS`. GREEN: implementar. TRIANGULATE: turno `cancelado` con otros ids y horario de tarde
- [x] 4.3 RED: test de `crear_turno` dentro de `transaccion`: devuelve el `Turno` con `id`; la fila guarda `creado_por` y `creado_en` (`isoformat` segundos, sin offset); hay un único registro `auditoria_turno` con `accion='crear'`, `usuario_id`, `ocurrio_en == creado_en`, `antes IS NULL` y `despues == snapshot_turno(turno_creado)` (RN-AUD-01). GREEN: implementar `registrar_auditoria` y `crear_turno`. TRIANGULATE: dos altas seguidas → ids y auditorías distintas
- [x] 4.4 RN-AUD-03: test de atomicidad — dentro de `transaccion`, `crear_turno` con un `creado_por` inexistente (falla la FK de la auditoría o del turno) → la excepción se propaga y al reabrir la base no hay ni turno ni auditoría
- [x] 4.5 RED: tests de `listar_turnos_activos_del_dia`: devuelve los `reservado` del día que comparten profesional, sillón **o** paciente; excluye `cancelado`, otro día y turnos sin recurso compartido. GREEN: implementar con la ventana `[dia, dia+1)`
- [x] 4.6 Safety net de `tests/api/test_repositorio_bloqueos.py`; RED: tests de `listar_bloqueos_de_recursos` — incluye bloqueo del profesional y del sillón que intersectan la ventana, incluye un bloqueo de varios días que la cubre, excluye bloqueos de otro recurso, de otro alcance con el mismo id y contiguos a la ventana (semiabierto). GREEN: implementar en `app/db/repositorio_bloqueos.py` — **[CHECKPOINT 2: grupos 3 y 4]**

## 5. Router de turnos — POST /turnos (D1, D4, D7)

> Tests en `tests/api/test_turnos.py` con `TestClient` y base temporal. Fixture local `contexto_turnos`: profesionales "Odontólogo Ficticio A" y "Odontóloga Ficticia B" con horario lunes 09:00-13:00, "Sillón 1" y "Sillón 2", prestaciones "Consulta ficticia" (30) y "Limpieza ficticia" (45), pacientes "Paciente Ficticio 1" (DNI "00000001 (ficticio)") y "Paciente Ficticio 2" (DNI "00000002 (ficticio)"), y usuarios `admin_ficticio`, `recepcion_ficticia`, `odontologo_a_ficticio` (profesional A). Fecha de los turnos: lunes `2026-01-12`.

- [ ] 5.1 RED: `test_post_turnos_recepcion_crea_turno_reservado_201` (RN-TUR-14, RN-TUR-01: `fin` 10:30, `estado` `reservado`) en rojo. GREEN: crear `app/api/turnos.py` con `CrearTurnoRequest` (`inicio: NaiveDatetime`), `TurnoResponse`, `turno_a_response` y `POST /turnos` según el flujo de design D1, y montar el router en `app/main.py`. TRIANGULATE: "Limpieza ficticia" → `fin` 10:45; administración también crea (`201`); `GET` posterior devuelve lo mismo (cuando exista 6.1, si no con lectura directa de la base)
- [ ] 5.2 RN-TUR-03/04/08/12: tests `409 conflicto_agenda` por profesional, por sillón y por paciente; contiguos antes y después → `201`; superposición de un minuto (10:29) → `409`; turno `cancelado` insertado por SQL en el mismo hueco → `201`
- [ ] 5.3 RN-TUR-05, RN-GLO-01: tests `409 fuera_de_horario` (12:45 cruza el fin de franja; martes sin horario) y `409 dentro_de_bloqueo` (bloqueo de sillón 10:00-12:00: sillón 1 a las 11:00 → `409`, sillón 2 a las 11:00 → `201`, sillón 1 a las 12:00 → `201`; bloqueo de profesional todo el día → `409`)
- [ ] 5.4 RN-TUR-02, RN-REC-03, D4: tests `422 dato_invalido` — sin `sillon_id` (`detalles[campo=sillon_id]`), sillón inactivo, profesional inactivo, prestación inactiva, recurso inexistente (cada uno de los cuatro ids), `inicio` con `-03:00` y con `Z` (`detalles[campo=inicio]`); en todos, verificar por SQL que no quedó turno ni auditoría
- [ ] 5.5 SE-06, RN-TUR-11: test de doble reserva — dos recepcionistas reservan el mismo hueco en secuencia: `201` y luego `409 conflicto_agenda`; por SQL queda un turno y una auditoría; administración tampoco puede superponer (`409`)
- [ ] 5.6 RN-ACC-01/02: tests — odontólogo creando un turno de su propio profesional → `403 sin_permiso` sin turno ni auditoría; sin token → `401 no_autenticado`
- [ ] 5.7 RN-AUD-01/03 a nivel API: con el reloj en `2026-01-05T12:00Z`, tras `POST /turnos` la auditoría tiene `accion='crear'`, `usuario_id` del recepcionista, `ocurrio_en = "2026-01-05T09:00:00"`, `antes` nulo y `despues` con las 8 claves y los valores del turno; el turno tiene `creado_por` y `creado_en` iguales. TRIANGULATE: reloj en `2026-01-06T02:30Z` → `"2026-01-05T23:30:00"`. Tras un `409`, la cantidad de turnos y auditorías no cambia — **[CHECKPOINT 3: grupo 5]**

## 6. Router de turnos — GET /turnos/{id} (D5, D7)

- [ ] 6.1 RED: `test_get_turno_recepcion_existente_200` en rojo. GREEN: implementar `GET /turnos/{id}` con `usuario_actual`, `obtener_turno` (`None` → `HTTPException(404)`) y `puede_ver_turno` (`False` → `SinPermiso`). TRIANGULATE: administración `200` sobre turno de la profesional B; id inexistente `9999` → `404 no_encontrado`; sin token → `401`
- [ ] 6.2 RN-ACC-03: odontólogo A ve su turno (`200`); odontólogo A pide un turno de la profesional B → `403 sin_permiso` y el cuerpo no contiene datos del turno
- [ ] 6.3 RN-AUD-02 a nivel API: `PUT`, `PATCH` y `DELETE` sobre `/turnos/{id}` y sobre una ruta de auditoría (`/auditoria/turnos/1`) responden `404` o `405` y la auditoría no cambia
- [ ] 6.4 REFACTOR del router y del repositorio con la suite de `tests/api/test_turnos.py` en verde tras cada paso: sin reglas de negocio en el router (regla dura 8), type hints y `snake_case` en funciones públicas (regla dura 12), `Annotated` en dependencias — **[CHECKPOINT 4: grupo 6]**

## 7. Verificación integral

- [ ] 7.1 Ejecutar `pytest tests` completo y verificar todo en verde: 524 del baseline + los nuevos, sin tests salteados
- [ ] 7.2 Verificar la trazabilidad: cada regla RN-TUR-01, 02, 03, 04, 05, 08, 11, 12, 14, RN-REC-03, RN-ACC-01, 02, 03, RN-AUD-01, 02, 03 y RN-GLO-01 tiene al menos un test nombrado en las tareas 1–6 (listar el mapeo en el resumen del apply)
- [ ] 7.3 Verificar reglas duras con búsquedas: `app/domain/` sin `fastapi`, `app.db`, `app.api`, `datetime.now`, `date.today`; `app/db/repositorio_turnos.py` y `repositorio_bloqueos.py` sin f-strings ni `%`/`+` en SQL; ningún `UPDATE`/`DELETE` sobre `auditoria_turno` en `app/`
- [ ] 7.4 Ejecutar `openspec validate c-11-crear-turno --strict` y verificar que no reporta errores

## Workflow follow-up

- Pasar a los autores de `C-12`, `C-13` y `C-14` la sección "Ajustes para C-12/C-13/C-14" del design antes de su `/opsx:apply`.
- Commit y push solo cuando el usuario lo pida (regla dura 13), con mensajes en español a nombre del integrante y sin línea de coautoría de IA.
- Archivar con `/opsx:archive c-11-crear-turno` y marcar `C-11` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
