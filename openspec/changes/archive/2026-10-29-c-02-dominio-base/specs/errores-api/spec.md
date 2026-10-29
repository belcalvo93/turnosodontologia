# Spec Delta

## MODIFIED Requirements

### Requirement: 409 conflicto de agenda

Los errores de dominio de agenda SHALL responder `409` con el mensaje en español del error de dominio y un código por tipo: `conflicto_agenda` (solapamiento), `fuera_de_horario` (fuera de la franja de atención), `dentro_de_bloqueo` (dentro de un bloqueo) y `turno_no_modificable` (intento de cancelar o reprogramar un turno pasado, en curso o ya cancelado).

#### Scenario: Código 409 por solapamiento

- **Dado** una operación que detecta un solapamiento con otro turno activo
- **Cuando** se responde el request
- **Entonces** responde `409` con `codigo` igual a `conflicto_agenda` y el `mensaje` en español del error de dominio

#### Scenario: Código 409 fuera de horario

- **Dado** una operación que detecta un turno fuera del horario de atención
- **Cuando** se responde el request
- **Entonces** responde `409` con `codigo` igual a `fuera_de_horario`

#### Scenario: Código 409 dentro de un bloqueo

- **Dado** una operación que detecta un turno dentro de un bloqueo
- **Cuando** se responde el request
- **Entonces** responde `409` con `codigo` igual a `dentro_de_bloqueo`

#### Scenario: Código 409 por turno no modificable

- **Dado** una operación que rechaza modificar un turno con `TurnoNoModificable`
- **Cuando** se responde el request
- **Entonces** responde `409` con `codigo` igual a `turno_no_modificable` y el `mensaje` en español del error de dominio
