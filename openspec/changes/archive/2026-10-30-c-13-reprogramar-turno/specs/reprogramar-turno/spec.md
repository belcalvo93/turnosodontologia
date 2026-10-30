# Spec — C-13 reprogramar-turno

## Propósito

Permitir a los roles de recepción y administración reprogramar un turno futuro activo, modificando su horario de inicio (y opcionalmente profesional y/o sillón), conservando el identificador del turno y registrando de manera atómica el cambio en la auditoría con los estados anterior y posterior (`US-008`, `RN-TUR-07`, `RN-TUR-08`, `RN-AUD-01`, `D-05`).

---

## ADDED Requirements

### Requirement: Reprogramación exitosa a un horario libre

El sistema SHALL permitir mover un turno futuro a una nueva fecha y horario disponibles dentro de la franja de atención del profesional, recalculando el fin según la prestación y registrando la auditoría atómicamente.

#### Scenario: Reprogramación válida de un turno futuro
- **Dado** que el paciente con DNI "11111111 (ficticio)" tiene un turno con `id = 1` reservado con el profesional 1 en el sillón 1 para el 2026-11-10 de 09:00 a 09:30 (prestación de 30 minutos),
- **Y** que el momento actual del sistema es 2026-11-09 08:00 (el turno es futuro),
- **Y** que el profesional atiende los martes de 08:00 a 14:00 y no tiene otros turnos ni bloqueos entre las 11:00 y las 11:30 del 2026-11-10,
- **Cuando** un usuario con rol `recepcion` solicita reprogramar el turno 1 para el 2026-11-10 a las 11:00,
- **Entonces** el sistema responde con código HTTP 200 (OK),
- **Y** el turno conserva su `id = 1`,
- **Y** el inicio pasa a ser 2026-11-10 11:00 y el fin 2026-11-10 11:30,
- **Y** se genera un registro en `auditoria_turno` con `accion = 'reprogramar'`, guardando el estado anterior y el nuevo estado.

---

### Requirement: Mover el turno sobre su propio horario previo

El turno SHALL NOT colisionar consigo mismo al reprogramarse hacia un horario contiguo o parcialmente superpuesto con su franja original (`RN-TUR-08`).

#### Scenario: Reprogramación que solapa parcialmente con el horario anterior
- **Dado** que el turno con `id = 2` está reservado para el profesional 1 de 10:00 a 10:30,
- **Y** que el momento actual es 2026-11-09 08:00 (el turno es futuro),
- **Y** que no existen otros turnos reservados en el intervalo de 10:15 a 10:45,
- **Cuando** el usuario solicita reprogramar el turno 2 para el mismo día a las 10:15 (nuevo fin 10:45),
- **Entonces** el sistema responde con código HTTP 200 (OK),
- **Y** el turno 2 queda agendado de 10:15 a 10:45 sin reportar conflicto de agenda consigo mismo.

---

### Requirement: Rechazo ante colisión de agenda sin registro de auditoría

Si el nuevo horario propuesto se superpone con otro turno activo de ese profesional, de ese sillón o de ese paciente, o cae dentro de un bloqueo o fuera de horario, la reprogramación SHALL rechazarse y no generar ninguna alteración ni registro de auditoría (`RN-AUD-03`).

#### Scenario: Conflicto con otro turno activo
- **Dado** que el turno con `id = 3` está reservado para el profesional 1 de 09:00 a 09:30 del 2026-11-10,
- **Y** que el profesional 1 ya tiene reservado el turno con `id = 4` de 10:00 a 10:30 del 2026-11-10,
- **Cuando** recepción solicita reprogramar el turno 3 para el 2026-11-10 a las 10:15,
- **Entonces** el sistema responde con código HTTP 409 (Conflicto),
- **Y** el turno 3 permanece inalterado de 09:00 a 09:30,
- **Y** no se agrega ningún registro en `auditoria_turno`.

---

### Requirement: Inmutabilidad de turnos pasados o cancelados

El sistema SHALL NOT permitir reprogramar un turno que ya pasó, que está en curso o que fue cancelado (`RN-TUR-09`, `RN-TUR-10`).

#### Scenario: Intento de reprogramar un turno pasado
- **Dado** que un turno tiene inicio a las 09:00 y fin a las 09:30,
- **Y** que el reloj del sistema marca las 09:15 (turno en curso) o las 10:00 (turno pasado),
- **Cuando** se solicita reprogramar dicho turno,
- **Entonces** el sistema responde con código HTTP 409 (`TurnoNoModificable`),
- **Y** el turno permanece sin cambios.

#### Scenario: Intento de reprogramar un turno cancelado
- **Dado** que un turno futuro tiene estado `cancelado`,
- **Cuando** se solicita reprogramar dicho turno,
- **Entonces** el sistema responde con código HTTP 409 (`TurnoNoModificable`),
- **Y** el turno permanece cancelado.

---

### Requirement: Control de acceso RBAC

El sistema SHALL permitir reprogramar turnos solo a recepción y administración. Los odontólogos no tienen permiso para esta operación (`RN-ACC-02`).

#### Scenario: Odontólogo intentando reprogramar
- **Dado** que un usuario autenticado tiene el rol `odontologo`,
- **Cuando** envía una petición `POST /turnos/1/reprogramar`,
- **Entonces** el sistema responde con código HTTP 403 (Sin Permiso).

---

### Requirement: Validación de recursos nuevos y orden de rechazo

Si la solicitud envía `nuevo_profesional_id` o `nuevo_sillon_id`, el sistema SHALL rechazar con HTTP 422 un recurso enviado que no exista o esté inactivo (`RN-REC-03`). El sistema SHALL evaluar primero si el turno está cancelado o pasado (HTTP 409), después los recursos nuevos (HTTP 422) y por último la disponibilidad en agenda (HTTP 409). Un rechazo SHALL NOT alterar el turno ni generar registro de auditoría (`RN-AUD-03`).

#### Scenario: Nuevo profesional inexistente
- **Dado** que el turno con `id = 5` es futuro y está reservado,
- **Y** que no existe un profesional con `id = 99`,
- **Cuando** recepción solicita reprogramar el turno 5 con `nuevo_profesional_id = 99`,
- **Entonces** el sistema responde con código HTTP 422 (`DatoInvalido`),
- **Y** el turno 5 permanece sin cambios,
- **Y** no se agrega ningún registro en `auditoria_turno`.

#### Scenario: Nuevo sillón inactivo
- **Dado** que el turno con `id = 5` es futuro y está reservado,
- **Y** que el sillón 2 está inactivo,
- **Cuando** recepción solicita reprogramar el turno 5 con `nuevo_sillon_id = 2`,
- **Entonces** el sistema responde con código HTTP 422 (`DatoInvalido`),
- **Y** el turno 5 permanece sin cambios,
- **Y** no se agrega ningún registro en `auditoria_turno`.

#### Scenario: Turno cancelado con nuevo sillón inactivo
- **Dado** que el turno con `id = 6` tiene estado `cancelado`,
- **Y** que el sillón 2 está inactivo,
- **Cuando** recepción solicita reprogramar el turno 6 con `nuevo_sillon_id = 2`,
- **Entonces** el sistema responde con código HTTP 409 (`TurnoNoModificable`),
- **Y** el turno 6 permanece cancelado,
- **Y** no se agrega ningún registro en `auditoria_turno`.
