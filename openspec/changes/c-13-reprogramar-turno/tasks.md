# Tasks — C-13 reprogramar-turno

## 0. Baseline

- [x] 0.1 Baseline: 625 tests en main.

## 1. Dominio Puro (`app/domain/reglas_turno.py`)

- [x] 1.1 Escribir tests de dominio para `validar_reprogramacion` en `tests/domain/test_reprogramar_turno.py` (hecha por Hernán antes del apply):
  - [x] Test: turno pasado o en curso (`inicio <= ahora`) lanza `TurnoNoModificable` (RN-TUR-09).
  - [x] Test: turno cancelado lanza `TurnoNoModificable` (RN-TUR-10).
  - [x] Test: mover turno sobre su propio intervalo previo (ej. de 10:00-10:30 a 10:15-10:45) es aceptado (RN-TUR-08).
  - [x] Test: nuevo horario solapa con otro turno activo del mismo profesional lanza `ConflictoAgenda` (RN-TUR-03, RN-TUR-07). El caso de sillón pasa a la tarea 1.5.
  - [x] Test: nuevo horario fuera de franja de atención lanza `FueraDeHorario` (RN-PRO-01).
  - [x] Test: nuevo horario coincide con bloqueo de profesional lanza `DentroDeBloqueo` (RN-TUR-05). El caso de sillón pasa a la tarea 1.5.
  - [x] Test: cambio exitoso con reasignación de nuevo profesional y nuevo sillón devuelve el `Turno` actualizado con mismo `id` (D-05).
- [x] 1.2 Implementar la función `validar_reprogramacion(...)` en `app/domain/reglas_turno.py` haciendo pasar todos los tests de dominio en verde (hecha por Hernán antes del apply).
- [ ] 1.3 Escribir tests de recursos nuevos y orden de validación en `tests/domain/test_reprogramar_turno.py`:
  - [ ] Test: turno cancelado con `nuevo_sillon_id` inactivo lanza `TurnoNoModificable` (409), no `DatoInvalido`.
  - [ ] Test: turno pasado con `nuevo_profesional_id` inexistente lanza `TurnoNoModificable` (409).
  - [ ] Test: `nuevo_profesional_id` o `nuevo_sillon_id` inexistente o inactivo lanza `DatoInvalido` (422).
  - [ ] Test: recurso nuevo inactivo en un horario con conflicto lanza `DatoInvalido`, no `ConflictoAgenda`.
  - [ ] Test: recurso vigente inactivo que no se envía no impide reprogramar.
- [ ] 1.4 Agregar `nuevo_profesional` y `nuevo_sillon` a `validar_reprogramacion` y validar solo los recursos enviados, después del estado y antes de la agenda, extrayendo helpers privados de `validar_recursos_alta` sin cambiar su comportamiento. Actualizar `test_reprogramar_cambiando_profesional_y_sillon_exitoso`, que hoy envía los ids sin los recursos.
- [ ] 1.5 Cubrir en `tests/domain/test_reprogramar_turno.py` los casos que faltan en la reprogramación:
  - [ ] Test: nuevo horario solapa con otro turno activo del mismo sillón, con otro profesional, lanza `ConflictoAgenda` (RN-TUR-03, RN-TUR-07).
  - [ ] Test: nuevo horario coincide con bloqueo del sillón lanza `DentroDeBloqueo` (RN-TUR-05).
  - [ ] Test: nuevo horario solapa con otro turno activo del mismo paciente, con otro profesional y sillón, lanza `ConflictoAgenda` (RN-TUR-03, RN-TUR-12).

## 2. Persistencia y Transaccionalidad (`app/db/`)

- [ ] 2.1 Escribir tests unitarios/integración para la persistencia de reprogramación en el repositorio de turnos (`tests/api/test_repositorio_turnos.py`):
  - [ ] Test: reprogramación exitosa actualiza campos en tabla `turno` e inserta fila en `auditoria_turno` con `accion = 'reprogramar'` y `antes`/`despues` con `snapshot_turno` completo, incluido `estado` (RN-AUD-01, C-11 D2).
  - [ ] Test: si ocurre un fallo o excepción, la transacción revierte y no se inserta auditoría (RN-AUD-03).
- [ ] 2.2 Implementar en el repositorio la función `reprogramar_turno(...)` (`UPDATE` + `registrar_auditoria(accion="reprogramar")`), con la precondición de ejecutarse dentro de la transacción del router (C-11 D1).

## 3. Capa API y Endpoint (`app/api/turnos.py`)

- [ ] 3.1 Escribir tests de integración API para `POST /turnos/{id}/reprogramar` en `tests/api/test_reprogramar_turno.py`:
  - [ ] Test: reprogramación exitosa con rol `recepcion` y `administracion` devuelve 200 y el turno actualizado con la forma de `TurnoResponse` (US-008, C-11 D8).
  - [ ] Test: odontólogo intentando reprogramar recibe 403 `SinPermiso` (RN-ACC-02).
  - [ ] Test: solicitud sin token recibe 401 `NoAutenticado` (RN-ACC-01).
  - [ ] Test: turno inexistente devuelve 404 `no_encontrado` (US-008, C-11 D5).
  - [ ] Test: nuevo profesional o nuevo sillón inexistente o inactivo devuelve 422 `DatoInvalido` (C-11 D10).
  - [ ] Test: turno cancelado con `nuevo_sillon_id` inactivo devuelve 409 y no agrega filas en `auditoria_turno`.
  - [ ] Test: `nuevo_inicio` con offset o `Z` devuelve 422 (C-11 D4).
  - [ ] Test: con el reloj inyectado en UTC, un turno futuro se reprograma sin `TypeError` y uno pasado en hora local devuelve 409 (C-11 D3).
  - [ ] Test: conflicto de agenda, bloqueo o fuera de horario devuelve 409 y la cantidad de filas en `auditoria_turno` no cambia (RN-AUD-03).
- [ ] 3.2 Definir el esquema Pydantic `ReprogramarTurnoRequest` con `nuevo_inicio: NaiveDatetime` (C-11 D4).
- [ ] 3.3 Implementar el endpoint `POST /turnos/{id}/reprogramar` con `requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION)` y `obtener_ahora_local`, responder con `TurnoResponse` y usar `obtener_turno` → `HTTPException(404)` (C-11 D3, D5, D8).
- [ ] 3.4 Dentro de `with transaccion(conexion):`, cargar el contexto con `listar_turnos_activos_del_dia` y `listar_bloqueos_de_recursos`, cargar los recursos nuevos enviados y llamar a `validar_reprogramacion` y `reprogramar_turno` (C-11 D1, D8). El router no valida recursos: lo hace el dominio.

## 4. Verificación y Cierre

- [ ] 4.1 Ejecutar suite completa con `pytest` y comprobar que todos los tests pasen en verde.
- [ ] 4.2 Verificar el cumplimiento de las 14 Reglas Duras de `AGENTS.md`.
- [ ] 4.3 Generar informe de verificación `verify.md`.
