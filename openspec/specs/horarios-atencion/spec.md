# horarios-atencion Specification

## Purpose

Gestión de horarios de atención semanales por profesional: permite dar de alta franjas horarias válidas y consultar la agenda de atención semanal respetando la matriz de permisos por rol.

## Requirements

### Requirement: Alta de franja de horario de atención

El sistema SHALL permitir al rol `administracion` crear una franja horaria de atención para un profesional mediante `POST /profesionales/{id}/horarios` especificando `dia_semana` (entero entre 0 y 6), `hora_desde` y `hora_hasta` en formato HH:MM. Si `hora_desde >= hora_hasta`, si `dia_semana` no está en 0..6 o si la franja se superpone con otra franja existente del mismo profesional en ese día, el sistema SHALL rechazar la operación con `422` `dato_invalido`. Si el profesional indicado no existe, el sistema SHALL responder `422` `dato_invalido`.

#### Scenario: Alta válida de franja horaria

- **Dado** un usuario autenticado con rol `administracion` y un profesional existente
- **Cuando** envía `POST /profesionales/{id}/horarios` con `dia_semana = 0`, `hora_desde = "09:00"` y `hora_hasta = "13:00"`
- **Entonces** el sistema responde `201` con la franja creada conteniendo su identificador y los datos normalizados

#### Scenario: Franja invertida o con inicio igual a fin es rechazada

- **Dado** un usuario autenticado con rol `administracion` y un profesional existente
- **Cuando** envía `POST /profesionales/{id}/horarios` con `hora_desde = "13:00"` y `hora_hasta = "09:00"`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste la franja

#### Scenario: Franja superpuesta en el mismo día es rechazada

- **Dado** un profesional con una franja existente el día lunes (0) de `09:00` a `13:00`
- **Cuando** administración envía `POST /profesionales/{id}/horarios` para el día lunes de `12:00` a `15:00`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste la franja

#### Scenario: Dos franjas en el mismo día disjuntas o contiguas son aceptadas

- **Dado** un profesional con una franja existente el día lunes (0) de `09:00` a `13:00`
- **Cuando** administración envía `POST /profesionales/{id}/horarios` para el día lunes de `14:00` a `18:00`
- **Entonces** el sistema responde `201` y ambas franjas quedan registradas

#### Scenario: Alta para profesional inexistente devuelve 422

- **Dado** un identificador de profesional que no existe en el sistema
- **Cuando** administración envía `POST /profesionales/9999/horarios` con datos de horario válidos
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido`

### Requirement: Consulta de horarios de atención por profesional

El sistema SHALL permitir consultar los horarios de atención de un profesional mediante `GET /profesionales/{id}/horarios`. Los roles `administracion` y `recepcion` SHALL poder consultar los horarios de cualquier profesional. El rol `odontologo` SHALL poder consultar únicamente los horarios donde `profesional_id` coincida con su propio `usuario.profesional_id`, respondiendo `403` `sin_permiso` si intenta consultar los de otro profesional.

#### Scenario: Odontólogo consulta sus propios horarios

- **Dado** un usuario autenticado con rol `odontologo` vinculado al profesional con `id = 1`
- **Cuando** envía `GET /profesionales/1/horarios`
- **Entonces** el sistema responde `200` con la lista de sus franjas de atención

#### Scenario: Odontólogo intenta consultar horarios de otro profesional

- **Dado** un usuario autenticado con rol `odontologo` vinculado al profesional con `id = 1`
- **Cuando** envía `GET /profesionales/2/horarios`
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso`

#### Scenario: Recepción consulta horarios de cualquier profesional

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `GET /profesionales/1/horarios`
- **Entonces** el sistema responde `200` con las franjas de atención del profesional

#### Scenario: Consulta sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `GET /profesionales/1/horarios`
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`
