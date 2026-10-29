# Spec Delta

## Purpose

Gestión del catálogo de prestaciones odontológicas: permite dar de alta, consultar, editar parcialmente y desactivar lógicamente prestaciones con nombre único y duración entera en minutos mayor que cero, que es la duración que toma cada turno (RN-TUR-01).

## ADDED Requirements

### Requirement: Alta de prestación

El sistema SHALL permitir al rol `administracion` crear una prestación mediante `POST /prestaciones` con `nombre` obligatorio, no vacío y único, y `duracion_minutos` entero mayor que cero (RN-REC-01), respondiendo `201` con `activa = true` y su `id` asignado. Un `nombre` vacío o una duración menor o igual a cero SHALL responder `422`; un `nombre` duplicado SHALL responder `409` y no persistir el registro.

#### Scenario: Alta válida de prestación

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /prestaciones` con `{"nombre": "  Consulta ficticia  ", "duracion_minutos": 45}`
- **Entonces** el sistema responde `201` con `id`, `nombre` normalizado, `duracion_minutos = 45` y `activa = true`

#### Scenario: Duración cero o negativa

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /prestaciones` con `duracion_minutos` igual a `0` o a un valor negativo
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste la prestación

#### Scenario: Nombre de prestación vacío

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /prestaciones` con `nombre` vacío o compuesto solo por espacios
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste la prestación

#### Scenario: Nombre de prestación duplicado

- **Dado** una prestación existente llamada `"Consulta ficticia"` y un usuario con rol `administracion`
- **Cuando** envía `POST /prestaciones` con el mismo nombre
- **Entonces** el sistema responde `409` con `codigo` `nombre_duplicado` y no persiste una segunda prestación

### Requirement: Listado de prestaciones activas e inactivas

El sistema SHALL exponer `GET /prestaciones` para cualquier usuario autenticado (`administracion`, `recepcion` u `odontologo`), devolviendo `200` con la lista de todas las prestaciones ordenadas por `id`, tanto activas como desactivadas, incluyendo el estado `activa` de cada una.

#### Scenario: Listado incluye prestaciones desactivadas

- **Dado** una prestación activa y una prestación previamente desactivada con `activa = false`
- **Cuando** un usuario autenticado consulta `GET /prestaciones`
- **Entonces** el sistema responde `200` con ambas prestaciones, ordenadas por `id`, con `activa = true` para la primera y `activa = false` para la desactivada

### Requirement: Edición parcial y desactivación lógica de prestación

El sistema SHALL permitir al rol `administracion` actualizar parcialmente una prestación mediante `PATCH /prestaciones/{id}` modificando `nombre`, `duracion_minutos` y/o `activa` (incluyendo desactivar con `activa = false` sin borrar el registro), respondiendo `200`. Un `id` inexistente SHALL responder `404`; un `nombre` vacío o una duración menor o igual a cero `422`; un `nombre` ya usado por otra prestación `409`.

#### Scenario: Desactivación lógica conserva la prestación

- **Dado** una prestación existente con `activa = true` y un usuario con rol `administracion`
- **Cuando** envía `PATCH /prestaciones/{id}` con `{"activa": false}`
- **Entonces** el sistema responde `200` con `activa = false` y la prestación continúa existiendo al listar `GET /prestaciones`

#### Scenario: Cambio de duración inválida

- **Dado** una prestación existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /prestaciones/{id}` con `{"duracion_minutos": 0}` o un valor negativo
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y la prestación conserva su duración anterior

#### Scenario: Renombrar a un nombre ya usado

- **Dado** dos prestaciones existentes y un usuario con rol `administracion`
- **Cuando** envía `PATCH /prestaciones/{id}` con el `nombre` de la otra prestación
- **Entonces** el sistema responde `409` con `codigo` `nombre_duplicado` y la prestación conserva su nombre anterior

#### Scenario: Edición con nombre nulo

- **Dado** una prestación existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /prestaciones/{id}` con `{"nombre": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y la prestación no se modifica

#### Scenario: Edición con duración nula

- **Dado** una prestación existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /prestaciones/{id}` con `{"duracion_minutos": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y la prestación no se modifica

#### Scenario: Edición de prestación inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `PATCH /prestaciones/9999` para un identificador que no existe
- **Entonces** el sistema responde `404` con `codigo` `no_encontrado` y un `mensaje` en español

### Requirement: Control de acceso por rol en prestaciones

El sistema SHALL exigir autenticación en todas las rutas de `/prestaciones` (`401` sin token válido) y SHALL restringir `POST /prestaciones` y `PATCH /prestaciones/{id}` exclusivamente al rol `administracion`, respondiendo `403` cuando recepción u odontología intente crear o modificar. `GET /prestaciones` SHALL admitir a los tres roles autenticados.

#### Scenario: Recepción intenta crear una prestación

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /prestaciones` con nombre y duración válidos
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y no crea la prestación

#### Scenario: Odontología intenta modificar una prestación

- **Dado** un usuario autenticado con rol `odontologo` y una prestación existente
- **Cuando** envía `PATCH /prestaciones/{id}` con `{"activa": false}`
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y la prestación no se modifica

#### Scenario: Consulta de prestaciones sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `GET /prestaciones`
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`
