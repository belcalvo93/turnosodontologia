# Spec — C-13 reprogramar-turno

## Propósito

Permitir a los roles de recepción y administración reprogramar un turno futuro activo, modificando su horario de inicio (y opcionalmente profesional y/o sillón), conservando el identificador del turno y registrando de manera atómica el cambio en la auditoría con los estados anterior y posterior (`US-008`, `RN-TUR-07`, `RN-TUR-08`, `RN-AUD-01`, `D-05`).

---

## Requisitos y Escenarios

### Requisito 1: Reprogramación exitosa a un horario libre

El sistema debe permitir mover un turno futuro a una nueva fecha y horario disponibles dentro de la franja de atención del profesional, recalculando el fin según la prestación y registrando la auditoría atómicamente.

#### Escenario 1: Reprogramación válida de un turno futuro
- **Dado** que el paciente con DNI "11111111 (ficticio)" tiene un turno con `id = 1` reservado con el profesional 1 en el sillón 1 para el 2026-11-10 de 09:00 a 09:30 (prestación de 30 minutos),
- **Y** que el momento actual del sistema es 2026-11-09 08:00 (el turno es futuro),
- **Y** que el profesional atiende los martes de 08:00 a 14:00 y no tiene otros turnos ni bloqueos entre las 11:00 y las 11:30 del 2026-11-10,
- **Cuando** un usuario con rol `recepcion` solicita reprogramar el turno 1 para el 2026-11-10 a las 11:00,
- **Entonces** el sistema responde con código HTTP 200 (OK),
- **Y** el turno conserva su `id = 1`,
- **Y** el inicio pasa a ser 2026-11-10 11:00 y el fin 2026-11-10 11:30,
- **Y** se genera un registro en `auditoria_turno` con `accion = 'reprogramar'`, guardando el estado anterior y el nuevo estado.

---

### Requisito 2: Mover el turno sobre su propio horario previo

El turno no debe colisionar consigo mismo al reprogramarse hacia un horario contiguo o parcialmente superpuesto con su franja original (`RN-TUR-08`).

#### Escenario 2: Reprogramación que solapa parcialmente con el horario anterior
- **Dado** que el turno con `id = 2` está reservado para el profesional 1 de 10:00 a 10:30,
- **Y** que el momento actual es 2026-11-09 08:00 (el turno es futuro),
- **Y** que no existen otros turnos reservados en el intervalo de 10:15 a 10:45,
- **Cuando** el usuario solicita reprogramar el turno 2 para el mismo día a las 10:15 (nuevo fin 10:45),
- **Entonces** el sistema responde con código HTTP 200 (OK),
- **Y** el turno 2 queda agendado de 10:15 a 10:45 sin reportar conflicto de agenda consigo mismo.

---

### Requisito 3: Rechazo ante colisión de agenda sin registro de auditoría

Si el nuevo horario propuesto se superpone con otro turno activo de ese profesional, de ese sillón o de ese paciente, o cae dentro de un bloqueo o fuera de horario, la reprogramación debe rechazarse y no generar ninguna alteración ni registro de auditoría (`RN-AUD-03`).

#### Escenario 3: Conflicto con otro turno activo
- **Dado** que el turno con `id = 3` está reservado para el profesional 1 de 09:00 a 09:30 del 2026-11-10,
- **Y** que el profesional 1 ya tiene reservado el turno con `id = 4` de 10:00 a 10:30 del 2026-11-10,
- **Cuando** recepción solicita reprogramar el turno 3 para el 2026-11-10 a las 10:15,
- **Entonces** el sistema responde con código HTTP 409 (Conflicto),
- **Y** el turno 3 permanece inalterado de 09:00 a 09:30,
- **Y** no se agrega ningún registro en `auditoria_turno`.

---

### Requisito 4: Inmutabilidad de turnos pasados o cancelados

No se puede reprogramar un turno que ya pasó, que está en curso o que fue cancelado (`RN-TUR-09`, `RN-TUR-10`).

#### Escenario 4: Intento de reprogramar un turno pasado
- **Dado** que un turno tiene inicio a las 09:00 y fin a las 09:30,
- **Y** que el reloj del sistema marca las 09:15 (turno en curso) o las 10:00 (turno pasado),
- **Cuando** se solicita reprogramar dicho turno,
- **Entonces** el sistema responde con código HTTP 409 (`TurnoNoModificable`),
- **Y** el turno permanece sin cambios.

#### Escenario 5: Intento de reprogramar un turno cancelado
- **Dado** que un turno futuro tiene estado `cancelado`,
- **Cuando** se solicita reprogramar dicho turno,
- **Entonces** el sistema responde con código HTTP 409 (`TurnoNoModificable`),
- **Y** el turno permanece cancelado.

---

### Requisito 5: Control de acceso RBAC

Solo recepción y administración pueden reprogramar turnos. Los odontólogos no tienen permiso para esta operación (`RN-ACC-02`).

#### Escenario 6: Odontólogo intentando reprogramar
- **Dado** que un usuario autenticado tiene el rol `odontologo`,
- **Cuando** envía una petición `POST /turnos/1/reprogramar`,
- **Entonces** el sistema responde con código HTTP 403 (Sin Permiso).
