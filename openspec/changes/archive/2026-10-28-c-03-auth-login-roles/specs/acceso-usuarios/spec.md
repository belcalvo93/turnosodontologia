# Spec Delta — acceso-usuarios

## Purpose

Autentica a los usuarios del consultorio (administración, recepción y odontólogo) y controla qué puede hacer cada rol en la API: login con contraseña hasheada, token firmado validado en cada request y chequeo de rol reutilizable por todos los recursos.

## ADDED Requirements

### Requirement: Contraseñas guardadas solo como hash

El sistema SHALL guardar la contraseña de cada usuario únicamente como un hash con sal de un algoritmo estándar para contraseñas. La contraseña en texto plano MUST NOT persistirse ni devolverse en ninguna respuesta. Dos usuarios con la misma contraseña SHALL tener hashes distintos (RN-ACC-04).

#### Scenario: La base no contiene la contraseña original

- **Dado** un usuario ficticio `recepcion_ficticia` creado con la contraseña `clave-ficticia-123`
- **Cuando** se lee su fila en la tabla `usuario`
- **Entonces** el valor guardado en `password_hash` es distinto de `clave-ficticia-123` y no la contiene como substring

#### Scenario: Misma contraseña, hashes distintos

- **Dado** dos usuarios ficticios creados con la misma contraseña `clave-ficticia-123`
- **Cuando** se comparan sus `password_hash`
- **Entonces** los dos valores son distintos

#### Scenario: El hash verifica solo la contraseña correcta

- **Dado** el hash guardado de la contraseña `clave-ficticia-123`
- **Cuando** se verifica contra `clave-ficticia-123` y contra `otra-clave-ficticia`
- **Entonces** la primera verificación es exitosa y la segunda falla

### Requirement: Datos de usuario válidos en la base

La tabla `usuario` SHALL exigir `username` único y `rol` dentro de `administracion`, `recepcion` u `odontologo`. `profesional_id` SHALL ser opcional y sin clave foránea en la base; la existencia del profesional la valida la aplicación al crear usuarios odontólogo (C-07).

#### Scenario: Username duplicado

- **Dado** un usuario ficticio `recepcion_ficticia` ya guardado
- **Cuando** se intenta guardar otro usuario con el mismo `username`
- **Entonces** la base rechaza la inserción con error de integridad

#### Scenario: Rol fuera de los tres roles

- **Dado** la tabla `usuario` vacía
- **Cuando** se intenta guardar un usuario con rol `paciente`
- **Entonces** la base rechaza la inserción con error de integridad

#### Scenario: Usuario sin profesional asociado

- **Dado** la tabla `usuario` vacía
- **Cuando** se guarda un usuario de rol `administracion` con `profesional_id` nulo
- **Entonces** la inserción se confirma sin error

### Requirement: Login con usuario y contraseña

El sistema SHALL exponer `POST /auth/login` sin autenticación, con body JSON `{username, password}`. Con credenciales válidas de un usuario activo SHALL responder `200` con `{"access_token": <token>, "token_type": "bearer"}`. El token SHALL identificar al usuario, incluir su rol y vencer a los `ACCESS_TOKEN_EXPIRE_MINUTES` minutos de emitido.

#### Scenario: Login correcto devuelve token

- **Dado** un usuario ficticio activo `recepcion_ficticia` con rol `recepcion` y contraseña `clave-ficticia-123`
- **Cuando** se hace `POST /auth/login` con `{"username": "recepcion_ficticia", "password": "clave-ficticia-123"}`
- **Entonces** responde `200` con `token_type` igual a `bearer` y un `access_token` no vacío
- **Y** ese token permite acceder a una ruta protegida que admite el rol `recepcion`

#### Scenario: El token incluye usuario, rol y vencimiento

- **Dado** `ACCESS_TOKEN_EXPIRE_MINUTES=60` y un login correcto de `recepcion_ficticia`
- **Cuando** se decodifica el token con la clave configurada
- **Entonces** contiene el id del usuario, el rol `recepcion` y un vencimiento 60 minutos posterior a su emisión

#### Scenario: Body de login incompleto

- **Dado** la aplicación iniciada
- **Cuando** se hace `POST /auth/login` con `{"username": "recepcion_ficticia"}` sin `password`
- **Entonces** responde `422` con `codigo` igual a `dato_invalido` y un elemento de `detalles` cuyo `campo` es `password`

### Requirement: Credenciales inválidas indistinguibles

Ante un login fallido el sistema SHALL responder `401` con el mismo cuerpo exacto (`codigo` `credenciales_invalidas` y el mismo `mensaje`) sin importar si el usuario no existe, la contraseña es incorrecta o el usuario está inactivo, para no revelar qué usuarios existen.

#### Scenario: Usuario inexistente

- **Dado** que no existe ningún usuario `fantasma_ficticio`
- **Cuando** se hace `POST /auth/login` con `{"username": "fantasma_ficticio", "password": "clave-ficticia-123"}`
- **Entonces** responde `401` con `codigo` igual a `credenciales_invalidas`

#### Scenario: Contraseña incorrecta

- **Dado** un usuario ficticio activo `recepcion_ficticia` con contraseña `clave-ficticia-123`
- **Cuando** se hace `POST /auth/login` con su username y la contraseña `otra-clave-ficticia`
- **Entonces** responde `401` con `codigo` igual a `credenciales_invalidas`

#### Scenario: Usuario inactivo

- **Dado** un usuario ficticio `inactivo_ficticio` con `activo = 0` y contraseña `clave-ficticia-123`
- **Cuando** se hace `POST /auth/login` con sus credenciales correctas
- **Entonces** responde `401` con `codigo` igual a `credenciales_invalidas`

