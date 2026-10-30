# Spec Delta

## Purpose

Alta y consulta de turnos del consultorio: reserva un turno validando horario, bloqueos y solapamientos de profesional, sillón y paciente en una única transacción, y permite consultarlo por id respetando los permisos de cada rol.

## ADDED Requirements

### Requirement: Alta de turno reservado

El sistema SHALL permitir crear un turno mediante `POST /turnos` con `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id` e `inicio` (hora local del consultorio, sin offset). El cliente no envía el fin: el sistema SHALL calcularlo como `inicio + duración de la prestación`, guardar el turno con estado `reservado` y responder `201` con el turno creado (RN-TUR-01, RN-TUR-14).

#### Scenario: Recepción crea un turno válido

- **Dado** un usuario `recepcion` autenticado, el profesional "Odontólogo Ficticio A" con horario lunes 09:00-13:00, el "Sillón 1", la prestación "Consulta ficticia" de 30 minutos y el paciente "Paciente Ficticio 1" (DNI "00000001 (ficticio)"), sin bloqueos ni turnos
- **Cuando** envía `POST /turnos` con esos recursos e `inicio = "2026-01-12T10:00:00"` (lunes)
- **Entonces** responde `201` con un `id` asignado, `inicio = "2026-01-12T10:00:00"`, `fin = "2026-01-12T10:30:00"` y `estado = "reservado"`

#### Scenario: El fin depende de la duración de la prestación

- **Dado** el mismo contexto y la prestación "Limpieza ficticia" de 45 minutos
- **Cuando** se crea un turno con esa prestación e `inicio = "2026-01-12T10:00:00"`
- **Entonces** responde `201` con `fin = "2026-01-12T10:45:00"`

#### Scenario: Administración también puede crear turnos

- **Dado** un usuario `administracion` autenticado y el mismo contexto válido
- **Cuando** envía `POST /turnos` con datos válidos
- **Entonces** responde `201` con `estado = "reservado"`

#### Scenario: El turno creado queda persistido

- **Dado** un turno recién creado con `POST /turnos`
- **Cuando** se lo consulta con `GET /turnos/{id}` usando el `id` devuelto
- **Entonces** responde `200` con los mismos `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin` y `estado`

### Requirement: Rechazo de solapamientos con intervalos semiabiertos

El sistema SHALL rechazar con `409` y `codigo` `conflicto_agenda` el alta de un turno que se superpone con otro turno `reservado` del mismo profesional, del mismo sillón o del mismo paciente (RN-TUR-03, RN-TUR-12). Los intervalos son semiabiertos `[inicio, fin)`: los turnos contiguos SHALL aceptarse (RN-TUR-04) y los turnos cancelados MUST NOT generar conflicto (RN-TUR-08).

#### Scenario: Solapamiento por profesional

- **Dado** un turno reservado de "Odontólogo Ficticio A" en el "Sillón 1" de 10:00 a 10:30
- **Cuando** se crea otro turno de "Odontólogo Ficticio A" en el "Sillón 2" a las 10:15
- **Entonces** responde `409` con `codigo` `conflicto_agenda` y un mensaje en español

#### Scenario: Solapamiento por sillón

- **Dado** un turno reservado de "Odontólogo Ficticio A" en el "Sillón 1" de 10:00 a 10:30
- **Cuando** se crea un turno de "Odontóloga Ficticia B" en el "Sillón 1" a las 10:15
- **Entonces** responde `409` con `codigo` `conflicto_agenda`

#### Scenario: Solapamiento por paciente

- **Dado** un turno reservado del "Paciente Ficticio 1" con "Odontólogo Ficticio A" en el "Sillón 1" de 10:00 a 10:30
- **Cuando** se crea un turno del mismo paciente con "Odontóloga Ficticia B" en el "Sillón 2" a las 10:15
- **Entonces** responde `409` con `codigo` `conflicto_agenda`

#### Scenario: Turnos contiguos aceptados

- **Dado** un turno reservado de "Odontólogo Ficticio A" en el "Sillón 1" de 10:00 a 10:30
- **Cuando** se crea un turno del mismo profesional y sillón a las 10:30 y otro a las 09:30 (termina 10:00)
- **Entonces** ambos responden `201`

#### Scenario: Un minuto de superposición se rechaza

