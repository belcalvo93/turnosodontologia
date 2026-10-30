# Tasks — C-17 seed-y-flujo-e2e

## 1. Configuración de las contraseñas demo

- [x] 1.1 Escribir en `tests/api/test_config.py` los casos de las variables nuevas y verificar que **fallan antes de implementar**: sin `SEED_RECEPCION_PASSWORD` ni `SEED_ODONTOLOGO_PASSWORD` los campos quedan en `None`, con ambas definidas toman su valor, y `SEED_ADMIN_PASSWORD` sigue funcionando igual
- [x] 1.2 Agregar `seed_recepcion_password` y `seed_odontologo_password` a `Config` y a `cargar_config` (patrón `valores.get("…") or None`) y verificar que 1.1 pasa

## 2. Test de aceptación del flujo E2E (primero en rojo)

- [x] 2.1 Escribir `tests/api/test_flujo_e2e.py`: fixture que arranca `create_app` con `APP_ENV=development`, las tres contraseñas, `CLINIC_TIMEZONE` fija y `RelojFijo`, y lee de la base los ids demo; el test principal recorre los 6 pasos del roadmap (login recepción → `POST /turnos` → reprogramar → cancelar → login administración → `GET /auditoria`) y verificar que **falla**: el login de recepción responde `401` porque `recepcion_demo` todavía no existe
- [x] 2.2 Agregar al mismo archivo los bordes del flujo y verificar que siguen en rojo por la misma razón: el hueco liberado por la cancelación se puede volver a reservar con el mismo profesional y sillón, y un `409` de reprogramación a un horario ocupado no agrega registros de auditoría (RN-AUD-03)

## 3. Seed demo y arranque

- [x] 3.1 Escribir `tests/api/test_seed_demo.py` y verificar que **falla por ausencia de `sembrar_demo`**: catálogo completo (2 profesionales con matrícula terminada en `"(ficticia)"`, 2 sillones, 3 prestaciones con duraciones 30, 45 y 60 minutos, 2 pacientes: uno con obra social y otro sin obra social, donde se consultan con una consulta directa a la base), 20 horarios (lunes a viernes, 09:00-13:00 y 14:00-18:00, para ambos profesionales, donde se consultan con una consulta directa a la base), `odontologo_demo` ligado al profesional A y los otros dos sin `profesional_id`, ningún usuario demo sin su contraseña, `password_hash` con prefijo `$argon2id$`, el test "un usuario demo existente no se modifica", y los datos ficticios rotulados (DNI terminado en `"(ficticio)"`, nombres con "ficticio/ficticia" sin distinguir mayúsculas, donde se consultan con una consulta directa a la base)
- [x] 3.2 Implementar en `app/db/seed.py` las funciones por grupo y `sembrar_demo(...) -> DatosDemo` con `ON CONFLICT DO NOTHING` donde hay `UNIQUE` e `INSERT … SELECT … WHERE NOT EXISTS` en `profesional` y `horario_atencion`, todo en un único `transaccion()`; verificar que 3.1 pasa y que los 6 tests de unidad de `sembrar_admin_demo` siguen verdes
- [x] 3.3 Escribir los tests del arranque y verificar que **fallan**: con las tres contraseñas se crean los 3 usuarios y el catálogo, dos arranques dejan exactamente 32 filas y los mismos hashes, en `test`/`production` no se siembra nada, sin `SEED_ADMIN_PASSWORD` no se siembra nada, y solo con `SEED_ADMIN_PASSWORD` no aparece `odontologo_demo`
- [x] 3.4 Cablear el `lifespan` de `app/main.py` para calcular los hashes de las variables definidas y llamar a `sembrar_demo`, y verificar que 3.3 y los tests del grupo 2 quedan en verde y que `tests/api/test_seed.py` sigue en verde sin modificarlo

## 4. Cierre de los dos huecos de reglas