#### Scenario: Los tres casos devuelven el mismo cuerpo

- **Dado** las respuestas de los tres escenarios anteriores
- **Cuando** se comparan sus cuerpos JSON
- **Entonces** los tres son idénticos

### Requirement: Rutas protegidas exigen un token válido

Toda ruta protegida SHALL exigir la cabecera `Authorization: Bearer <token>` con un token firmado por el sistema y no vencido. Si falta, está mal formada, es inválida o está vencida, SHALL responder `401` con `codigo` `no_autenticado` y la cabecera `WWW-Authenticate: Bearer` (RN-ACC-01). `/auth/login` y `/health` son públicas.

#### Scenario: Sin token

- **Dado** una ruta protegida
- **Cuando** se la llama sin cabecera `Authorization`
- **Entonces** responde `401` con `codigo` igual a `no_autenticado` y la cabecera `WWW-Authenticate: Bearer`

#### Scenario: Cabecera mal formada

- **Dado** una ruta protegida
- **Cuando** se la llama con `Authorization: Basic dXN1YXJpbzpjbGF2ZQ==`
- **Entonces** responde `401` con `codigo` igual a `no_autenticado`

#### Scenario: Token inválido

- **Dado** una ruta protegida
- **Cuando** se la llama con un token que no fue firmado con la clave del sistema (texto arbitrario, firmado con otra clave o con algoritmo `none`)
- **Entonces** responde `401` con `codigo` igual a `no_autenticado`

#### Scenario: Token vencido

- **Dado** un token emitido para `recepcion_ficticia` cuyo vencimiento ya pasó
- **Cuando** se llama a una ruta protegida con ese token
- **Entonces** responde `401` con `codigo` igual a `no_autenticado`

#### Scenario: Límite del vencimiento

- **Dado** `ACCESS_TOKEN_EXPIRE_MINUTES=60` y un token emitido en el instante T
- **Cuando** se llama a una ruta protegida en T + 59 minutos y luego en T + 60 minutos
- **Entonces** la primera llamada responde `200` y la segunda responde `401` con `codigo` igual a `no_autenticado`

#### Scenario: Health sigue siendo público

- **Dado** la aplicación iniciada
- **Cuando** se hace `GET /health` sin cabecera `Authorization`
- **Entonces** responde `200`

### Requirement: Usuario recargado desde la base en cada request

Con un token válido, el sistema SHALL recargar el usuario desde la base en cada request y usar el rol y el estado `activo` guardados, no los del token. Si el usuario ya no existe o fue desactivado, SHALL responder `401` con `codigo` `no_autenticado`.

#### Scenario: Usuario desactivado después del login

- **Dado** un token válido emitido para `recepcion_ficticia`
- **Y** luego `recepcion_ficticia` pasa a `activo = 0` en la base
- **Cuando** se llama a una ruta protegida con ese token
- **Entonces** responde `401` con `codigo` igual a `no_autenticado`

#### Scenario: Cambio de rol después del login

- **Dado** un token válido emitido para `recepcion_ficticia` con rol `recepcion`
- **Y** luego su rol cambia a `odontologo` en la base
- **Cuando** llama a una ruta protegida que solo admite `recepcion`
- **Entonces** responde `403` con `codigo` igual a `sin_permiso`

### Requirement: Autorización por rol

Una ruta protegida SHALL poder declarar qué roles la admiten. Un usuario autenticado cuyo rol no está entre ellos SHALL recibir `403` con `codigo` `sin_permiso`; uno cuyo rol está admitido SHALL acceder normalmente (RN-ACC-02).

#### Scenario: Rol sin permiso

- **Dado** una ruta protegida que solo admite el rol `administracion`
- **Cuando** `recepcion_ficticia` (rol `recepcion`) la llama con un token válido
- **Entonces** responde `403` con `codigo` igual a `sin_permiso`

#### Scenario: Rol permitido

- **Dado** una ruta protegida que admite los roles `administracion` y `recepcion`
- **Cuando** `recepcion_ficticia` (rol `recepcion`) la llama con un token válido
- **Entonces** responde `200`

### Requirement: Usuario administrador de desarrollo

Al arrancar en `APP_ENV=development` con `SEED_ADMIN_PASSWORD` definida, el sistema SHALL crear el usuario `admin_demo` con rol `administracion`, activo y con esa contraseña hasheada, si no existe. El seed SHALL ser idempotente y no modificar un `admin_demo` existente. En otro entorno o sin la variable, MUST NOT crear usuarios.

#### Scenario: Creación en development

- **Dado** `APP_ENV=development`, `SEED_ADMIN_PASSWORD=clave-demo-ficticia` y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** existe un único usuario `admin_demo` con rol `administracion` y activo
- **Y** `POST /auth/login` con `admin_demo` / `clave-demo-ficticia` responde `200`

#### Scenario: Arranque repetido idempotente

- **Dado** una base temporal donde un arranque previo en development ya creó `admin_demo`
- **Cuando** la aplicación vuelve a arrancar con la misma configuración
- **Entonces** sigue existiendo un único usuario `admin_demo` y su `password_hash` no cambió

#### Scenario: Sin seed fuera de development

- **Dado** `APP_ENV=test`, `SEED_ADMIN_PASSWORD=clave-demo-ficticia` y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** la tabla `usuario` está vacía

#### Scenario: Sin seed si falta la contraseña

- **Dado** `APP_ENV=development` sin `SEED_ADMIN_PASSWORD` y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** el arranque termina sin error y la tabla `usuario` está vacía
