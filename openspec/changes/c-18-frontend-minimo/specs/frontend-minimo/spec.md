# Spec Delta

## Purpose

Entrega de la interfaz web mínima en TypeScript compilada a archivos estáticos y servida por FastAPI (`GET /` y `/static/*`), permitiendo operar las vistas de login, agenda de un profesional, alta de turno y alta de bloqueo con reporte de `turnos_afectados` respetando los roles y el contrato de errores en español de la API (`D-09`).

## ADDED Requirements

### Requirement: Entrega de documentos y recursos estáticos sin alterar el 404 JSON

El sistema SHALL servir el documento principal HTML en `GET /` con código `200` y tipo `text/html`, y los recursos estáticos compilados (`.js` y `.css`) bajo el prefijo `/static/`. Cualquier ruta inexistente fuera de `/static/` SHALL seguir respondiendo `404` en formato JSON con `codigo = "no_encontrado"` y `mensaje` en español (`RN-GLO-01`).

#### Scenario: Carga inicial de la interfaz web en la raíz

- **Dado** la aplicación FastAPI iniciada
- **Cuando** un cliente solicita `GET /`
- **Entonces** el sistema responde `200` con `Content-Type` que incluye `text/html` y el cuerpo de `index.html` con los contenedores de login, agenda, crear turno y crear bloqueo

#### Scenario: Carga de los recursos estáticos compilados bajo /static

- **Dado** la aplicación FastAPI iniciada con los archivos compilados en `app/static/`
- **Cuando** el navegador solicita `GET /static/app.js` y `GET /static/styles.css`
- **Entonces** el sistema responde `200` en ambas peticiones con el código JavaScript compilado desde TypeScript y la hoja de estilos

#### Scenario: Una ruta de API inexistente conserva el 404 JSON en español (RN-GLO-01)

- **Dado** la aplicación FastAPI iniciada con `GET /` y `/static` montados
- **Cuando** un cliente solicita una ruta inexistente como `GET /ruta-que-no-existe`
- **Entonces** el sistema responde `404` con cuerpo JSON `{"codigo": "no_encontrado", "mensaje": "El recurso solicitado no existe."}` y no devuelve HTML

### Requirement: Inicio de sesión y visibilidad por rol en la interfaz

La interfaz SHALL autenticar al usuario mediante `POST /auth/login` (`RN-ACC-01`), almacenar el `access_token` en `sessionStorage` y mostrar solo las secciones habilitadas para el claim `rol` del token (`RN-ACC-02`). Ante cualquier respuesta `401`, la interfaz SHALL mostrar el `mensaje` en español devuelto por la API (`RN-GLO-01`).

#### Scenario: Inicio de sesión válido adapta las vistas según el rol (RN-ACC-01, RN-ACC-02)

- **Dado** el usuario demo `recepcion_demo` con rol `recepcion` en la pantalla de login
- **Cuando** ingresa sus credenciales válidas y envía el formulario hacia `POST /auth/login`
- **Entonces** la interfaz guarda el token en `sessionStorage`, muestra las vistas de Agenda y Crear Turno, y oculta la vista de Crear Bloqueo exclusiva de `administracion`

#### Scenario: Credenciales inválidas muestran el mensaje 401 de la API (RN-GLO-01)

- **Dado** un usuario en la pantalla de login
- **Cuando** envía credenciales incorrectas y `POST /auth/login` responde `401` con `codigo = "credenciales_invalidas"`
- **Entonces** la interfaz permanece en la pantalla de login y muestra el texto en español del campo `mensaje` devuelto por la API

#### Scenario: Sesión vencida o token inválido redirige al login con mensaje en español (RN-ACC-01, RN-GLO-01)

- **Dado** un usuario con un token vencido o inválido en `sessionStorage`
- **Cuando** la interfaz realiza una petición a una ruta protegida y recibe `401` con `codigo = "no_autenticado"`
- **Entonces** la interfaz limpia `sessionStorage`, vuelve a la pantalla de login y muestra el `mensaje` en español de la respuesta

### Requirement: Consulta de agenda de un profesional

La interfaz SHALL consultar `GET /agenda/profesionales/{id}?desde=&hasta=` para el profesional y rango elegidos (`US-009`), listando por `inicio` los turnos activos y bloqueos. Para `administracion` y `recepcion` SHALL mostrar el paciente ficticio desde `GET /pacientes` (`RN-PAC-03`), y para `odontologo` SHALL mostrar `"Paciente #<paciente_id>"` o el error `403` en español si consulta otro profesional (`RN-ACC-03`).

#### Scenario: Consulta de agenda muestra turnos activos y bloqueos ordenados con datos ficticios (RN-PAC-03)

- **Dado** un usuario autenticado con rol `recepcion` o `administracion` y un profesional con turnos `reservado` de pacientes con DNI terminado en `"(ficticio)"` y bloqueos en el rango
- **Cuando** selecciona al profesional y el rango de fechas y consulta la agenda
- **Entonces** la interfaz llama a `GET /agenda/profesionales/{id}?desde=&hasta=` y muestra la lista ordenada por `inicio` con el horario, estado, sillón, prestación y nombre del paciente ficticio

