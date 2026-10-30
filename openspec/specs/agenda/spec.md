# agenda Specification

## Purpose

Permitir la consulta de turnos activos y bloqueos en un rango de fechas para un profesional o un sillón, garantizando el orden cronológico de los eventos, la exclusión de turnos cancelados y el control de acceso estricto según el rol del usuario (`US-009`, `US-010`, `Flujo 6`, `RN-ACC-03`).

## Requirements

### Requirement: Consulta cronológica de agenda de un profesional

La agenda de un profesional SHALL devolver todos los turnos activos (`estado = 'reservado'`) y los bloqueos vigentes dentro del intervalo solicitado, ordenados cronológicamente por `inicio`.

#### Scenario: Consulta válida de agenda diaria de profesional

- **Dado** que el profesional 1 ("Dr. Perez (ficticio)") tiene un turno activo de 09:00 a 09:30 del día 2026-11-16,
- **Y** que tiene un bloqueo de agenda de 11:00 a 12:00 del mismo día,
- **Y** que tiene otro turno activo de 10:00 a 10:30 del mismo día,
- **Cuando** un usuario con rol `recepcion` consulta `GET /agenda/profesionales/1?desde=2026-11-16T00:00:00&hasta=2026-11-16T23:59:59`,
- **Entonces** el sistema responde con código HTTP 200 (OK),
- **Y** devuelve una lista de eventos ordenada por inicio: primero el turno de las 09:00, segundo el turno de las 10:00, y tercero el bloqueo de las 11:00.

### Requirement: Exclusión estricta de turnos cancelados

Los turnos que han sido cancelados no ocupan lugar en la agenda y SHALL NOT aparecer en la respuesta de consulta (`RN-TUR-08`).

#### Scenario: Turno cancelado en el rango solicitado

- **Dado** que el profesional 1 tiene un turno activo de 09:00 a 09:30 del día 2026-11-16,
- **Y** que tiene un turno con estado `cancelado` de 10:00 a 10:30 del mismo día,
- **Cuando** administración consulta la agenda del profesional 1 para el día 2026-11-16,
- **Entonces** el sistema responde con código HTTP 200 (OK),
- **Y** la respuesta contiene únicamente el turno activo de las 09:00, omitiendo el turno cancelado.

### Requirement: Validación de rango temporal de consulta

El parámetro `desde` no puede ser posterior al parámetro `hasta`. Ante un rango invertido, el sistema SHALL rechazar la solicitud.

#### Scenario: Rango con fecha desde posterior a hasta

- **Dado** un usuario autenticado con rol `administracion`,
- **Cuando** solicita `GET /agenda/profesionales/1?desde=2026-11-20T18:00:00&hasta=2026-11-20T08:00:00`,
- **Entonces** el sistema responde con código HTTP 422 (`DatoInvalido`),
- **Y** el mensaje de error indica que el rango de fechas es inválido.

### Requirement: Confidencialidad y control RBAC para odontólogos

Un usuario con rol `odontologo` SHALL poder visualizar únicamente su propia agenda profesional vinculada (`usuario.profesional_id == id`), y SHALL NOT poder consultar agendas de otros profesionales ni de sillones (`RN-ACC-03`, `03_actores_y_roles.md`).

#### Scenario: Odontólogo consulta su propia agenda profesional

- **Dado** un usuario con rol `odontologo` vinculado al profesional con `id = 2`,
- **Cuando** envía una petición `GET /agenda/profesionales/2?desde=2026-11-16T08:00:00&hasta=2026-11-16T18:00:00`,
- **Entonces** el sistema responde con código HTTP 200 (OK) con sus eventos de agenda.

#### Scenario: Odontólogo intenta consultar la agenda de otro colega

- **Dado** un usuario con rol `odontologo` vinculado al profesional con `id = 2`,
- **Cuando** envía una petición `GET /agenda/profesionales/1?desde=2026-11-16T08:00:00&hasta=2026-11-16T18:00:00`,
- **Entonces** el sistema responde con código HTTP 403 (`SinPermiso`).

#### Scenario: Odontólogo intenta consultar la agenda de un sillón

- **Dado** un usuario con rol `odontologo`,
- **Cuando** envía una petición `GET /agenda/sillones/1?desde=2026-11-16T08:00:00&hasta=2026-11-16T18:00:00`,
- **Entonces** el sistema responde con código HTTP 403 (`SinPermiso`).

### Requirement: Consulta de agenda por sillón

Administración y recepción SHALL poder consultar la agenda de un sillón para visualizar los turnos agendados en él y los bloqueos de mantenimiento asignados (`US-010`).

#### Scenario: Consulta válida de agenda de sillón

- **Dado** que el sillón 1 ("Sillón Odontológico 1 (ficticio)") tiene un turno activo de 14:00 a 14:45,
- **Y** un bloqueo por mantenimiento de 15:00 a 16:00,
- **Cuando** recepción consulta `GET /agenda/sillones/1?desde=2026-11-16T00:00:00&hasta=2026-11-16T23:59:59`,
- **Entonces** el sistema responde con código HTTP 200 (OK),
- **Y** devuelve ambos eventos ordenados por hora de inicio.
