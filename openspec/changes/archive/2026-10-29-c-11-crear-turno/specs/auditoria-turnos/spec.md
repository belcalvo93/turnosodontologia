# Spec Delta

## Purpose

Trazabilidad de los turnos: cada modificación de un turno (crear, cancelar, reprogramar) deja un registro de solo agregado con quién, qué y cuándo, confirmado o descartado junto con la operación auditada.

## ADDED Requirements

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
