# Proposal — C-12 cancelar-turno

## Why

Recepción y administración necesitan poder cancelar un turno futuro cuando un paciente avisa que no asistirá, liberando el horario del profesional, del sillón y del paciente (`RN-TUR-06`) y dejando constancia auditable de quién canceló y cuándo (`RN-AUD-01`). `C-12` forma parte del camino crítico (`C-01 → C-03 → C-04 → C-09 → C-11 → C-12 → C-15 → C-17`) y es requisito directo de `C-15 consulta-auditoria`.

## What Changes

- Se agrega `validar_cancelacion(turno: Turno, ahora: datetime) -> Turno` en `app/domain/reglas_turno.py`:
  - Verifica con el reloj inyectado `ahora` que el turno sea futuro (`turno.inicio > ahora`, `RN-TUR-09`) y que no esté ya en estado `cancelado` (`RN-TUR-10`).
  - Lanza `TurnoNoModificable` (mapeado a HTTP `409`) si el turno ya está cancelado, en curso (`inicio == ahora`) o en el pasado (`inicio < ahora`).
  - Devuelve el `Turno` con `estado = "cancelado"`.
- Se agrega la operación transaccional de cancelación en la capa de persistencia (`app/db/`): dentro de una única `transaccion(conexion)` (`BEGIN IMMEDIATE`), carga el turno por `id` (`404` si no existe), invoca `validar_cancelacion(turno, ahora)`, actualiza `turno.estado = 'cancelado'` e inserta el registro correspondiente en `auditoria_turno` (`accion = 'cancelar'`, `usuario_id`, `ocurrio_en`, `antes`, `despues`). Si la validación falla, no modifica el turno ni inserta registro de auditoría (`RN-AUD-03`).
- Se agrega el endpoint `POST /turnos/{id}/cancelar` en `app/api/turnos.py` restringido a los roles `administracion` y `recepcion` (`403` para `odontologo`, `401` sin autenticar).
- Se agregan tests unitarios de dominio (`tests/domain/test_reglas_turno.py`) y de API (`tests/api/test_cancelar_turno.py`) con reloj fijo (antes, igual y después del inicio), segunda cancelación (`409`), turno inexistente (`404`), y prueba de que cancelar un turno permite volver a reservar ese mismo hueco con `201` (`RN-TUR-06`).

**Fuera de alcance:** reglas de anticipación mínima configurable (`IF-10` / `SE-08`, diferenciador fuera del MVP), lista de espera automática (`IF-03`), reprogramación (`C-13`) y consulta de auditoría (`C-15`).

## Capabilities

### New Capabilities

- `cancelar-turno`: cancelación de turnos futuros con liberación del horario en agenda y registro atómico en auditoría.

### Modified Capabilities

Ninguna.

## Impact

- **Archivos nuevos:** `tests/api/test_cancelar_turno.py`.
- **Archivos modificados:** `app/domain/reglas_turno.py` (`validar_cancelacion`), repositorio de turnos en `app/db/`, `app/api/turnos.py` (`POST /turnos/{id}/cancelar`), `tests/domain/test_reglas_turno.py`.
- **Sin cambios:** `knowledge-base/`, `CHANGES.md` (hasta archivar), `docs/`.
- **Dependencias:** requiere `C-11` (`crear-turno`) y `C-02` (`dominio-base`). Habilita `C-15` (`consulta-auditoria`).
