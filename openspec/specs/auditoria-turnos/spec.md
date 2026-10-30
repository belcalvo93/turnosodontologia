# auditoria-turnos Specification

## Purpose

Trazabilidad de los turnos: cada modificación de un turno (crear, cancelar, reprogramar) deja un registro de solo agregado con quién, qué y cuándo, confirmado o descartado junto con la operación auditada.

## Requirements

### Requirement: Auditoría del alta de un turno

Cada alta confirmada de un turno SHALL registrar exactamente un registro de auditoría con `accion = "crear"`, el `turno_id` creado, el `usuario_id` del usuario autenticado que operó, `ocurrio_en` (fecha y hora de la operación), `antes` nulo y `despues` con el snapshot del turno creado (RN-AUD-01). El turno SHALL guardar además quién lo creó (`creado_por`) y cuándo (`creado_en`).

#### Scenario: Alta registrada con usuario y fecha

- **Dado** un usuario `recepcion` autenticado y el reloj de la aplicación fijado en `2026-01-05T12:00:00Z`
- **Cuando** crea un turno válido con `POST /turnos`
- **Entonces** existe un único registro de auditoría para ese turno con `accion = "crear"`, `usuario_id` igual al id del usuario de recepción y `ocurrio_en = "2026-01-05T09:00:00"`

#### Scenario: Antes nulo y después con el turno creado

- **Dado** el registro de auditoría del escenario anterior
- **Cuando** se leen `antes` y `despues`
- **Entonces** `antes` es nulo y `despues` describe el turno creado con su `id`, recursos, `inicio`, `fin` y `estado = "reservado"`

#### Scenario: El turno guarda su creador

- **Dado** un turno creado por un usuario `administracion` con el reloj fijado en `2026-01-05T12:00:00Z`
- **Cuando** se lee su fila en la base
- **Entonces** `creado_por` es el id de ese usuario y `creado_en = "2026-01-05T09:00:00"`

### Requirement: Fechas de auditoría en hora local del consultorio

`ocurrio_en` y `creado_en` SHALL guardarse como texto ISO 8601 en hora local de la zona `CLINIC_TIMEZONE`, con precisión de segundos y sin offset (KB 04 §Convenciones), derivados del reloj inyectado de la aplicación y no de la hora real del sistema.

#### Scenario: Conversión de UTC a hora local

- **Dado** `CLINIC_TIMEZONE = "America/Argentina/Buenos_Aires"` y el reloj fijado en `2026-01-05T12:00:00Z`
- **Cuando** se crea un turno
- **Entonces** `ocurrio_en` es `"2026-01-05T09:00:00"`

#### Scenario: Cambio de día al convertir

- **Dado** la misma zona y el reloj fijado en `2026-01-06T02:30:00Z`
- **Cuando** se crea un turno
- **Entonces** `ocurrio_en` es `"2026-01-05T23:30:00"`

#### Scenario: Sin offset en el texto guardado

- **Dado** cualquier turno creado
- **Cuando** se leen `ocurrio_en` y `creado_en`
- **Entonces** ninguno contiene `+`, `Z` ni un offset `-HH:MM` y ambos tienen el formato `YYYY-MM-DDTHH:MM:SS`

### Requirement: Formato canónico del snapshot

`antes` y `despues` SHALL ser texto JSON con un objeto que tiene exactamente las claves `id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin` y `estado`, con `inicio` y `fin` en hora local sin offset (`YYYY-MM-DDTHH:MM:SS`). Toda acción auditada (`crear`, `cancelar`, `reprogramar`) MUST usar este mismo formato.

#### Scenario: Claves exactas del snapshot

- **Dado** un turno creado
- **Cuando** se decodifica el JSON de `despues` de su auditoría `crear`
- **Entonces** el objeto tiene exactamente las ocho claves del formato canónico, sin claves adicionales

#### Scenario: Valores coinciden con el turno

- **Dado** un turno creado de 10:00 a 10:30 del 2026-01-12
- **Cuando** se decodifica `despues`
- **Entonces** `inicio = "2026-01-12T10:00:00"`, `fin = "2026-01-12T10:30:00"`, `estado = "reservado"` y los ids coinciden con los de `GET /turnos/{id}`

