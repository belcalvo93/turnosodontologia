# Spec Delta

## Purpose

Cancelación de turnos futuros: permite a recepción y administración pasar un turno reservado futuro a estado `cancelado` registrando la auditoría antes/después en la misma transacción y liberando el horario para nuevas reservas.

## ADDED Requirements

### Requirement: Validación de turno futuro y activo al cancelar

El sistema SHALL permitir cancelar únicamente turnos en estado `reservado` cuyo `inicio` sea estrictamente posterior al instante actual (`inicio > ahora`) recibido por reloj inyectado. Si el turno ya comenzó (`inicio == ahora`), está en el pasado (`inicio < ahora`) o ya se encuentra en estado `cancelado`, el sistema SHALL rechazar la operación con `409` sin modificar el turno ni agregar registros de auditoría. Si el turno no existe, SHALL responder `404`.

#### Scenario: Cancelación exitosa de un turno futuro

- **Dado** un reloj fijo en `09:00`, un turno en estado `reservado` con inicio a las `10:00` del mismo día y un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /turnos/{id}/cancelar`
- **Entonces** el sistema responde `200` con el turno en estado `cancelado` y registra una entrada de auditoría con `accion = "cancelar"`, valores `antes` (`estado: "reservado"`) y `despues` (`estado: "cancelado"`), el usuario y la fecha/hora

#### Scenario: Rechazo de cancelación de turno pasado o en el instante exacto de inicio

- **Dado** un turno en estado `reservado` con inicio a las `09:00` y un reloj fijo en `09:00` (o en `09:30`)
- **Cuando** un usuario con rol `recepcion` envía `POST /turnos/{id}/cancelar`
- **Entonces** el sistema responde `409` con un mensaje de error en español, el turno conserva el estado `reservado` y no se agrega ningún registro de auditoría

#### Scenario: Rechazo de segunda cancelación sobre un turno ya cancelado

- **Dado** un turno futuro que ya fue cancelado previamente
- **Cuando** un usuario con rol `recepcion` o `administracion` envía nuevamente `POST /turnos/{id}/cancelar`
- **Entonces** el sistema responde `409` con un mensaje de error en español y no agrega un nuevo registro de auditoría

#### Scenario: Cancelación de turno inexistente

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /turnos/9999/cancelar` para un identificador que no existe
- **Entonces** el sistema responde `404` con un mensaje de error en español

### Requirement: Liberación del horario tras cancelar un turno

El sistema SHALL liberar el intervalo horario del profesional, del sillón y del paciente cuando un turno pasa a estado `cancelado`, permitiendo crear un nuevo turno en ese mismo horario y recursos.

#### Scenario: Reservar nuevamente un hueco liberado por cancelación

- **Dado** un turno futuro de `10:00` a `10:30` que es cancelado mediante `POST /turnos/{id}/cancelar`
- **Cuando** recepción envía `POST /turnos` para el mismo profesional, sillón y horario `10:00`
- **Entonces** el sistema acepta la nueva reserva y responde `201` con el nuevo turno en estado `reservado`

### Requirement: Control de acceso por rol en cancelación de turnos

El sistema SHALL exigir autenticación en `POST /turnos/{id}/cancelar` (`401` sin token) y SHALL autorizar únicamente a los roles `administracion` y `recepcion`, respondiendo `403` si un usuario con rol `odontologo` intenta cancelar un turno.

#### Scenario: Odontólogo intenta cancelar un turno

- **Dado** un usuario autenticado con rol `odontologo` y un turno futuro en estado `reservado`
- **Cuando** envía `POST /turnos/{id}/cancelar`
- **Entonces** el sistema responde `403` con un mensaje de error en español y el turno permanece `reservado`
