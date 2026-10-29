# Spec Delta

## Purpose

Gestión del catálogo de sillones/boxes del consultorio: permite dar de alta, consultar, editar parcialmente y desactivar lógicamente sillones con nombre único, conservando los sillones inactivos en el listado para no perder el historial de turnos.

## ADDED Requirements

### Requirement: Alta de sillón

El sistema SHALL permitir al rol `administracion` crear un sillón mediante `POST /sillones` con `nombre` obligatorio, no vacío y único, respondiendo `201` con `activo = true` y su `id` asignado. Un `nombre` vacío o compuesto solo por espacios SHALL responder `422`; un `nombre` ya usado por otro sillón SHALL responder `409` y no persistir el registro.

#### Scenario: Alta válida de sillón

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /sillones` con `{"nombre": "  Sillón 1 (ficticio)  "}`
- **Entonces** el sistema responde `201` con `id`, `nombre` normalizado sin espacios laterales y `activo = true`

#### Scenario: Nombre de sillón duplicado

- **Dado** un sillón existente con nombre `"Sillón 1 (ficticio)"` y un usuario con rol `administracion`
- **Cuando** envía `POST /sillones` con el mismo nombre
- **Entonces** el sistema responde `409` con `codigo` `nombre_duplicado` y no persiste un segundo sillón

#### Scenario: Nombre de sillón vacío

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /sillones` con `nombre` vacío o compuesto solo por espacios
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste ningún registro

### Requirement: Listado de sillones activos e inactivos

El sistema SHALL exponer `GET /sillones` para cualquier usuario autenticado (`administracion`, `recepcion` u `odontologo`), devolviendo `200` con la lista de todos los sillones ordenados por `id`, tanto activos como desactivados, incluyendo el estado `activo` de cada uno.

#### Scenario: Listado incluye sillones desactivados

- **Dado** un sillón activo y un sillón previamente desactivado con `activo = false`
- **Cuando** un usuario autenticado consulta `GET /sillones`
- **Entonces** el sistema responde `200` con ambos sillones, ordenados por `id`, con `activo = true` para el primero y `activo = false` para el desactivado

### Requirement: Edición parcial y desactivación lógica de sillón

El sistema SHALL permitir al rol `administracion` actualizar parcialmente un sillón mediante `PATCH /sillones/{id}` modificando `nombre` y/o `activo` (incluyendo desactivar con `activo = false` sin borrar el registro), respondiendo `200`. Un `id` inexistente SHALL responder `404`; un `nombre` vacío `422`; un `nombre` ya usado por otro sillón `409`.

#### Scenario: Desactivación lógica conserva el sillón

- **Dado** un sillón existente con `activo = true` y un usuario con rol `administracion`
- **Cuando** envía `PATCH /sillones/{id}` con `{"activo": false}`
- **Entonces** el sistema responde `200` con `activo = false` y el sillón continúa existiendo al listar `GET /sillones`

#### Scenario: Renombrar a un nombre ya usado

- **Dado** dos sillones existentes y un usuario con rol `administracion`
- **Cuando** envía `PATCH /sillones/{id}` con el `nombre` del otro sillón
- **Entonces** el sistema responde `409` con `codigo` `nombre_duplicado` y el sillón conserva su nombre anterior

#### Scenario: Edición de sillón inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `PATCH /sillones/9999` para un identificador que no existe
- **Entonces** el sistema responde `404` con `codigo` `no_encontrado` y un `mensaje` en español

#### Scenario: Edición con nombre vacío

- **Dado** un sillón existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /sillones/{id}` con `{"nombre": "   "}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el sillón no se modifica

#### Scenario: Edición con nombre nulo

- **Dado** un sillón existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /sillones/{id}` con `{"nombre": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el sillón no se modifica

### Requirement: Control de acceso por rol en sillones

El sistema SHALL exigir autenticación en todas las rutas de `/sillones` (`401` sin token válido) y SHALL restringir `POST /sillones` y `PATCH /sillones/{id}` exclusivamente al rol `administracion`, respondiendo `403` cuando recepción u odontología intente crear o modificar. `GET /sillones` SHALL admitir a los tres roles autenticados.

#### Scenario: Recepción intenta crear un sillón

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /sillones` con un nombre válido
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y no crea el sillón

#### Scenario: Odontología intenta modificar un sillón

- **Dado** un usuario autenticado con rol `odontologo` y un sillón existente
- **Cuando** envía `PATCH /sillones/{id}` con `{"activo": false}`
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y el sillón no se modifica

#### Scenario: Consulta de sillones sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `GET /sillones`
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`