#### Scenario: El snapshot no incluye datos personales

- **Dado** un turno de un paciente ficticio
- **Cuando** se lee `despues`
- **Entonces** el snapshot contiene solo ids, fechas y estado, sin datos personales del paciente

### Requirement: Auditoría atómica con la operación

El registro de auditoría y el cambio del turno SHALL confirmarse o descartarse juntos en la misma transacción. Si la operación se rechaza (`409`, `422`) o falla la escritura de la auditoría, MUST NOT quedar ni el turno ni el registro de auditoría (RN-AUD-03).

#### Scenario: Rechazo 409 sin auditoría

- **Dado** un turno reservado de 10:00 a 10:30 y su único registro de auditoría
- **Cuando** se intenta crear otro turno del mismo profesional a las 10:15 y responde `409`
- **Entonces** la cantidad de turnos y de registros de auditoría no cambia

#### Scenario: Rechazo 422 sin auditoría

- **Dado** una base sin turnos
- **Cuando** se intenta crear un turno con un sillón inactivo y responde `422`
- **Entonces** no existe ningún turno ni ningún registro de auditoría

#### Scenario: Falla al escribir la auditoría

- **Dado** una transacción que inserta un turno válido
- **Cuando** la inserción de su registro de auditoría falla (por ejemplo, por un `usuario_id` inexistente)
- **Entonces** la transacción se revierte y el turno no queda persistido

### Requirement: Auditoría de solo agregado

Los registros de auditoría de turnos SHALL poder solo insertarse: la base MUST rechazar todo `UPDATE` o `DELETE` sobre ellos y la API MUST NOT exponer operaciones para editarlos o borrarlos (RN-AUD-02).

#### Scenario: La base rechaza la modificación

- **Dado** un registro de auditoría existente
- **Cuando** se ejecuta un `UPDATE` sobre él
- **Entonces** la base rechaza la sentencia con error de integridad y el registro queda igual

#### Scenario: La base rechaza el borrado

- **Dado** un registro de auditoría existente
- **Cuando** se ejecuta un `DELETE` sobre él
- **Entonces** la base rechaza la sentencia con error de integridad y el registro sigue existiendo

#### Scenario: Sin rutas de escritura de auditoría

- **Dado** la aplicación iniciada y un usuario `administracion` autenticado
- **Cuando** envía `PUT`, `PATCH` o `DELETE` a una ruta de auditoría de turnos
- **Entonces** responde `404` o `405` y los registros no cambian

### Requirement: Consulta del historial de auditoría de un turno

El sistema SHALL permitir al rol `administracion` consultar el historial de auditoría de un turno con `GET /auditoria?turno_id=`. La respuesta SHALL incluir todos los registros del turno en orden cronológico ascendente por `ocurrio_en` y, ante empate, por `id`.

#### Scenario: Historial de un turno creado, reprogramado y cancelado

- **Dado** un turno creado, luego reprogramado y luego cancelado por el mismo usuario `administracion`
- **Cuando** se consulta `GET /auditoria?turno_id={id}`
- **Entonces** responde `200` con exactamente 3 registros, en orden `crear`, `reprogramar` y `cancelar`

#### Scenario: Turno sin más registros que el alta

- **Dado** un turno recién creado, sin reprogramaciones ni cancelación
- **Cuando** se consulta su historial
- **Entonces** responde `200` con exactamente 1 registro de acción `crear`

#### Scenario: Un turno cancelado conserva su historial completo

- **Dado** un turno cancelado que antes fue creado y reprogramado
- **Cuando** se consulta su historial
- **Entonces** responde `200` con los 3 registros, incluido el de la cancelación

### Requirement: Contrato de cada registro de auditoría

Cada registro SHALL exponer `id`, `turno_id`, `accion`, `usuario_id`, `username`, `ocurrio_en`, `antes` y `despues`. `antes` y `despues` SHALL ser objetos JSON parseados, no texto escapado. `antes` MUST ser `null` solo en la acción `crear`; `despues` MUST ser siempre un objeto con la forma canónica del snapshot.