- **Dado** un turno reservado de "Odontólogo Ficticio A" en el "Sillón 1" de 10:00 a 10:30
- **Cuando** se crea un turno del mismo profesional a las 10:29
- **Entonces** responde `409` con `codigo` `conflicto_agenda`

#### Scenario: Un turno cancelado no ocupa agenda

- **Dado** un turno en estado `cancelado` de "Odontólogo Ficticio A" en el "Sillón 1" de 10:00 a 10:30
- **Cuando** se crea un turno del mismo profesional y sillón a las 10:00
- **Entonces** responde `201`

### Requirement: Rechazo fuera de horario o dentro de un bloqueo

El sistema SHALL rechazar con `409` el alta de un turno que no entra completo en una franja de atención del profesional (`codigo` `fuera_de_horario`) o que se superpone con un bloqueo del profesional o del sillón elegido (`codigo` `dentro_de_bloqueo`), con intervalos semiabiertos también para los bloqueos (RN-TUR-05, RN-GLO-01).

#### Scenario: Turno que termina después del fin de la franja

- **Dado** el profesional con horario lunes 09:00-13:00 y la prestación "Consulta ficticia" de 30 minutos
- **Cuando** se crea un turno el lunes a las 12:45
- **Entonces** responde `409` con `codigo` `fuera_de_horario` y un mensaje en español

#### Scenario: Turno en un día sin horario

- **Dado** el profesional con horario solo los lunes
- **Cuando** se crea un turno el martes a las 10:00
- **Entonces** responde `409` con `codigo` `fuera_de_horario`

#### Scenario: Turno dentro de un bloqueo del sillón

- **Dado** un bloqueo del "Sillón 1" de 10:00 a 12:00 del lunes
- **Cuando** se crea un turno en el "Sillón 1" a las 11:00, otro en el "Sillón 2" a las 11:00 y otro en el "Sillón 1" a las 12:00
- **Entonces** el primero responde `409` con `codigo` `dentro_de_bloqueo` y los otros dos responden `201`

#### Scenario: Turno dentro de un bloqueo del profesional

- **Dado** un bloqueo de "Odontólogo Ficticio A" que cubre todo el lunes por vacaciones
- **Cuando** se crea un turno de ese profesional el lunes a las 10:00
- **Entonces** responde `409` con `codigo` `dentro_de_bloqueo`

### Requirement: Rechazo por dato inválido

El sistema SHALL rechazar con `422` y `codigo` `dato_invalido` el alta de un turno sin `sillon_id` (RN-TUR-02), con un profesional, sillón o prestación inexistente o inactivo (RN-REC-03), con un paciente inexistente o con un `inicio` que trae zona horaria u offset. En todos los casos MUST NOT persistirse ni el turno ni su auditoría.

#### Scenario: Falta el sillón

- **Dado** un usuario `recepcion` autenticado y un contexto válido
- **Cuando** envía `POST /turnos` sin `sillon_id`
- **Entonces** responde `422` con `codigo` `dato_invalido` y un elemento de `detalles` con `campo` igual a `sillon_id`

#### Scenario: Sillón inactivo

- **Dado** el "Sillón 2" dado de baja (`activo = false`)
- **Cuando** se crea un turno en el "Sillón 2" en un horario libre
- **Entonces** responde `422` con `codigo` `dato_invalido` y un mensaje en español, y no se crea ningún turno

#### Scenario: Profesional inactivo o prestación inactiva

- **Dado** un profesional dado de baja, o una prestación dada de baja
- **Cuando** se crea un turno con ese profesional o con esa prestación
- **Entonces** responde `422` con `codigo` `dato_invalido`

#### Scenario: Recurso inexistente

- **Dado** un contexto válido
- **Cuando** se crea un turno con un `paciente_id`, `profesional_id`, `sillon_id` o `prestacion_id` que no existe
- **Entonces** responde `422` con `codigo` `dato_invalido`

#### Scenario: Inicio con zona horaria

- **Dado** un contexto válido
- **Cuando** se crea un turno con `inicio = "2026-01-12T10:00:00-03:00"` (o con sufijo `Z`)
- **Entonces** responde `422` con `codigo` `dato_invalido` y un elemento de `detalles` con `campo` igual a `inicio`

### Requirement: Doble reserva del mismo hueco

La verificación de disponibilidad y la inserción del turno SHALL ocurrir en una única transacción de escritura, de modo que de dos reservas del mismo hueco solo una se confirme y la otra responda `409` (SE-06). Ningún rol MUST poder forzar un solapamiento (RN-TUR-11).

