# Spec Delta

## Purpose

Plataforma mínima sobre la que se construye la API de turnos: lee su configuración del entorno, abre conexiones SQLite con transacciones atómicas y claves foráneas activas, aplica el esquema al arrancar y expone un endpoint de salud público.

## ADDED Requirements

### Requirement: Configuración desde variables de entorno

El sistema SHALL construir su configuración desde las variables de entorno `APP_ENV`, `DATABASE_URL` y `CLINIC_TIMEZONE`, sin dependencias de carga automática de archivos. `DATABASE_URL` SHALL aceptar tanto el formato `sqlite:///ruta` como un path plano y SHALL normalizarse a un path usable por `sqlite3`. Si una variable no está definida, SHALL aplicarse el default de desarrollo (`development`, `./turnos.db`, `America/Argentina/Buenos_Aires`).

#### Scenario: Defaults de desarrollo

- **Dado** un entorno sin `APP_ENV`, sin `DATABASE_URL` y sin `CLINIC_TIMEZONE`
- **Cuando** se carga la configuración
- **Entonces** `app_env` es `development`, el path de la base es `./turnos.db` y la zona horaria es `America/Argentina/Buenos_Aires`

#### Scenario: DATABASE_URL con esquema de URL

- **Dado** un entorno con `DATABASE_URL="sqlite:///./turnos.db"` y `APP_ENV="test"`
- **Cuando** se carga la configuración
- **Entonces** el path de la base es `./turnos.db` (sin el prefijo `sqlite:///`) y `app_env` es `test`

#### Scenario: Path explícito de la base

- **Dado** un entorno con `DATABASE_URL` apuntando a un archivo temporal absoluto
- **Cuando** se carga la configuración
- **Entonces** el path de la base es exactamente ese archivo absoluto, sin prefijos ni transformaciones adicionales

### Requirement: Conexión SQLite transaccional

El sistema SHALL proveer una función que abra conexiones SQLite sobre la base configurada con `PRAGMA foreign_keys=ON` y `busy_timeout` definido, cerrables por quien las usa, y un context manager de transacción que haga `BEGIN IMMEDIATE`, `commit` al salir sin excepción y `rollback` si se lanza una excepción dentro del bloque.

#### Scenario: Claves foráneas activas

- **Dado** una conexión del sistema y un esquema de prueba con una tabla hija que referencia a una tabla padre
- **Cuando** se intenta insertar una fila hija con un id de padre inexistente
- **Entonces** SQLite rechaza la inserción con error de clave foránea

#### Scenario: Commit al cerrar la transacción

- **Dado** una base temporal y una tabla de prueba
- **Cuando** se ejecuta un `INSERT` dentro del context manager de transacción y el bloque termina sin excepción
- **Entonces** la fila queda persistida al abrir una conexión nueva

#### Scenario: Rollback ante excepción

- **Dado** una base temporal, una tabla de prueba y un `INSERT` dentro del context manager de transacción
- **Cuando** el bloque lanza una excepción después del `INSERT`
- **Entonces** la excepción se propaga y la fila no queda persistida

### Requirement: Esquema aplicado al arrancar

El sistema SHALL aplicar `app/db/esquema.sql` sobre la base configurada al iniciar la aplicación, antes de atender requests, y SHALL poder repetir esa aplicación en arranques sucesivos sin error. En este change el archivo solo contiene comentarios: no crea tablas.

#### Scenario: Arranque con esquema vacío

- **Dado** el `esquema.sql` de este change, que no declara tablas, y una base temporal
- **Cuando** la aplicación arranca
- **Entonces** el arranque termina sin error y la aplicación queda lista para atender requests

#### Scenario: Aplicación repetida del esquema

- **Dado** una base temporal ya inicializada
- **Cuando** se vuelve a aplicar el esquema
- **Entonces** la operación termina sin error y la base queda en el mismo estado

### Requirement: Endpoint de salud público

El sistema SHALL exponer `GET /health` sin autenticación, respondiendo `200` con un cuerpo JSON que indique que la API está operativa, sin consultar la base de datos.

#### Scenario: Consulta de salud sin token

- **Dado** la aplicación iniciada con una base temporal
- **Cuando** se hace `GET /health` sin cabecera de autenticación
- **Entonces** responde `200` con `{"status": "ok"}`