#### Scenario: Antes y después como objetos JSON

- **Dado** un turno con historial
- **Cuando** se consulta su auditoría
- **Entonces** cada registro devuelve `antes` y `despues` como objetos, y `despues` tiene las claves `id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin` y `estado`

#### Scenario: Antes nulo solo en el alta

- **Dado** un turno creado y luego cancelado
- **Cuando** se consulta su auditoría
- **Entonces** el registro `crear` tiene `antes` nulo y el registro `cancelar` tiene `antes` y `despues` como objetos

#### Scenario: La reprogramación describe el cambio

- **Dado** un turno reprogramado a otro horario
- **Cuando** se consulta el registro `reprogramar`
- **Entonces** `antes.id` y `despues.id` son el mismo `turno_id`, y el `inicio` de `despues` difiere del de `antes`

### Requirement: Identificación del usuario sin datos sensibles

La respuesta SHALL identificar a quien operó con `usuario_id` y `username`, obtenidos de modo que un usuario desactivado siga apareciendo. MUST NOT incluir `password_hash`, `password`, el `rol` del usuario ni datos personales del paciente (`nombre`, `apellido`, `dni`).

#### Scenario: Nunca se expone el hash de la contraseña

- **Dado** un turno con historial y un usuario con contraseña hasheada
- **Cuando** se consulta su auditoría
- **Entonces** la respuesta no contiene `password_hash` ni `password`

#### Scenario: Un usuario desactivado sigue identificado

- **Dado** un registro de auditoría cuyo usuario fue desactivado después de operar
- **Cuando** se consulta el historial del turno
- **Entonces** el registro sigue devolviendo el `usuario_id` y el `username` de ese usuario

#### Scenario: Sin datos del paciente en el snapshot

- **Dado** un turno de un paciente ficticio
- **Cuando** se consulta su auditoría
- **Entonces** `antes` y `despues` contienen solo ids, fechas y estado, sin `nombre`, `apellido` ni `dni`

### Requirement: Turno obligatorio y existencia del turno

`turno_id` SHALL ser obligatorio y entero positivo. Si falta, es `0`, negativo o no entero, la API SHALL responder `422`. Si el turno no existe, SHALL responder `404` con `codigo` `no_encontrado`, sin devolver una lista vacía.

#### Scenario: Sin turno_id

- **Dado** un usuario `administracion` autenticado
- **Cuando** consulta `GET /auditoria` sin `turno_id`
- **Entonces** responde `422` y no devuelve registros

#### Scenario: turno_id no positivo

- **Dado** un usuario `administracion` autenticado
- **Cuando** consulta `GET /auditoria?turno_id=0` o un valor negativo
- **Entonces** responde `422`

#### Scenario: Turno inexistente

- **Dado** un usuario `administracion` autenticado y ningún turno con ese id
- **Cuando** consulta `GET /auditoria?turno_id=999999`
- **Entonces** responde `404` con `codigo` `no_encontrado`

### Requirement: Acceso restringido al historial

La consulta SHALL estar reservada al rol `administracion`. Sin token SHALL responder `401 no_autenticado`; con rol `recepcion` u `odontologo`, `403 sin_permiso`. El control de acceso MUST resolverse antes de revelar si el turno existe.

#### Scenario: Recepción no puede consultar la auditoría

- **Dado** un usuario `recepcion` autenticado
- **Cuando** consulta `GET /auditoria?turno_id=1`
- **Entonces** responde `403` con `codigo` `sin_permiso`

#### Scenario: Odontólogo no puede consultar la auditoría

- **Dado** un usuario `odontologo` autenticado
- **Cuando** consulta `GET /auditoria?turno_id=1`
- **Entonces** responde `403` con `codigo` `sin_permiso`

#### Scenario: Sin token

- **Dado** una petición sin cabecera de autorización
- **Cuando** consulta `GET /auditoria?turno_id=1`
- **Entonces** responde `401` con `codigo` `no_autenticado`

#### Scenario: El rol sin permiso no descubre si el turno existe

- **Dado** un usuario `recepcion` autenticado
- **Cuando** consulta un `turno_id` inexistente
- **Entonces** responde `403` y no `404`