- [x] 4.1 `RN-REC-03`: agregar en `tests/api/test_turnos.py` los casos de caracterización de "los turnos históricos se conservan" citando los escenarios del delta `specs/turnos/spec.md` ("Sillón desactivado después de la reserva", "Profesional desactivado después de la reserva" y "La desactivación no borra auditoría") — desactivar el sillón o el profesional de un turno reservado y verificar que `GET /turnos/{id}` sigue devolviéndolo con el recurso desactivado y estado `reservado`, que la desactivación no borra la auditoría y que un turno nuevo sobre el recurso desactivado responde `422`. Es caracterización: si pasa sin tocar código, el comportamiento ya era correcto y queda blindado; documentarlo en la tarea
- [x] 4.2 Revisar que todos los datos de los tests nuevos (pacientes, profesionales, sillones, prestaciones y contraseñas) son ficticios y están rotulados: ningún DNI sin `"(ficticio)"`, ninguna contraseña literal fuera de las variables de entorno de la fixture; corregir lo que aparezca

## 5. Trazabilidad RN → test

- [x] 5.1 Escribir los tests en `tests/test_trazabilidad.py` importando los helpers desde `tests/trazabilidad.py` (`codigos_de_reglas`, `filas_de_tabla`, `tests_existentes` con `ast`, `hallazgos`) con los cuatro casos: el repositorio real no tiene hallazgos, una regla sin fila falla nombrando el código, un test citado inexistente falla nombrando el nodo, y una tabla completa no reporta nada; verificar que **falla antes de implementar** porque el módulo de helpers no existe (y tampoco el documento)
- [x] 5.2 Implementar los helpers en `tests/trazabilidad.py` y crear `docs/trazabilidad-rn-test.md` con las 31 reglas de KB 05 mapeadas a su nodo de test exacto; verificar que 5.1 pasa y que el documento coincide con lo relevado en `explore.md` §3

## 6. README y `.env.example`

- [x] 6.1 Agregar `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD` a `.env.example` como placeholders, con la misma advertencia de no versionar valores reales
- [x] 6.2 Actualizar el README: estado real (17 changes y el conteo real de la suite), eliminar la frase "todavía no hay rutas protegidas", documentar los 3 usuarios demo, agregar el flujo E2E de 6 pasos con ejemplos que coincidan con las respuestas reales del test, la dependencia de `CLINIC_TIMEZONE`, que no hace falta borrar `turnos.db`, el link a `docs/trazabilidad-rn-test.md` y la estructura de archivos al día
- [x] 6.3 Verificar que cada ejemplo del README coincide con una respuesta real del test E2E (mismos campos, estados y códigos HTTP) y que el conteo de tests publicado es el de la suite completa

## 7. Verificación

- [x] 7.1 Correr la suite completa (`.venv\Scripts\python.exe -m pytest -q`) y verificar 0 fallos y que el total sea 759 más los tests nuevos
- [x] 7.2 Correr `openspec validate c-17-seed-y-flujo-e2e --strict` y verificar que no reporta errores ni warnings
- [x] 7.3 Verificar con `git diff --stat` que no se modificaron `app/db/esquema.sql` ni ningún archivo de `app/api/`, `knowledge-base/`, `CHANGES.md` ni `docs/discovery/`
- [x] 7.4 Escribir `verify.md` con el resultado de la suite, la tabla escenario → test de los 8 requirements del delta (6 de acceso-usuarios, 1 de base-tecnica y 1 de turnos), el conteo de filas del seed y la confirmación de archivos protegidos

## Workflow follow-up

- Correr la verificación del proyecto y dejar el resultado registrado (no se archiva con tests en rojo).
- Archivar con `/opsx:archive c-17-seed-y-flujo-e2e` cuando la revisión esté aprobada.
- Marcar `[C-17]` en `CHANGES.md` solo si el usuario lo pide (regla dura 14).
- No hacer commit ni push sin pedido explícito del usuario (regla dura 13).
- El saneamiento documental (`agenda`, `horarios-atencion`, `AccionAuditoria`) va en un PR aparte, **después** del archive: no es tarea de este change.
