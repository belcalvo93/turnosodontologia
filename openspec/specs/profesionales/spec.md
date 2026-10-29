# profesionales Specification

## Purpose
Gestión del catálogo de profesionales odontológicos del consultorio: permite dar de alta, consultar, editar parcialmente y desactivar lógicamente profesionales con control de acceso por rol, conservando los profesionales inactivos en el listado e historial.

## Requirements

### Requirement: Alta de profesional

El sistema SHALL permitir al rol `administracion` crear un profesional mediante `POST /profesionales` indicando `nombre` y `apellido` obligatorios no vacíos y `matricula` opcional. El profesional creado SHALL quedar con `activo = true` y un identificador entero asignado, respondiendo `201`. Si `nombre` o `apellido` están vacíos o contienen solo espacios en blanco, el sistema SHALL rechazar la operación con `422`.

#### Scenario: Alta válida con matrícula opcional

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /profesionales` con `nombre`, `apellido` y `matricula` válidos
- **Entonces** el sistema responde `201` con el profesional creado incluyendo `id`, `nombre`, `apellido`, `matricula` y `activo = true`

#### Scenario: Alta válida sin matrícula

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /profesionales` con `nombre` y `apellido` válidos y sin `matricula`
- **Entonces** el sistema responde `201` con `matricula = null` y `activo = true`

#### Scenario: Rechazo por nombre o apellido vacío

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /profesionales` con `nombre` vacío o compuesto solo por espacios en blanco
- **Entonces** el sistema responde `422` con un mensaje de error en español y no persiste ningún registro

### Requirement: Listado de profesionales activos e inactivos

El sistema SHALL exponer `GET /profesionales` para cualquier usuario autenticado (`administracion`, `recepcion` u `odontologo`), devolviendo `200` con la lista de todos los profesionales registrados, tanto activos como desactivados, indicando su estado `activo`.

#### Scenario: Listado incluye profesionales desactivados como inactivos

- **Dado** un profesional activo y un profesional previamente desactivado con `activo = false`
- **Cuando** un usuario autenticado consulta `GET /profesionales`
- **Entonces** el sistema responde `200` incluyendo ambos profesionales en la lista, con `activo = true` para el primero y `activo = false` para el desactivado

### Requirement: Edición parcial y desactivación lógica de profesional

El sistema SHALL permitir al rol `administracion` actualizar parcialmente un profesional mediante `PATCH /profesionales/{id}` modificando `nombre`, `apellido`, `matricula` y/o `activo` (incluyendo desactivar con `activo = false` sin borrar físicamente el registro), respondiendo `200`. Si el `id` no existe, SHALL responder `404`. Si se envía `nombre` o `apellido` vacío, SHALL responder `422`.

#### Scenario: Desactivación lógica conserva el registro

- **Dado** un profesional existente con `activo = true` y un usuario con rol `administracion`
- **Cuando** envía `PATCH /profesionales/{id}` con `{"activo": false}`
- **Entonces** el sistema responde `200` con `activo = false` y el profesional continúa existiendo al listar `GET /profesionales`

#### Scenario: Edición de profesional inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `PATCH /profesionales/9999` para un identificador que no existe
- **Entonces** el sistema responde `404` con un mensaje de error en español

### Requirement: Control de acceso por rol en profesionales

El sistema SHALL exigir autenticación en todas las rutas de `/profesionales` (`401` sin token válido) y SHALL restringir las operaciones de escritura (`POST /profesionales` y `PATCH /profesionales/{id}`) exclusivamente al rol `administracion`, respondiendo `403` cuando un usuario con rol `recepcion` u `odontologo` intente crear o modificar un profesional.

#### Scenario: Recepción intenta crear un profesional

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /profesionales` con datos válidos
- **Entonces** el sistema responde `403` con un mensaje de error en español y no crea el profesional

#### Scenario: Odontólogo intenta modificar un profesional

- **Dado** un usuario autenticado con rol `odontologo` y un profesional existente
- **Cuando** envía `PATCH /profesionales/{id}` con `{"activo": false}`
- **Entonces** el sistema responde `403` con un mensaje de error en español y el profesional no se modifica

#### Scenario: Consulta sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `GET /profesionales`
- **Entonces** el sistema responde `401`
