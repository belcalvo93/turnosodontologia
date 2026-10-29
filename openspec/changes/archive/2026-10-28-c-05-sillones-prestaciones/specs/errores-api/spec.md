# Spec Delta

## ADDED Requirements

### Requirement: 409 por nombre duplicado

Los conflictos de unicidad de `nombre` SHALL responder `409` con `codigo` `nombre_duplicado` y un `mensaje` en español que indique el recurso afectado. El cuerpo MUST NOT exponer el mensaje del error de SQLite ni el nombre de la restricción.

#### Scenario: Alta de un recurso con nombre ya existente

- **Dado** un sillón o una prestación existente con un `nombre` determinado
- **Cuando** se intenta crear otro registro del mismo recurso con ese `nombre`
- **Entonces** responde `409` con `codigo` igual a `nombre_duplicado` y un `mensaje` en español, sin claves adicionales del motor de base de datos
