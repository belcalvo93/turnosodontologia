# Spec Delta

## ADDED Requirements

### Requirement: 409 por username duplicado

Los conflictos de unicidad del `username` de un usuario SHALL responder `409` con `codigo` `username_duplicado` y un `mensaje` en español que indique el conflicto sin repetir el valor recibido. El cuerpo MUST NOT exponer el mensaje del error de SQLite ni el nombre de la restricción.

#### Scenario: Alta de un usuario con username ya existente

- **Dado** un usuario existente con un `username` determinado
- **Cuando** se intenta crear otro usuario con ese mismo `username`
- **Entonces** responde `409` con `codigo` igual a `username_duplicado` y un `mensaje` en español que no contiene el username, sin claves adicionales del motor de base de datos