#### Scenario: Odontólogo que consulta la agenda de otro profesional ve el error 403 en español (RN-ACC-03, RN-GLO-01)

- **Dado** un usuario autenticado con rol `odontologo` vinculado al profesional A
- **Cuando** selecciona en el desplegable al profesional B y solicita su agenda
- **Entonces** la API responde `403` con `codigo = "sin_permiso"` y la interfaz muestra en pantalla el `mensaje` en español devuelto por la API

#### Scenario: Agenda sin turnos ni bloqueos en el rango seleccionado (caso de borde)

- **Dado** un usuario autenticado que consulta la agenda de un profesional válido
- **Cuando** `GET /agenda/profesionales/{id}?desde=&hasta=` devuelve `items = []`
- **Entonces** la interfaz muestra un estado vacío en español indicando que no hay turnos ni bloqueos registrados en ese rango

### Requirement: Creación de turno desde la interfaz

La interfaz SHALL permitir a los roles `administracion` y `recepcion` enviar `POST /turnos` seleccionando paciente, profesional, sillón y prestación activos e ingresando la fecha y hora de `inicio` en formato local sin zona horaria (`RN-TUR-01`, `RN-TUR-02`). Cuando la API rechaza la operación con `409` (`conflicto_agenda`, `fuera_de_horario`, `dentro_de_bloqueo`) o `422` (`dato_invalido`), la interfaz SHALL mostrar el `mensaje` en español de la respuesta (`RN-GLO-01`).

#### Scenario: Alta exitosa de turno muestra confirmación con el horario calculado (RN-TUR-01, RN-TUR-14)

- **Dado** un usuario autenticado con rol `recepcion` y recursos activos cargados en los selectores (con pacientes ficticios `RN-PAC-03`)
- **Cuando** completa paciente, profesional, sillón, prestación e `inicio` válido dentro del horario de atención y envía el formulario
- **Entonces** la interfaz envía `POST /turnos`, recibe `201` y muestra la confirmación con el turno en estado `reservado` y el `fin` calculado según la duración de la prestación

#### Scenario: Rechazo por solapamiento o fuera de horario muestra el error 409 en español (RN-TUR-03, RN-TUR-05, RN-GLO-01)

- **Dado** un usuario autenticado con rol `recepcion` en el formulario de crear turno
- **Cuando** intenta crear un turno en un horario ya ocupado o fuera del horario del profesional y `POST /turnos` responde `409` con `codigo` `conflicto_agenda`, `fuera_de_horario` o `dentro_de_bloqueo`
- **Entonces** la interfaz muestra una alerta de error con el `mensaje` en español devuelto por la API sin limpiar la selección del usuario

#### Scenario: Envío con datos inválidos muestra el error 422 en español (RN-GLO-01)

- **Dado** un usuario autenticado con rol `recepcion` en el formulario de crear turno
- **Cuando** envía datos que la API rechaza con `422` y `codigo = "dato_invalido"`
- **Entonces** la interfaz muestra el `mensaje` en español y los `detalles` por campo devueltos por la API

### Requirement: Creación de bloqueo horario con visualización de turnos afectados

La interfaz SHALL permitir únicamente al rol `administracion` enviar `POST /bloqueos` con `alcance`, `recurso_id`, `inicio`, `fin` y `motivo` (`RN-REC-02`). Al recibir `201`, la interfaz SHALL mostrar el bloqueo creado y la tabla informativa `turnos_afectados` devuelta por la API (`RN-TUR-04`, `RN-TUR-05`, `RN-TUR-08`), sin ofrecer acciones de cancelación, reprogramación, notificación ni exportación.

#### Scenario: Crear bloqueo con turnos reservados superpuestos muestra la tabla de turnos_afectados (RN-TUR-05, RN-TUR-08)

- **Dado** un usuario autenticado con rol `administracion` y un profesional o sillón con turnos `reservado` en el intervalo
- **Cuando** completa el formulario de bloqueo y envía `POST /bloqueos`
- **Entonces** la interfaz recibe `201` y renderiza el listado `turnos_afectados` con el horario (`inicio` y `fin`), el paciente ficticio, el recurso y el estado `reservado` de cada turno afectado

#### Scenario: Intervalo de bloqueo inválido muestra el error 422 en español (RN-REC-02, RN-GLO-01)

- **Dado** un usuario autenticado con rol `administracion` en el formulario de bloqueo
- **Cuando** envía un bloqueo con `inicio` igual o posterior a `fin` y `POST /bloqueos` responde `422` con `codigo = "dato_invalido"`
- **Entonces** la interfaz muestra el `mensaje` de error en español devuelto por la API y no muestra tabla de turnos afectados

#### Scenario: Crear bloqueo sin turnos superpuestos muestra aviso de lista vacía (caso de borde)

- **Dado** un usuario autenticado con rol `administracion` y un intervalo sin turnos activos superpuestos (o solo con turnos contiguos en el borde `RN-TUR-04`)
- **Cuando** envía `POST /bloqueos` y la respuesta `201` trae `turnos_afectados = []`
- **Entonces** la interfaz confirma la creación del bloqueo y muestra un mensaje explícito en español indicando que no hay turnos afectados en ese intervalo
