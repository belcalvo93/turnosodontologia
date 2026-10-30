# Spec Delta

## Purpose

Gestión de bloqueos horarios por profesional o por sillón: al crear un bloqueo, el sistema además informa los turnos reservados que quedan dentro del intervalo del recurso bloqueado, sin cancelarlos ni modificarlos, para que recepción los reprograme o cancele a mano.

## MODIFIED Requirements

### Requirement: Creación de bloqueo sobre profesional o sillón

El sistema SHALL permitir al rol `administracion` crear un bloqueo mediante `POST /bloqueos` indicando `alcance` (`profesional` o `sillon`), `recurso_id`, `inicio`, `fin` y `motivo`, siempre que `inicio < fin` y que el `recurso_id` corresponda a un profesional o sillón existente según el `alcance`. Cuando los datos son válidos, SHALL persistir el bloqueo y responder `201`.

Además, para cualquier alcance admitido (`profesional` o `sillon`), la respuesta de `POST /bloqueos` SHALL incluir al mismo nivel del bloqueo creado el campo `turnos_afectados`: la lista de turnos con `estado = 'reservado'` cuyo intervalo `[inicio, fin)` se solapa con el intervalo del bloqueo (intervalos semiabiertos: los turnos contiguos al borde, con `fin == bloqueo.inicio` o `inicio == bloqueo.fin`, no se consideran afectados) y cuyo `profesional_id` o `sillon_id` coincide con el recurso bloqueado. Los turnos afectados SHALL devolverse ordenados por `inicio ASC, id ASC` y SHALL conservar su `estado = 'reservado'` sin registrarse en `auditoria_turno`: el sistema SHALL NOT cancelar, modificar ni reprogramar los turnos afectados al crear un bloqueo. El alcance global ("consultorio") queda fuera de alcance.

#### Scenario: Alta válida de bloqueo para un profesional

- **Dado** un usuario autenticado con rol `administracion` y un profesional existente
- **Cuando** envía `POST /bloqueos` con `alcance = "profesional"`, el `recurso_id` de ese profesional, `inicio = "2026-11-10T09:00:00"`, `fin = "2026-11-10T13:00:00"` y `motivo = "Vacaciones"`
- **Entonces** el sistema responde `201` con el bloqueo creado e identificador asignado

#### Scenario: Rechazo por intervalo inválido (inicio mayor o igual que fin)

- **Dado** un usuario autenticado con rol `administracion` y un sillón existente
- **Cuando** envía `POST /bloqueos` con `inicio` igual o posterior a `fin`
- **Entonces** el sistema responde `422` con un mensaje de error en español y no persiste el bloqueo

#### Scenario: Rechazo por recurso inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /bloqueos` con `alcance = "profesional"` (o `"sillon"`) y un `recurso_id` que no existe en la tabla correspondiente
- **Entonces** el sistema responde `422` con un mensaje de error en español y no persiste el bloqueo

#### Scenario: Crear un bloqueo reporta los turnos reservados solapados (RN-TUR-05 con RN-TUR-04)

- **Dado** un usuario con rol `administracion`, un profesional con un turno `reservado` de `10:00` a `10:30` (y un sillón con su propio turno en el mismo rango) y datos ficticios rotulados con sufijo `"(ficticio)"`
- **Cuando** crea un bloqueo `alcance = "profesional"` con intervalo `09:30–10:30`
- **Entonces** responde `201` con el bloqueo y `turnos_afectados` contiene exactamente el turno `reservado` de ese profesional (con `id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin`, `estado`), sin el turno del otro recurso

#### Scenario: Crear un bloqueo de sillón reporta solo los turnos de ese sillón

- **Dado** un usuario con rol `administracion`, un sillón A con un turno `reservado` que cae dentro del intervalo, y un profesional con su propio turno en el mismo rango
- **Cuando** crea un bloqueo `alcance = "sillon"` sobre el sillón A
- **Entonces** responde `201` y `turnos_afectados` contiene solo el turno del sillón A: los turnos de otro profesional o de otro sillón no se reportan

#### Scenario: Los turnos contiguos al intervalo del bloqueo no se reportan (RN-TUR-04)

- **Dado** un usuario con rol `administracion` y dos turnos `reservado` del mismo profesional, uno de `08:00` a `10:00` y otro de `13:00` a `15:00`
- **Cuando** crea un bloqueo para ese profesional con intervalo `10:00–13:00`
- **Entonces** responde `201` con `turnos_afectados = []`: los intervalos semiabiertos `[inicio, fin)` hacen que los turnos que terminan o empiezan en el borde del bloqueo no lo afecten

#### Scenario: Los turnos cancelados no se reportan (RN-TUR-08)

- **Dado** un usuario con rol `administracion`, un profesional con dos turnos `reservado` y un turno `cancelado` que quedan dentro del intervalo
- **Cuando** crea un bloqueo para ese profesional sobre ese intervalo
- **Entonces** responde `201` y `turnos_afectados` contiene solo los 2 turnos `reservado`; el turno `cancelado` no ocupa agenda

#### Scenario: turnos_afectados llega vacío cuando no hay turnos superpuestos

- **Dado** un usuario con rol `administracion` y un sillón sin turnos que se superpongan con el intervalo
- **Cuando** crea un bloqueo `alcance = "sillon"` sobre ese intervalo
- **Entonces** responde `201` con el bloqueo creado y `turnos_afectados = []`

#### Scenario: Los turnos afectados se listan ordenados por inicio y no se modifican

- **Dado** un usuario con rol `administracion`, un profesional con un turno `reservado` de `11:00` a `11:30`, otro de `10:00` a `10:30` y un tercero de `10:30` a `11:00` (id mayor), todos dentro del intervalo del bloqueo
- **Cuando** crea el bloqueo para ese profesional y luego consulta cada turno reportado por su `id`
- **Entonces** `turnos_afectados` está ordenado por `inicio ASC` (empatados por `id ASC`), cada turno sigue con `estado = "reservado"` y no se agregó ninguna fila en `auditoria_turno`

#### Scenario: GET /bloqueos no incluye turnos_afectados

- **Dado** al menos un bloqueo registrado creado con reporte de turnos afectados
- **Cuando** un usuario autenticado (cualquier rol) consulta `GET /bloqueos`
- **Entonces** cada bloqueo del listado conserva exactamente sus campos `id, alcance, recurso_id, inicio, fin, motivo` y no incluye la clave `turnos_afectados`
