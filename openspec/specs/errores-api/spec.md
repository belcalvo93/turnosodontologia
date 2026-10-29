# errores-api Specification

## Purpose

Define el contrato único de errores de la API: todo error responde un JSON en español con un código estable y un status HTTP consistente (RN-GLO-01), para que los clientes y los tests no dependan del formato por defecto del framework.

## Requirements

### Requirement: Formato único de error

Toda respuesta de error de la API SHALL tener un cuerpo JSON con `codigo` (texto estable en snake_case), `mensaje` (texto claro en español) y, solo cuando hay errores por campo, `detalles`: una lista de objetos `{campo, mensaje}`. El cuerpo MUST NOT usar la clave `detail` del formato por defecto del framework.

#### Scenario: Error sin detalles por campo

- **Dado** una ruta protegida
- **Cuando** se la llama sin token
- **Entonces** el cuerpo tiene exactamente las claves `codigo` y `mensaje`, con `mensaje` no vacío en español

#### Scenario: Error con detalles por campo

- **Dado** la aplicación iniciada
- **Cuando** se hace `POST /auth/login` con `{}`
- **Entonces** el cuerpo tiene `codigo`, `mensaje` y `detalles`, y `detalles` incluye un elemento para `username` y otro para `password`, cada uno con `campo` y `mensaje`

### Requirement: 401 sin autenticar

Un request sin autenticación válida SHALL responder `401` con la cabecera `WWW-Authenticate: Bearer`. Usa `codigo` `no_autenticado` cuando falta el token o es inválido o vencido, y `credenciales_invalidas` cuando falla el login.

#### Scenario: Código 401 por falta de token

- **Dado** una ruta protegida
- **Cuando** se la llama sin cabecera `Authorization`
- **Entonces** responde `401` con `{"codigo": "no_autenticado", "mensaje": <texto en español>}` y la cabecera `WWW-Authenticate: Bearer`

#### Scenario: Código 401 por login fallido

- **Dado** que no existe el usuario `fantasma_ficticio`
- **Cuando** se hace `POST /auth/login` con ese username
- **Entonces** responde `401` con `{"codigo": "credenciales_invalidas", "mensaje": <texto en español>}` y la cabecera `WWW-Authenticate: Bearer`

### Requirement: 403 rol sin permiso

Un usuario autenticado sin permiso para la operación SHALL recibir `403` con `codigo` `sin_permiso` y un `mensaje` en español.

#### Scenario: Código 403

- **Dado** una ruta protegida que solo admite `administracion`
- **Cuando** la llama un usuario ficticio de rol `recepcion` con token válido
- **Entonces** responde `403` con `{"codigo": "sin_permiso", "mensaje": <texto en español>}`

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

### Requirement: 422 dato inválido

Un dato inválido SHALL responder `422` con `codigo` `dato_invalido`, tanto si lo detecta la validación de entrada como el dominio. Si lo detecta la validación de entrada, `detalles` SHALL indicar cada campo con un mensaje en español.

#### Scenario: Código 422 por validación de entrada

- **Dado** la aplicación iniciada
- **Cuando** se hace `POST /auth/login` con `{"username": "recepcion_ficticia", "password": 123}`
- **Entonces** responde `422` con `codigo` igual a `dato_invalido` y un elemento de `detalles` con `campo` igual a `password` y `mensaje` en español

#### Scenario: Código 422 por regla de dominio

- **Dado** una operación en la que el dominio rechaza un dato inválido
- **Cuando** se responde el request
- **Entonces** responde `422` con `codigo` igual a `dato_invalido` y el `mensaje` en español del error de dominio

### Requirement: 404 y 405 en el mismo formato

Una ruta inexistente SHALL responder `404` con `codigo` `no_encontrado`, y un método no admitido SHALL responder `405` con `codigo` `metodo_no_permitido`, ambos con `mensaje` en español.

#### Scenario: Ruta inexistente

- **Dado** la aplicación iniciada
- **Cuando** se hace `GET /no-existe`
- **Entonces** responde `404` con `codigo` igual a `no_encontrado`

#### Scenario: Método no admitido

- **Dado** la aplicación iniciada
- **Cuando** se hace `GET /auth/login`
- **Entonces** responde `405` con `codigo` igual a `metodo_no_permitido`

### Requirement: 409 por nombre duplicado

Los conflictos de unicidad de `nombre` SHALL responder `409` con `codigo` `nombre_duplicado` y un `mensaje` en español que indique el recurso afectado. El cuerpo MUST NOT exponer el mensaje del error de SQLite ni el nombre de la restricción.

#### Scenario: Alta de un recurso con nombre ya existente

- **Dado** un sillón o una prestación existente con un `nombre` determinado
- **Cuando** se intenta crear otro registro del mismo recurso con ese `nombre`
- **Entonces** responde `409` con `codigo` igual a `nombre_duplicado` y un `mensaje` en español, sin claves adicionales del motor de base de datos

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

### Requirement: 409 por username duplicado

Los conflictos de unicidad del `username` de un usuario SHALL responder `409` con `codigo` `username_duplicado` y un `mensaje` en español que indique el conflicto sin repetir el valor recibido. El cuerpo MUST NOT exponer el mensaje del error de SQLite ni el nombre de la restricción.

#### Scenario: Alta de un usuario con username ya existente

- **Dado** un usuario existente con un `username` determinado
- **Cuando** se intenta crear otro usuario con ese mismo `username`
- **Entonces** responde `409` con `codigo` igual a `username_duplicado` y un `mensaje` en español que no contiene el username, sin claves adicionales del motor de base de datos
