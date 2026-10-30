# Proposal — C-13 reprogramar-turno

## Why

Recepción y administración necesitan reprogramar un turno agendado ante solicitudes de cambio por parte del paciente o necesidades del consultorio (`US-008`), permitiendo modificar su horario de inicio y opcionalmente reasignar profesional o sillón, sin perder el identificador original del turno y registrando el cambio en la auditoría con valores antes y después (`RN-AUD-01`, `D-05`, `SE-21`). 

`C-13` es una de las ramas clave del ciclo de vida del turno (`Fase 3`), corre en paralelo con `C-12` (`cancelar-turno`) y `C-14` (`agenda`), y es requisito indispensable para desbloquear `C-15` (`consulta-auditoria`).

## What Changes

1. **Dominio Puro (`app/domain/reglas_turno.py`):**
   - Incorporación de `validar_reprogramacion(turno, nuevo_inicio, ahora, duracion_minutos, horarios_profesional, bloqueos_profesional, bloqueos_sillon, turnos_existentes, nuevo_profesional_id=None, nuevo_sillon_id=None) -> Turno`:
     - Valida que el turno esté en estado `reservado` y que sea futuro (`turno.inicio > ahora`, `RN-TUR-09`, `RN-TUR-10`). De lo contrario lanza `TurnoNoModificable` (mapeado a HTTP 409).
     - Recalcula el nuevo fin sumando la duración en minutos de la prestación (`RN-TUR-01`).
     - Reutiliza la validación de alta (`validar_alta`) en el nuevo intervalo pasando `excluir_turno_id=turno.id` para no generar autocolisión consigo mismo (`RN-TUR-07`, `RN-TUR-08`).
     - Devuelve una nueva instancia inmutable de `Turno` con el mismo `id`, mismo `paciente_id`, misma `prestacion_id`, nuevo horario y recursos actualizados.

2. **Capa de Persistencia (`app/db/`):**
   - Operación transaccional `reprogramar_turno_en_db` en el repositorio de turnos:
     - Ejecutada dentro del context manager `transaccion(conexion)` (`BEGIN IMMEDIATE`).
     - Actualiza el registro en la tabla `turno`.
     - Inserta el registro en `auditoria_turno` (`accion = 'reprogramar'`, `usuario_id`, `ocurrio_en`, `antes`, `despues`).
     - Si la validación o ejecución falla, la transacción revierte y no se escribe auditoría (`RN-AUD-03`).

3. **Capa API (`app/api/turnos.py`):**
   - Endpoint `POST /turnos/{id}/reprogramar`.
   - Esquemas Pydantic `ReprogramarTurnoRequest` (`nuevo_inicio: datetime`, `nuevo_profesional_id: int | None`, `nuevo_sillon_id: int | None`) y `TurnoResponse`.
   - Control de acceso: permitido para `administracion` y `recepcion`; `403` para `odontologo`; `401` sin token.
   - Reloj inyectado mediante `app.state.reloj` para pruebas determinísticas de tiempo.

4. **Tests:**
   - Tests de dominio en `tests/domain/test_reglas_turno.py`: turno en el pasado o presente (409), turno cancelado (409), mover sobre su propio horario previo (válido, 200/éxito), colisión con otro turno de profesional o sillón (409), fuera de horario de atención (409), dentro de bloqueo (409).
   - Tests de API en `tests/api/test_reprogramar_turno.py`: endpoints con permisos RBAC, atomicidad de auditoría ante rechazo, respuesta 404 si el turno no existe, respuesta 422 si el profesional o sillón reasignado no existe o está inactivo.

**Fuera de alcance:** cancelación de turnos (`C-12`), consulta cronológica de auditoría (`C-15`), cálculo de sobreturnos (prohibidos por `RN-TUR-11`) y reglas de anticipación mínima configurable (diferenciador fuera del MVP).

## Capabilities

### New Capabilities
- `reprogramar-turno`: capacidad de modificar el inicio, profesional y sillón de un turno futuro activo manteniendo su id y registrando trazabilidad atómica en auditoría.

### Modified Capabilities
- Ninguna.

## Impact

- **Archivos nuevos:**
  - `openspec/changes/c-13-reprogramar-turno/` (artefactos OpenSpec).
  - `tests/api/test_reprogramar_turno.py` (suite de tests de API).
- **Archivos modificados:**
  - `app/domain/reglas_turno.py`: agrega `validar_reprogramacion`.
  - `app/api/turnos.py`: agrega ruta `POST /turnos/{id}/reprogramar`.
  - Repositorio de turnos en `app/db/`.
  - `tests/domain/test_reglas_turno.py`: agrega casos de prueba de dominio de reprogramación.
- **Dependencias:**
  - Requiere `C-02` (`dominio-base`, completado), `C-10` (`reglas-alta-turno`, completado) y `C-11` (`crear-turno`, en desarrollo).
  - Desbloquea `C-15` (`consulta-auditoria`) junto con `C-12`.
- **Governance:** ALTO (involucra modificación de turnos, reglas de negocio y transacciones de auditoría).
