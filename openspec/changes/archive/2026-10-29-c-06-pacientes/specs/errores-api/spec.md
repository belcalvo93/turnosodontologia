# Spec Delta

## ADDED Requirements

### Requirement: 409 por DNI duplicado

Los conflictos de unicidad del DNI de un paciente SHALL responder `409` con `codigo` `dni_duplicado` y un `mensaje` en español que indique el conflicto sin repetir el valor recibido. El cuerpo MUST NOT exponer el mensaje del error de SQLite ni el nombre de la restricción.

#### Scenario: Alta de un paciente con DNI ya existente

- **Dado** un paciente existente con un DNI determinado
- **Cuando** se intenta crear otro paciente con ese mismo DNI
- **Entonces** responde `409` con `codigo` igual a `dni_duplicado` y un `mensaje` en español que no contiene el DNI, sin claves adicionales del motor de base de datos

#### Scenario: Edición de un paciente con el DNI de otro

- **Dado** dos pacientes existentes con DNI distintos
- **Cuando** se intenta cambiar el DNI de uno por el del otro
- **Entonces** responde `409` con `codigo` igual a `dni_duplicado` y un `mensaje` en español que no contiene el DNI