#### Scenario: La segunda reserva del mismo hueco se rechaza

- **Dado** dos usuarios `recepcion` autenticados y un hueco libre del lunes a las 10:00
- **Cuando** ambos envían `POST /turnos` para el mismo profesional, sillón e `inicio`, uno después del otro
- **Entonces** el primero responde `201` y el segundo responde `409` con `codigo` `conflicto_agenda`

#### Scenario: Solo queda un turno y una auditoría

- **Dado** las dos reservas del escenario anterior
- **Cuando** se cuentan los registros de `turno` y de auditoría
- **Entonces** hay un único turno para ese hueco y un único registro de auditoría `crear`

#### Scenario: Administración tampoco puede superponer

- **Dado** un turno reservado de "Odontólogo Ficticio A" de 10:00 a 10:30
- **Cuando** un usuario `administracion` crea otro turno del mismo profesional a las 10:00
- **Entonces** responde `409` con `codigo` `conflicto_agenda`

### Requirement: Permisos para crear turnos

`POST /turnos` SHALL exigir autenticación (`401` con `codigo` `no_autenticado` sin token válido) y SHALL admitir solo los roles `administracion` y `recepcion`; un usuario `odontologo` SHALL recibir `403` con `codigo` `sin_permiso` y MUST NOT crear el turno (RN-ACC-01, RN-ACC-02).

#### Scenario: Odontólogo intenta crear un turno

- **Dado** un usuario `odontologo` autenticado y asociado a "Odontólogo Ficticio A"
- **Cuando** envía `POST /turnos` con datos válidos para su propio profesional
- **Entonces** responde `403` con `codigo` `sin_permiso` y no se crea ningún turno ni auditoría

#### Scenario: Sin token

- **Dado** la aplicación iniciada
- **Cuando** se envía `POST /turnos` sin cabecera `Authorization`
- **Entonces** responde `401` con `codigo` `no_autenticado`

#### Scenario: Recepción tiene permiso

- **Dado** un usuario `recepcion` autenticado
- **Cuando** envía `POST /turnos` con datos válidos
- **Entonces** responde `201`

### Requirement: Consulta de turno por id

El sistema SHALL exponer `GET /turnos/{id}` para usuarios autenticados, respondiendo `200` con `id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin` (hora local sin offset) y `estado`. Si el turno no existe SHALL responder `404` con `codigo` `no_encontrado`; sin token, `401` (RN-ACC-01).

#### Scenario: Recepción consulta un turno existente

- **Dado** un turno reservado y un usuario `recepcion` autenticado
- **Cuando** envía `GET /turnos/{id}`
- **Entonces** responde `200` con los datos del turno y `estado = "reservado"`

#### Scenario: Turno inexistente

- **Dado** un usuario `administracion` autenticado
- **Cuando** envía `GET /turnos/9999` para un id que no existe
- **Entonces** responde `404` con `codigo` `no_encontrado` y un mensaje en español

#### Scenario: Consulta sin token

- **Dado** un turno existente
- **Cuando** se envía `GET /turnos/1` sin cabecera `Authorization`
- **Entonces** responde `401` con `codigo` `no_autenticado`

### Requirement: El odontólogo solo ve sus propios turnos

Un usuario `odontologo` SHALL poder consultar con `GET /turnos/{id}` solo los turnos de su propio profesional; un turno de otro profesional SHALL responder `403` con `codigo` `sin_permiso` (RN-ACC-03). `administracion` y `recepcion` SHALL poder consultar cualquier turno.

#### Scenario: Odontólogo consulta un turno propio

- **Dado** un usuario `odontologo` asociado a "Odontólogo Ficticio A" y un turno de ese profesional
- **Cuando** envía `GET /turnos/{id}`
- **Entonces** responde `200` con el turno

#### Scenario: Odontólogo consulta un turno de otro profesional

- **Dado** un usuario `odontologo` asociado a "Odontólogo Ficticio A" y un turno de "Odontóloga Ficticia B"
- **Cuando** envía `GET /turnos/{id}`
- **Entonces** responde `403` con `codigo` `sin_permiso` y no expone datos del turno

#### Scenario: Administración consulta un turno de cualquier profesional

- **Dado** un usuario `administracion` y un turno de "Odontóloga Ficticia B"
- **Cuando** envía `GET /turnos/{id}`
- **Entonces** responde `200`
