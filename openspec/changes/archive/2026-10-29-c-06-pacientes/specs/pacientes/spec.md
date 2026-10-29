# Spec Delta

## Purpose

Gestión del padrón de pacientes del consultorio: permite dar de alta, consultar y editar parcialmente pacientes con nombre, apellido y DNI obligatorios, datos de contacto y cobertura opcionales, y DNI único, sin liquidación de obras sociales ni baja lógica.

## ADDED Requirements

### Requirement: Alta de paciente

El sistema SHALL permitir a los roles `administracion` y `recepcion` crear un paciente mediante `POST /pacientes` con `nombre`, `apellido` y `dni` obligatorios y no vacíos, y `telefono`, `obra_social` y `nro_afiliado` opcionales, respondiendo `201` con su `id` asignado. Los obligatorios vacíos o solo con espacios SHALL responder `422`; un DNI ya usado SHALL responder `409` con `codigo` `dni_duplicado` y no persistir el registro.

#### Scenario: Alta válida con obra social y número de afiliado

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /pacientes` con `nombre`, `apellido`, `dni`, `telefono`, `obra_social` y `nro_afiliado` válidos
- **Entonces** el sistema responde `201` con el paciente creado, sus datos normalizados y su `id`

#### Scenario: Alta válida sin datos opcionales

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /pacientes` con solo `nombre`, `apellido` y `dni`
- **Entonces** el sistema responde `201` con `telefono`, `obra_social` y `nro_afiliado` en `null`

#### Scenario: Normalización del DNI con espacios laterales

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /pacientes` con `dni` rodeado de espacios
- **Entonces** el sistema responde `201` y devuelve el DNI sin espacios laterales

#### Scenario: Nombre de paciente vacío

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /pacientes` con `nombre` vacío o compuesto solo por espacios
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el paciente

#### Scenario: Apellido de paciente vacío

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /pacientes` con `apellido` vacío o compuesto solo por espacios
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el paciente

#### Scenario: DNI vacío

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /pacientes` con `dni` vacío o compuesto solo por espacios
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el paciente

#### Scenario: DNI duplicado

- **Dado** un paciente existente con un DNI determinado y un usuario con rol `recepcion`
- **Cuando** envía `POST /pacientes` con ese mismo DNI
- **Entonces** el sistema responde `409` con `codigo` `dni_duplicado`, un `mensaje` en español que no repite el DNI y no persiste un segundo paciente

#### Scenario: Número de afiliado sin obra social

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /pacientes` con `nro_afiliado` pero sin `obra_social`
- **Entonces** el sistema responde `201` y guarda el número de afiliado como dato libre

### Requirement: Listado de pacientes

El sistema SHALL exponer `GET /pacientes` para los roles `administracion` y `recepcion`, devolviendo `200` con todos los pacientes ordenados por `id`. El rol `odontologo` SHALL recibir `403` con `codigo` `sin_permiso` hasta que exista la lectura acotada a sus turnos.

#### Scenario: Listado de pacientes ordenado por id

- **Dado** dos pacientes existentes y un usuario con rol `administracion`
- **Cuando** consulta `GET /pacientes`
- **Entonces** el sistema responde `200` con ambos pacientes ordenados por `id`

#### Scenario: Recepción consulta el listado

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** consulta `GET /pacientes`
- **Entonces** el sistema responde `200` con el paciente

#### Scenario: Odontología consulta el listado

- **Dado** un usuario autenticado con rol `odontologo`
- **Cuando** consulta `GET /pacientes`
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso`

### Requirement: Edición parcial de paciente

El sistema SHALL permitir a `administracion` y `recepcion` actualizar parcialmente un paciente mediante `PATCH /pacientes/{id}`, respondiendo `200`. `null` en `nombre`, `apellido` o `dni` SHALL responder `422` sin modificar el paciente; `null` en `telefono`, `obra_social` o `nro_afiliado` SHALL limpiar el dato con `200`. Un `id` inexistente SHALL responder `404` y un DNI ya usado `409`.

#### Scenario: Edición de nombre, apellido y DNI

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `nombre`, `apellido` y `dni` nuevos y válidos
- **Entonces** el sistema responde `200` con los datos actualizados

#### Scenario: Edición de datos opcionales

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `telefono`, `obra_social` y `nro_afiliado` nuevos
- **Entonces** el sistema responde `200` y devuelve los tres valores actualizados

#### Scenario: Limpieza del teléfono

- **Dado** un paciente existente con teléfono y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"telefono": null}`
- **Entonces** el sistema responde `200` con `telefono` en `null`

#### Scenario: Limpieza de la obra social

- **Dado** un paciente existente con obra social y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"obra_social": null}`
- **Entonces** el sistema responde `200` con `obra_social` en `null`

#### Scenario: Limpieza del número de afiliado

- **Dado** un paciente existente con número de afiliado y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"nro_afiliado": null}`
- **Entonces** el sistema responde `200` con `nro_afiliado` en `null`

#### Scenario: Edición con nombre nulo

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"nombre": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el paciente no se modifica

#### Scenario: Edición con apellido nulo

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"apellido": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el paciente no se modifica

#### Scenario: Edición con DNI nulo

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"dni": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el paciente no se modifica

#### Scenario: Edición con nombre solo de espacios

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"nombre": "   "}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el paciente no se modifica

#### Scenario: Edición con apellido solo de espacios

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"apellido": "   "}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el paciente no se modifica

#### Scenario: Edición con DNI solo de espacios

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con `{"dni": "   "}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el paciente no se modifica

#### Scenario: Edición con el mismo DNI del paciente

- **Dado** un paciente existente con un DNI determinado y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con ese mismo DNI
- **Entonces** el sistema responde `200` con el paciente sin cambios y sin conflicto de unicidad

#### Scenario: Edición con DNI de otro paciente

- **Dado** dos pacientes existentes y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con el DNI del otro paciente
- **Entonces** el sistema responde `409` con `codigo` `dni_duplicado` y el paciente conserva su DNI anterior

#### Scenario: Edición de paciente inexistente

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/9999` para un identificador que no existe
- **Entonces** el sistema responde `404` con `codigo` `no_encontrado` y un `mensaje` en español

### Requirement: Control de acceso por rol en pacientes

El sistema SHALL exigir autenticación en todas las rutas de `/pacientes` (`401` sin token válido). `POST` y `PATCH` SHALL admitir solo a `administracion` y `recepcion`; `odontologo` SHALL recibir `403` con `codigo` `sin_permiso` al intentar crear o editar.

#### Scenario: Recepción crea un paciente

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /pacientes` con datos válidos
- **Entonces** el sistema responde `201`

#### Scenario: Odontología intenta crear un paciente

- **Dado** un usuario autenticado con rol `odontologo`
- **Cuando** envía `POST /pacientes` con datos válidos
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y no crea el paciente

#### Scenario: Recepción edita un paciente

- **Dado** un paciente existente y un usuario con rol `recepcion`
- **Cuando** envía `PATCH /pacientes/{id}` con un cambio válido
- **Entonces** el sistema responde `200`

#### Scenario: Odontología intenta editar un paciente

- **Dado** un paciente existente y un usuario con rol `odontologo`
- **Cuando** envía `PATCH /pacientes/{id}` con un cambio válido
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y el paciente no se modifica

#### Scenario: Consulta de pacientes sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `GET /pacientes`
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`

#### Scenario: Alta de paciente sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `POST /pacientes` con datos válidos
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`

#### Scenario: Edición de paciente sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `PATCH /pacientes/1` con un cambio válido
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`
