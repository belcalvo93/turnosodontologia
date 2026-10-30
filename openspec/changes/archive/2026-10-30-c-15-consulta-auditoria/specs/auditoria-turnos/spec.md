# Spec Delta

## ADDED Requirements

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
