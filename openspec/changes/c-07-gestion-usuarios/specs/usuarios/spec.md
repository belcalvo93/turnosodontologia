# Spec Delta

## Purpose

Gestión administrativa del padrón de usuarios del consultorio: alta, listado y edición parcial de las cuentas que operan la API (rol, profesional vinculado, estado y contraseña), manteniendo la contraseña solo como hash y la invariante entre rol y profesional.

## ADDED Requirements

### Requirement: Alta de usuario

El sistema SHALL permitir al rol `administracion` crear usuarios con `POST /usuarios`, con `username` y `password` obligatorios y `rol` dentro de `administracion`, `recepcion` u `odontologo`. SHALL responder `201` con `id`, `username`, `rol`, `profesional_id` y `activo`, y MUST NOT incluir `password_hash` ni la contraseña. Un `username` ya usado SHALL responder `409` con `codigo` `username_duplicado` sin persistir el usuario.

#### Scenario: Alta de recepción

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /usuarios` con `username` nuevo, contraseña y `rol` `recepcion`
- **Entonces** el sistema responde `201` con el usuario creado, su `id` y `profesional_id` en `null`

#### Scenario: Alta de odontólogo vinculado a un profesional activo

- **Dado** un profesional activo existente y un usuario con rol `administracion`
- **Cuando** envía `POST /usuarios` con `rol` `odontologo` y el `profesional_id` de ese profesional
- **Entonces** el sistema responde `201` con el usuario creado y el `profesional_id` informado

#### Scenario: Username duplicado

- **Dado** un usuario existente con un `username` determinado y un usuario con rol `administracion`
- **Cuando** envía `POST /usuarios` con ese mismo `username`
- **Entonces** el sistema responde `409` con `codigo` `username_duplicado`, un `mensaje` en español que no repite el username y no persiste un segundo usuario

#### Scenario: Contraseña vacía

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /usuarios` con `password` vacía
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el usuario

#### Scenario: Username vacío o solo con espacios

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /usuarios` con `username` vacío o compuesto solo por espacios
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el usuario

#### Scenario: Rol fuera de los tres roles del MVP

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /usuarios` con `rol` `paciente`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el usuario

#### Scenario: La respuesta no expone el hash

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** crea un usuario con `POST /usuarios`
- **Entonces** el cuerpo de la respuesta `201` no contiene las claves `password` ni `password_hash`

### Requirement: Vínculo obligatorio entre odontólogo y profesional

Un usuario con rol `odontologo` SHALL tener un `profesional_id` que exista y esté activo; si falta, no existe o está inactivo, el sistema SHALL responder `422` con `codigo` `dato_invalido` sin persistir el usuario. Un usuario con cualquier otro rol MUST NOT tener `profesional_id`; si el request lo envía, SHALL responder `422`.

#### Scenario: Odontólogo sin profesional

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /usuarios` con `rol` `odontologo` sin `profesional_id`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el usuario

#### Scenario: Odontólogo con profesional inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /usuarios` con `rol` `odontologo` y un `profesional_id` que no existe
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el usuario

#### Scenario: Odontólogo con profesional inactivo

- **Dado** un profesional inactivo existente y un usuario con rol `administracion`
- **Cuando** envía `POST /usuarios` con `rol` `odontologo` y el `profesional_id` de ese profesional
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el usuario

#### Scenario: Rol sin vínculo con profesional

- **Dado** un profesional activo existente y un usuario con rol `administracion`
- **Cuando** envía `POST /usuarios` con `rol` `recepcion` y un `profesional_id`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y no persiste el usuario

#### Scenario: Usuario administrativo sin profesional

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /usuarios` con `rol` `administracion` y `profesional_id` en `null`
- **Entonces** el sistema responde `201` con `profesional_id` en `null`

### Requirement: Listado de usuarios

El sistema SHALL exponer `GET /usuarios` solo para el rol `administracion`, devolviendo `200` con todos los usuarios, activos e inactivos, ordenados por `id` ascendente. Cada elemento SHALL incluir `id`, `username`, `rol`, `profesional_id` y `activo`; la respuesta MUST NOT incluir `password_hash` ni contraseñas.

#### Scenario: Listado ordenado que incluye inactivos

- **Dado** tres usuarios existentes, uno de ellos inactivo, y un usuario con rol `administracion`
- **Cuando** consulta `GET /usuarios`
- **Entonces** el sistema responde `200` con los tres usuarios ordenados por `id` ascendente y el inactivo incluido

#### Scenario: El listado no expone el hash

- **Dado** usuarios existentes y un usuario con rol `administracion`
- **Cuando** consulta `GET /usuarios`
- **Entonces** ningún elemento de la respuesta contiene las claves `password` ni `password_hash`

#### Scenario: Recepción consulta el listado

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** consulta `GET /usuarios`
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso`

