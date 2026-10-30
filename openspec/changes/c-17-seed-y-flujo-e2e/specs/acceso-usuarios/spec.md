# Spec Delta

## MODIFIED Requirements

### Requirement: Usuario administrador de desarrollo

Al arrancar en `APP_ENV=development` con `SEED_ADMIN_PASSWORD` definida, el sistema SHALL sembrar los datos demo de desarrollo: el usuario `admin_demo` (rol `administracion`, activo, con esa contraseña hasheada) si no existe, y el catálogo demo. El seed SHALL ser idempotente y SHALL NOT modificar un `admin_demo` existente. En otro entorno o sin la variable, MUST NOT sembrar nada.

#### Scenario: Creación en development

- **Dado** `APP_ENV=development`, `SEED_ADMIN_PASSWORD=clave-demo-ficticia` y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** existe un único usuario `admin_demo` con rol `administracion` y activo
- **Y** el catálogo demo está sembrado
- **Y** `POST /auth/login` con `admin_demo` / `clave-demo-ficticia` responde `200`

#### Scenario: Arranque repetido idempotente

- **Dado** una base temporal donde un arranque previo en development ya sembró los datos demo
- **Cuando** la aplicación vuelve a arrancar con la misma configuración
- **Entonces** cada tabla demo tiene exactamente las mismas filas que antes, sin profesionales ni horarios duplicados
- **Y** el `password_hash` de cada usuario demo no cambió

#### Scenario: Sin seed fuera de development

- **Dado** `APP_ENV=test`, `SEED_ADMIN_PASSWORD=clave-demo-ficticia` y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** las tablas `usuario`, `profesional`, `sillon`, `prestacion`, `horario_atencion` y `paciente` están vacías

#### Scenario: Sin seed si falta la contraseña

- **Dado** `APP_ENV=development` sin `SEED_ADMIN_PASSWORD` y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** el arranque termina sin error y ninguna tabla de datos demo tiene filas

## ADDED Requirements

### Requirement: Catálogo demo de desarrollo

Bajo el mismo gate del seed de desarrollo, el sistema SHALL sembrar un catálogo ficticio con dos profesionales (uno con matrícula ficticia), dos sillones, tres prestaciones con duración de 30, 45 y 60 minutos, y dos pacientes (uno con obra social y otro sin ella).

#### Scenario: Catálogo completo al arrancar

- **Dado** `APP_ENV=development` con `SEED_ADMIN_PASSWORD` definida y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** existen exactamente 2 profesionales, 2 sillones, 3 prestaciones y 2 pacientes, todos activos

#### Scenario: Los recursos sembrados aceptan turnos

- **Dado** el catálogo demo sembrado y un usuario `recepcion_demo` autenticado
- **Cuando** reserva un turno en un día hábil a las 10:00 con la prestación "Consulta ficticia"
- **Entonces** responde `201` con `estado` `reservado` y `fin` a las 10:30

### Requirement: Horarios de atención demo

El seed SHALL crear los horarios de atención de ambos profesionales de lunes a viernes, con dos franjas por día: de 09:00 a 13:00 y de 14:00 a 18:00.

#### Scenario: Horarios de lunes a viernes para ambos profesionales

- **Dado** el catálogo demo sembrado
- **Cuando** se consultan los horarios de cada profesional
- **Entonces** cada uno tiene 2 franjas por cada día hábil de lunes (1) a viernes (5), de 09:00 a 13:00 y de 14:00 a 18:00

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

- **Dado** `APP_ENV=development` con `SEED_ADMIN_PASSWORD` definida pero sin `SEED_RECEPCION_PASSWORD` ni `SEED_ODONTOLOGO_PASSWORD`
- **Cuando** la aplicación arranca
- **Entonces** existe `admin_demo` y el catálogo demo está sembrado
- **Y** no existen los usuarios `recepcion_demo` ni `odontologo_demo`

#### Scenario: Un usuario demo existente no se modifica

- **Dado** una base donde `recepcion_demo` ya existe con otro rol y `activo = 0`
- **Cuando** la aplicación arranca de nuevo en development con su contraseña definida
- **Entonces** `recepcion_demo` conserva su rol, su `password_hash` y su estado `activo`

### Requirement: Contraseñas del seed desde el entorno

Las contraseñas de los usuarios demo SHALL provenir exclusivamente de las variables de entorno `SEED_ADMIN_PASSWORD`, `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD`. Ningún valor de contraseña SHALL estar en el repositorio, y la base SHALL guardar solo el hash Argon2id, nunca el texto plano (RN-ACC-04).

#### Scenario: La base guarda hashes, no contraseñas

- **Dado** `APP_ENV=development` con las tres contraseñas demo definidas y una base temporal vacía
- **Cuando** la aplicación arranca
- **Entonces** el `password_hash` de cada usuario demo empieza con `$argon2id$`

#### Scenario: La contraseña demo no queda en el archivo de la base

- **Dado** un arranque en development con `SEED_ADMIN_PASSWORD=clave-demo-ficticia`
- **Cuando** se leen los bytes del archivo de la base
- **Entonces** la cadena `clave-demo-ficticia` no aparece

### Requirement: Datos ficticios del seed

Todos los datos del seed demo SHALL ser ficticios y estar rotulados como tales (RN-PAC-03): los DNI de los pacientes demo SHALL terminar en `"(ficticio)"` y los nombres de profesionales y pacientes SHALL incluir la palabra "ficticio" o "ficticia" (sin distinguir mayúsculas). El seed MUST NOT contener datos reales de pacientes.

#### Scenario: Los DNI demo están rotulados

- **Dado** el catálogo demo sembrado
- **Cuando** se consultan los pacientes
- **Entonces** cada `dni` termina en `"(ficticio)"`

#### Scenario: Los nombres demo están rotulados

- **Dado** el catálogo demo sembrado
- **Cuando** se consultan profesionales y pacientes
- **Entonces** cada nombre o apellido contiene la palabra "ficticio" o "ficticia", sin distinguir mayúsculas
