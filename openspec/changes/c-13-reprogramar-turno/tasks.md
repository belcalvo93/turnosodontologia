# Tasks — C-13 reprogramar-turno

## 1. Dominio Puro (`app/domain/reglas_turno.py`)

- [ ] 1.1 Escribir tests de dominio para `validar_reprogramacion` en `tests/domain/test_reglas_turno.py`:
  - [ ] Test: turno pasado o en curso (`inicio <= ahora`) lanza `TurnoNoModificable` (RN-TUR-09).
  - [ ] Test: turno cancelado lanza `TurnoNoModificable` (RN-TUR-10).
  - [ ] Test: mover turno sobre su propio intervalo previo (ej. de 10:00-10:30 a 10:15-10:45) es aceptado (RN-TUR-08).
  - [ ] Test: nuevo horario solapa con otro turno activo del mismo profesional o sillón lanza `ConflictoAgenda` (RN-TUR-03, RN-TUR-07).
  - [ ] Test: nuevo horario fuera de franja de atención lanza `FueraDeHorario` (RN-PRO-01).
  - [ ] Test: nuevo horario coincide con bloqueo de profesional o sillón lanza `DentroDeBloqueo` (RN-TUR-05).
  - [ ] Test: cambio exitoso con reasignación de nuevo profesional y nuevo sillón devuelve el `Turno` actualizado con mismo `id` (D-05).
- [ ] 1.2 Implementar la función `validar_reprogramacion(...)` en `app/domain/reglas_turno.py` haciendo pasar todos los tests de dominio en verde.

## 2. Persistencia y Transaccionalidad (`app/db/`)

- [ ] 2.1 Escribir tests unitarios/integración para la persistencia de reprogramación en el repositorio de turnos (`tests/api/test_repositorio_turnos.py`):
  - [ ] Test: reprogramación exitosa actualiza campos en tabla `turno` e inserta fila en `auditoria_turno` con `accion = 'reprogramar'` y JSON `antes`/`despues` (RN-AUD-01).
  - [ ] Test: si ocurre un fallo o excepción, la transacción revierte y no se inserta auditoría (RN-AUD-03).
- [ ] 2.2 Implementar en el repositorio la función `reprogramar_turno(...)` dentro de `with transaccion(conexion):` (SQLite `BEGIN IMMEDIATE`).

## 3. Capa API y Endpoint (`app/api/turnos.py`)

- [ ] 3.1 Escribir tests de integración API para `POST /turnos/{id}/reprogramar` en `tests/api/test_reprogramar_turno.py`:
  - [ ] Test: reprogramación exitosa con rol `recepcion` y `administracion` devuelve 200 y el turno actualizado (US-008).
  - [ ] Test: odontólogo intentando reprogramar recibe 403 `SinPermiso` (RN-ACC-02).
  - [ ] Test: solicitud sin token recibe 401 `NoAutenticado` (RN-ACC-01).
  - [ ] Test: turno inexistente devuelve 404 (US-008).
  - [ ] Test: nuevo profesional o nuevo sillón inexistente o inactivo devuelve 422 `DatoInvalido`.
  - [ ] Test: conflicto de agenda, bloqueo o fuera de horario devuelve 409 y la cantidad de filas en `auditoria_turno` no cambia (RN-AUD-03).
- [ ] 3.2 Definir los esquemas Pydantic `ReprogramarTurnoRequest`.
- [ ] 3.3 Implementar el endpoint `POST /turnos/{id}/reprogramar` con `requiere_rol("administracion", "recepcion")` y reloj inyectado de la aplicación.

## 4. Verificación y Cierre

- [ ] 4.1 Ejecutar suite completa con `pytest` y comprobar que todos los tests pasen en verde.
- [ ] 4.2 Verificar el cumplimiento de las 14 Reglas Duras de `AGENTS.md`.
- [ ] 4.3 Generar informe de verificación `verify.md`.