### Requirement: Edición parcial de usuario

El sistema SHALL permitir a `administracion` actualizar parcialmente un usuario con `PATCH /usuarios/{id}`, respondiendo `200` con los datos actualizados. Los campos omitidos SHALL conservar su valor; `null` en `rol` o en `activo` SHALL responder `422`. Un `id` inexistente SHALL responder `404` con `codigo` `no_encontrado`. El `username` es inmutable: si el body lo incluye, SHALL responder `422` sin modificar el usuario.

#### Scenario: Desactivar un usuario con PATCH

- **Dado** un usuario activo existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con `{"activo": false}`
- **Entonces** el sistema responde `200` con el usuario y `activo` en `false`

#### Scenario: Reactivar un usuario con PATCH

- **Dado** un usuario inactivo existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con `{"activo": true}`
- **Entonces** el sistema responde `200` con el usuario y `activo` en `true`

#### Scenario: Rol nulo en la edición

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con `{"rol": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el usuario no se modifica

#### Scenario: Estado activo nulo en la edición

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con `{"activo": null}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el usuario no se modifica

#### Scenario: Intento de cambiar el username

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con `{"username": "otro_nombre_ficticio"}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el usuario conserva su username original

#### Scenario: Edición de un usuario inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `PATCH /usuarios/9999` para un identificador que no existe
- **Entonces** el sistema responde `404` con `codigo` `no_encontrado` y un `mensaje` en español

### Requirement: Cambio de rol y vínculo con profesional en la edición

Al cambiar el `rol` a un valor distinto de `odontologo`, el sistema SHALL limpiar `profesional_id` automáticamente y responder `200`. Al cambiarlo a `odontologo`, el request SHALL traer un `profesional_id` existente y activo; si no, SHALL responder `422` sin modificar el usuario. Si el `rol` no cambia, el `profesional_id` candidato SHALL seguir cumpliendo la invariante.

#### Scenario: De recepción a odontólogo con profesional válido

- **Dado** un usuario con rol `recepcion` y un profesional activo
- **Cuando** un administrador envía `PATCH /usuarios/{id}` con `{"rol": "odontologo", "profesional_id": <id del profesional>}`
- **Entonces** el sistema responde `200` con `rol` `odontologo` y el `profesional_id` informado

#### Scenario: De recepción a odontólogo sin profesional

- **Dado** un usuario con rol `recepcion`
- **Cuando** un administrador envía `PATCH /usuarios/{id}` con `{"rol": "odontologo"}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el usuario conserva su rol y su `profesional_id` anteriores

#### Scenario: De odontólogo a recepción limpia el vínculo

- **Dado** un usuario con rol `odontologo` vinculado a un profesional
- **Cuando** un administrador envía `PATCH /usuarios/{id}` con `{"rol": "recepcion"}`
- **Entonces** el sistema responde `200` con `rol` `recepcion` y `profesional_id` en `null`

#### Scenario: De odontólogo a administración limpia el vínculo

- **Dado** un usuario con rol `odontologo` vinculado a un profesional
- **Cuando** un administrador envía `PATCH /usuarios/{id}` con `{"rol": "administracion"}`
- **Entonces** el sistema responde `200` con `rol` `administracion` y `profesional_id` en `null`

#### Scenario: Cambio de profesional sin cambiar el rol

- **Dado** un usuario con rol `odontologo` vinculado a un profesional y otro profesional activo
- **Cuando** un administrador envía `PATCH /usuarios/{id}` con el `profesional_id` del segundo profesional
- **Entonces** el sistema responde `200` con el nuevo `profesional_id`

#### Scenario: Cambio a un profesional inactivo sin cambiar el rol

- **Dado** un usuario con rol `odontologo` y un profesional inactivo
- **Cuando** un administrador envía `PATCH /usuarios/{id}` con el `profesional_id` del profesional inactivo
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el usuario conserva su `profesional_id` anterior

### Requirement: Reset de contraseña por administración

