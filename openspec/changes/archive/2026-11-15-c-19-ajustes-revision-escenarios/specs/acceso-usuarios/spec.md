# Spec Delta

## MODIFIED Requirements

### Requirement: Catálogo demo de desarrollo

Bajo el mismo gate del seed de desarrollo, el sistema SHALL sembrar un catálogo ficticio con dos profesionales (ambos con matrícula ficticia), dos sillones, tres prestaciones con duración de 30, 45 y 60 minutos, y dos pacientes (uno con obra social y otro sin ella).

#### Scenario: Catálogo completo al arrancar

- **Dado** `APP_ENV=development` con `SEED_ADMIN_PASSWORD` definida y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** existen exactamente 2 profesionales, 2 sillones, 3 prestaciones y 2 pacientes, todos activos
- **Y** las tres prestaciones tienen duración de 30, 45 y 60 minutos respectivamente
- **Y** los dos profesionales tienen una matrícula terminada en `"(ficticia)"`
- **Y** uno de los pacientes tiene `obra_social` no nula y el otro la tiene nula

#### Scenario: Los recursos sembrados aceptan turnos

- **Dado** el catálogo demo sembrado con `SEED_ADMIN_PASSWORD` y `SEED_RECEPCION_PASSWORD` definidas, un reloj inyectado que marca un lunes a las 09:00 en la zona horaria de la clínica (`CLINIC_TIMEZONE`) y un usuario `recepcion_demo` autenticado
- **Cuando** reserva un turno ese mismo lunes a las 10:00, con el profesional "Odontólogo Ficticio A" (franja sembrada de 09:00 a 13:00), el "Sillón 1" (`sillon_id`, RN-TUR-02) y la prestación "Consulta ficticia"
- **Entonces** responde `201` con `estado` `reservado`, `sillon_id` igual al del "Sillón 1", `inicio` ese lunes a las 10:00 y `fin` ese lunes a las 10:30
- **Y** el `inicio` del turno es posterior al instante del reloj, así que el turno es futuro y admite cancelación o reprogramación (RN-TUR-09)

### Requirement: Usuarios demo de recepción y odontología

Con `SEED_RECEPCION_PASSWORD` definida, el seed SHALL crear `recepcion_demo` (rol `recepcion`, activo); con `SEED_ODONTOLOGO_PASSWORD`, `odontologo_demo` (rol `odontologo`, activo, ligado al profesional "Odontólogo Ficticio A"). Cada usuario SHALL crearse solo si su contraseña está definida y SHALL NOT modificarse si ya existe.

#### Scenario: Seed completo con las tres contraseñas

- **Dado** `APP_ENV=development` con `SEED_ADMIN_PASSWORD`, `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD` definidas, y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** existen exactamente los usuarios `admin_demo`, `recepcion_demo` y `odontologo_demo`, los tres activos y con su rol correspondiente
- **Y** `odontologo_demo` tiene `profesional_id` igual al id del profesional "Odontólogo Ficticio A"
- **Y** `recepcion_demo` y `admin_demo` tienen `profesional_id` nulo
- **Y** la base tiene 32 filas de datos demo en total
- **Y** `POST /auth/login` con cada uno de los tres usuarios responde `200`

#### Scenario: Sin variable de contraseña no hay usuario para ese rol

- **Dado** `APP_ENV=development` con `SEED_ADMIN_PASSWORD` definida y sin `SEED_RECEPCION_PASSWORD` ni `SEED_ODONTOLOGO_PASSWORD`
- **Cuando** la aplicación arranca
- **Entonces** existe `admin_demo` y el catálogo demo está sembrado
- **Y** no existen los usuarios `recepcion_demo` ni `odontologo_demo`

#### Scenario: Un usuario demo existente no se modifica

- **Dado** una base donde `recepcion_demo` ya existe con otro rol y `activo = 0`, con `SEED_ADMIN_PASSWORD`, `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD` definidas
- **Cuando** la aplicación arranca de nuevo en development
- **Entonces** `recepcion_demo` conserva su rol, su `password_hash` y su estado `activo`

#### Scenario: Solo la contraseña de odontología crea solo odontologo_demo

- **Dado** `APP_ENV=development` con `SEED_ADMIN_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD` definidas, sin `SEED_RECEPCION_PASSWORD`, y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** existen exactamente los usuarios `admin_demo` y `odontologo_demo`, y el catálogo demo está sembrado
- **Y** `odontologo_demo` tiene rol `odontologo`, está activo y tiene `profesional_id` igual al id del profesional "Odontólogo Ficticio A"
- **Y** no existe el usuario `recepcion_demo`
- **Y** `POST /auth/login` con `odontologo_demo` y el valor de `SEED_ODONTOLOGO_PASSWORD` responde `200`

#### Scenario: Solo la contraseña de recepción crea solo recepcion_demo

- **Dado** `APP_ENV=development` con `SEED_ADMIN_PASSWORD` y `SEED_RECEPCION_PASSWORD` definidas, sin `SEED_ODONTOLOGO_PASSWORD`, y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** existen exactamente los usuarios `admin_demo` y `recepcion_demo`, y el catálogo demo está sembrado
- **Y** `recepcion_demo` tiene rol `recepcion`, está activo y tiene `profesional_id` nulo
- **Y** no existe el usuario `odontologo_demo`
- **Y** `POST /auth/login` con `recepcion_demo` y el valor de `SEED_RECEPCION_PASSWORD` responde `200`

### Requirement: Datos ficticios del seed

Todos los datos del seed demo SHALL ser ficticios y estar rotulados como tales (RN-PAC-03): los DNI de los pacientes demo SHALL terminar en `"(ficticio)"` y el nombre completo (nombre y apellido) de cada profesional y paciente SHALL incluir la palabra "ficticio" o "ficticia" (sin distinguir mayúsculas). Alcanza con que la palabra aparezca en uno de los dos campos: se evalúa el texto formado por `nombre` y `apellido` juntos (por ejemplo, `nombre` "Paciente" y `apellido` "Ficticio 1" cumple). El seed MUST NOT contener datos reales de pacientes.

#### Scenario: Los DNI demo están rotulados

- **Dado** el catálogo demo sembrado con `SEED_ADMIN_PASSWORD` definida
- **Cuando** se consultan los pacientes con una consulta directa a la tabla `paciente`
- **Entonces** cada `dni` termina en `"(ficticio)"`

#### Scenario: Los nombres demo están rotulados

- **Dado** el catálogo demo sembrado con `SEED_ADMIN_PASSWORD` definida
- **Cuando** se consultan los profesionales y los pacientes con una consulta directa a la base
- **Entonces** para cada uno, el texto formado por su `nombre` y su `apellido` juntos contiene "ficticio" o "ficticia", sin distinguir mayúsculas
