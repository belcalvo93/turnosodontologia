# base-tecnica Specification

## Purpose
Plataforma mínima sobre la que se construye la API de turnos: lee su configuración del entorno, abre conexiones SQLite con transacciones atómicas y claves foráneas activas, aplica el esquema al arrancar y expone un endpoint de salud público.

## Requirements

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

El sistema SHALL proveer una función que abra conexiones SQLite sobre la base configurada con `PRAGMA foreign_keys=ON` y `busy_timeout` definido, cerrables por quien las usa, y un context manager de transacción que haga `BEGIN IMMEDIATE`, `commit` al salir sin excepción y `rollback` si se lanza una excepción dentro del bloque. Una conexión SHALL poder usarse desde un hilo distinto al que la abrió, siempre que no se comparta entre requests concurrentes.

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

#### Scenario: Uso desde otro hilo

- **Dado** una conexión del sistema abierta en el hilo principal
- **Cuando** se ejecuta una consulta y se cierra la conexión desde otro hilo
- **Entonces** la consulta devuelve su resultado y el cierre termina sin error de hilo

### Requirement: Esquema aplicado al arrancar

El sistema SHALL aplicar `app/db/esquema.sql` sobre la base configurada al iniciar la aplicación, antes de atender requests, y SHALL poder repetir esa aplicación en arranques sucesivos sin error. Cada tabla del esquema SHALL declararse de forma idempotente.

#### Scenario: Arranque con esquema vacío

- **Dado** una base temporal vacía, sin ninguna tabla
- **Cuando** la aplicación arranca
- **Entonces** el arranque termina sin error, la tabla `usuario` existe y la aplicación queda lista para atender requests

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

### Requirement: Configuración de autenticación

El sistema SHALL leer `JWT_SECRET`, `JWT_ALGORITHM` (default `HS256`, solo HMAC), `ACCESS_TOKEN_EXPIRE_MINUTES` (default `60`, entero positivo) y `SEED_ADMIN_PASSWORD` (opcional). Sin `JWT_SECRET`, en `development` o `test` SHALL generar un secreto aleatorio por proceso; en cualquier otro entorno la aplicación MUST NOT arrancar. El código MUST NOT contener un secreto por defecto.

#### Scenario: Defaults de autenticación en desarrollo

- **Dado** un entorno vacío
- **Cuando** se carga la configuración
- **Entonces** el algoritmo es `HS256`, la duración del token es `60` minutos, no hay contraseña de seed y hay un secreto no vacío

#### Scenario: Secreto aleatorio por proceso

- **Dado** un entorno con `APP_ENV=test` sin `JWT_SECRET`
- **Cuando** se carga la configuración dos veces
- **Entonces** las dos cargas tienen secretos no vacíos y distintos entre sí

#### Scenario: Secreto explícito

- **Dado** un entorno con `JWT_SECRET` definido con un valor ficticio de 32 caracteres o más
- **Cuando** se carga la configuración
- **Entonces** el secreto de la configuración es exactamente ese valor

#### Scenario: Falta JWT_SECRET fuera de development y test

- **Dado** un entorno con `APP_ENV=production` sin `JWT_SECRET`
- **Cuando** se carga la configuración para crear la aplicación
- **Entonces** falla con un error de configuración cuyo mensaje nombra `JWT_SECRET`, y la aplicación no se crea

#### Scenario: Duración del token inválida

- **Dado** un entorno con `ACCESS_TOKEN_EXPIRE_MINUTES=abc` (o `0`)
- **Cuando** se carga la configuración
- **Entonces** falla con un error de configuración cuyo mensaje nombra `ACCESS_TOKEN_EXPIRE_MINUTES`

#### Scenario: Algoritmo no admitido

- **Dado** un entorno con `JWT_ALGORITHM=none`
- **Cuando** se carga la configuración
- **Entonces** falla con un error de configuración cuyo mensaje nombra `JWT_ALGORITHM`

### Requirement: Documentación OpenAPI solo en development

El sistema SHALL exponer `/docs` y `/openapi.json` sin autenticación solo cuando `APP_ENV` es `development`. En cualquier otro entorno ambas rutas SHALL responder `404` (03 §Rutas públicas).

#### Scenario: Docs disponibles en development

- **Dado** la aplicación iniciada con `APP_ENV=development`
- **Cuando** se hace `GET /docs` y `GET /openapi.json`
- **Entonces** ambas responden `200`

#### Scenario: Docs ocultas fuera de development

- **Dado** la aplicación iniciada con `APP_ENV=test`
- **Cuando** se hace `GET /docs` y `GET /openapi.json`
- **Entonces** ambas responden `404`


### Requirement: Trazabilidad de reglas de negocio a tests

El repositorio SHALL mantener `docs/trazabilidad-rn-test.md` con una fila por regla `RN-xx-NN` de `knowledge-base/05_reglas_de_negocio.md`, citando el test que la cubre. La suite SHALL fallar si falta una regla o un test citado, si `RN-TUR-13` no cita el mismo test que `RN-TUR-04`, o si una regla que no es `RN-GLO-02` figura como `No aplica`. `RN-GLO-02` SHALL figurar como `No aplica` con su motivo: declara una ausencia, no un comportamiento.

#### Scenario: Todas las reglas están mapeadas

- **Dado** el repositorio con `docs/trazabilidad-rn-test.md` y `knowledge-base/05_reglas_de_negocio.md`
- **Cuando** se corre la suite
- **Entonces** la verificación de trazabilidad pasa e informa que las 31 reglas están mapeadas
- **Y** cada test citado existe en la suite
- **Y** `RN-TUR-13` cita el mismo test que `RN-TUR-04`
- **Y** `RN-GLO-02` figura como `No aplica` con su motivo

#### Scenario: Una regla sin fila hace fallar la verificación

- **Dado** un documento de reglas que declara una regla `RN-xx-NN` ausente de la tabla de trazabilidad
- **Cuando** se ejecuta la verificación
- **Entonces** falla y el mensaje nombra el código de la regla que falta

#### Scenario: Un test citado inexistente hace fallar la verificación

- **Dado** una tabla de trazabilidad que cita un test que no existe en la suite
- **Cuando** se ejecuta la verificación
- **Entonces** falla y el mensaje nombra el test citado que no se encontró

#### Scenario: No aplica solo vale para RN-GLO-02 y con motivo

- **Dado** una tabla de trazabilidad donde `RN-PAC-01` figura como `No aplica` con motivo, y otra donde `RN-GLO-02` figura como `No aplica` sin motivo
- **Cuando** se ejecuta la verificación sobre cada una
- **Entonces** la primera falla y el mensaje nombra `RN-PAC-01`
- **Y** la segunda falla y el mensaje nombra `RN-GLO-02`

#### Scenario: Una regla sin test verificable no rompe la tabla

- **Dado** una tabla donde `RN-GLO-02` figura como `No aplica` con el motivo "declara una ausencia de funcionalidad del MVP"
- **Cuando** se ejecuta la verificación
- **Entonces** no reporta hallazgos para `RN-GLO-02` y no exige un test citado para esa fila
