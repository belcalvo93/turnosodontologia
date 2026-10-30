# Spec Delta

## ADDED Requirements

### Requirement: Conservación del turno histórico al desactivar un recurso

Un turno SHALL seguir consultable con `GET /turnos/{id}` aunque su profesional o su sillón se desactiven después de la reserva, conservando los `profesional_id` y `sillon_id` originales y su `estado`. La desactivación de un recurso MUST NOT borrar ni modificar turnos existentes ni sus registros de auditoría (RN-REC-03).

#### Scenario: Sillón desactivado después de la reserva

- **Dado** un turno reservado sobre el "Sillón 1" y un usuario `administracion` autenticado
- **Cuando** desactiva ese sillón con `PATCH /sillones/{id}` con `activo = false`
- **Y** consulta `GET /turnos/{id}`
- **Entonces** responde `200` con el turno, `sillon_id` igual al del sillón desactivado y `estado` `reservado`
- **Y** el listado de sillones muestra ese sillón como inactivo

#### Scenario: Profesional desactivado después de la reserva

- **Dado** un turno reservado de un profesional y un usuario `administracion` autenticado
- **Cuando** desactiva a ese profesional con `PATCH /profesionales/{id}` con `activo = false`
- **Y** consulta `GET /turnos/{id}`
- **Entonces** responde `200` con el turno y `profesional_id` igual al del profesional desactivado

#### Scenario: La desactivación no borra auditoría

- **Dado** un turno creado y su registro de auditoría `crear`
- **Cuando** se desactiva el sillón del turno
- **Entonces** el registro de auditoría del turno sigue existiendo sin cambios