`PATCH /usuarios/{id}` SHALL aceptar un campo opcional `password` con al menos un carácter. Si viene, el sistema SHALL guardarlo solo como hash nuevo y responder `200` sin devolverlo; si se omite, el hash SHALL conservarse. La contraseña nueva SHALL habilitar el login y la anterior MUST NOT. El sistema MUST NOT imponer una política de longitud distinta de la del login.

#### Scenario: Reset de contraseña cambia el hash

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con una `password` nueva
- **Entonces** el sistema responde `200` y el hash guardado deja de verificar la contraseña anterior

#### Scenario: La contraseña nueva permite login

- **Dado** un usuario existente cuyo hash fue actualizado por un reset
- **Cuando** se hace `POST /auth/login` con la contraseña nueva
- **Entonces** el sistema responde `200` con un token válido

#### Scenario: La contraseña anterior ya no sirve

- **Dado** un usuario existente cuyo hash fue actualizado por un reset
- **Cuando** se hace `POST /auth/login` con la contraseña anterior
- **Entonces** el sistema responde `401` con `codigo` `credenciales_invalidas`

#### Scenario: PATCH sin password conserva el hash

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con `{"activo": false}` sin `password`
- **Entonces** el hash guardado no cambia y el login con la contraseña original sigue funcionando tras reactivar el usuario

#### Scenario: Contraseña vacía en la edición

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con `{"password": ""}`
- **Entonces** el sistema responde `422` con `codigo` `dato_invalido` y el hash no cambia

#### Scenario: La respuesta del reset no expone secretos

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `PATCH /usuarios/{id}` con una `password` nueva
- **Entonces** el cuerpo de la respuesta `200` no contiene las claves `password` ni `password_hash`

### Requirement: Baja lógica y efecto en el acceso

Desactivar un usuario SHALL ser `PATCH` con `activo = false`; el usuario SHALL seguir apareciendo en el listado como inactivo y MUST NOT poder autenticarse (`401` `credenciales_invalidas`). Un token válido emitido antes de la desactivación SHALL dejar de servir (`401` `no_autenticado`). MUST NOT existir borrado físico ni rutas `PUT`/`DELETE` para usuarios.

#### Scenario: Usuario desactivado no puede loguear

- **Dado** un usuario activo con contraseña conocida, desactivado con `PATCH /usuarios/{id}`
- **Cuando** se hace `POST /auth/login` con sus credenciales correctas
- **Entonces** el sistema responde `401` con `codigo` `credenciales_invalidas`

#### Scenario: Token vigente tras la desactivación

- **Dado** un token válido emitido para un usuario y ese usuario desactivado después del login
- **Cuando** el usuario llama a una ruta protegida con ese token
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`

#### Scenario: El usuario desactivado sigue en el listado

- **Dado** un usuario desactivado con `PATCH /usuarios/{id}` y un administrador autenticado
- **Cuando** consulta `GET /usuarios`
- **Entonces** el usuario aparece con `activo` en `false`

#### Scenario: No existe borrado físico

- **Dado** un usuario existente y un usuario con rol `administracion`
- **Cuando** envía `DELETE /usuarios/{id}`
- **Entonces** el sistema responde `405` con `codigo` `metodo_no_permitido` y el usuario sigue existiendo

### Requirement: Control de acceso a la gestión de usuarios

Las tres rutas de `/usuarios` SHALL exigir token válido y SHALL admitir solo el rol `administracion`; recepción y odontólogo SHALL recibir `403` con `codigo` `sin_permiso`, y un request sin token SHALL recibir `401` con `codigo` `no_autenticado`.

#### Scenario: Recepción intenta crear un usuario

- **Dado** un usuario autenticado con rol `recepcion`
- **Cuando** envía `POST /usuarios` con datos válidos
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y no crea el usuario

#### Scenario: Odontología intenta editar un usuario

- **Dado** un usuario existente y un usuario autenticado con rol `odontologo`
- **Cuando** envía `PATCH /usuarios/{id}` con un cambio válido
- **Entonces** el sistema responde `403` con `codigo` `sin_permiso` y el usuario no se modifica

#### Scenario: Consulta de usuarios sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `GET /usuarios`
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`

#### Scenario: Alta de usuario sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `POST /usuarios` con datos válidos
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`

#### Scenario: Edición de usuario sin autenticación

- **Dado** un cliente sin token de autenticación
- **Cuando** envía `PATCH /usuarios/1` con un cambio válido
- **Entonces** el sistema responde `401` con `codigo` `no_autenticado`
