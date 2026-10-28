# Tasks — C-03 auth-login-roles

> **Strict TDD**: en cada tarea con código, primero se escribe el test y se ve fallar (RED), después va el mínimo código para que pase (GREEN), luego se triangula con un segundo caso y por último se refactoriza con la suite en verde.
> **Governance CRÍTICO**: el apply se hace por grupos, con un checkpoint con el equipo al cerrar cada grupo.
> Todos los usuarios, contraseñas y secretos de los tests son ficticios (por ejemplo `recepcion_ficticia` / `clave-ficticia-123`, y secretos de 32 caracteres o más rotulados como ficticios).

## 1. Red de seguridad y dependencias

- [x] 1.1 Correr `pytest tests` antes de tocar nada y registrar el baseline, verificando que todos los tests actuales (dominio de C-10 y API de C-01) pasan. Si alguno falla, se reporta como falla previa y no se corrige en este change.
- [x] 1.2 Agregar `PyJWT>=2.10` y `pwdlib[argon2]>=0.2` a `requirements.txt` e instalarlas en el `.venv`, verificando que `pip install -r requirements.txt` termina sin error, que `python -c "import jwt, pwdlib; from pwdlib.hashers.argon2 import Argon2Hasher"` funciona y que `pytest tests` sigue en verde.

## 2. Ajustes a la base técnica de C-01

- [x] 2.1 _(check_same_thread=False resuelto por Belén en PR #31; este test cubre el cierre desde otro hilo: `test_abrir_conexion_se_puede_cerrar_desde_otro_hilo`)_ Escribir en `tests/api/test_conexion.py` un test que abre una conexión con `abrir_conexion` en el hilo principal y ejecuta `SELECT 1` y `close()` desde un `threading.Thread`. Verificar que falla en RED con `ProgrammingError`. Después pasar `check_same_thread=False` en `abrir_conexion` y su docstring, verificando que el test nuevo y los 5 tests existentes de conexión pasan.
- [x] 2.2 Escribir tests en `tests/api/test_config.py` para los defaults de autenticación (entorno vacío → `HS256`, `60` minutos, sin contraseña de seed, secreto no vacío) y para un `JWT_SECRET` explícito, que se respeta tal cual. Sumar los campos a `Config` y a `cargar_config`, verificando que los tests nuevos y los 3 existentes pasan.
- [x] 2.3 Escribir tests de que `APP_ENV=test` sin `JWT_SECRET` produce dos secretos distintos en dos cargas, y de que `APP_ENV=production` sin `JWT_SECRET` lanza `ConfigInvalida` con un mensaje que nombra `JWT_SECRET`. Implementar el secreto aleatorio solo para `development`/`test`, verificando que ningún secreto queda escrito en el código (búsqueda en `app/config.py`).
- [x] 2.4 Escribir tests de que `ACCESS_TOKEN_EXPIRE_MINUTES=abc` y `=0`, y `JWT_ALGORITHM=none`, lanzan `ConfigInvalida` con un mensaje que nombra la variable, y de que `HS512` se acepta. Implementar las validaciones, verificando que los tests pasan.
- [x] 2.5 Escribir tests de que `GET /docs` y `GET /openapi.json` responden `200` con `APP_ENV=development` y `404` con `APP_ENV=test`. Condicionar `docs_url`, `redoc_url` y `openapi_url` en `create_app`, verificando que los tests pasan y que `tests/api/test_main.py` sigue en verde.

## 3. Formato global de errores (RN-GLO-01)

- [x] 3.1 Crear `tests/api/rutas_prueba.py` con un router solo de test con rutas que lanzan `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo` y `DatoInvalido`, y la fixture `cliente_con_rutas_prueba` en `tests/conftest.py`. Escribir tests de que cada ruta responde `409` (`conflicto_agenda`, `fuera_de_horario`, `dentro_de_bloqueo`) o `422` (`dato_invalido`) con exactamente `{codigo, mensaje}` y el `mensaje` del error de dominio. Implementar `registrar_manejadores` en `app/api/errores.py` con la tabla de mapeo de dominio y llamarla desde `create_app`, verificando que los tests pasan.
- [x] 3.2 Escribir un test que recorre las subclases de `ErrorDominio` y verifica que todas tienen entrada en la tabla de mapeo, y otro que verifica que una subclase sin mapeo (definida en el test) responde `500` con `codigo` `error_interno`. Implementar el fallback, verificando que los tests pasan.
- [x] 3.3 Escribir tests de que `GET /no-existe` responde `404` con `codigo` `no_encontrado` y de que un método no admitido sobre una ruta de prueba responde `405` con `metodo_no_permitido`, ambos sin la clave `detail`. Implementar el handler de `StarletteHTTPException`, verificando que los tests pasan.
- [x] 3.4 Escribir tests sobre una ruta de prueba con un body Pydantic: `{}` devuelve `422` `dato_invalido` con `detalles` para cada campo faltante ("Campo obligatorio."), y un tipo incorrecto devuelve `detalles` con `campo` sin el prefijo `body` y `mensaje` en español. Un error de todo el cuerpo (body que no es un objeto o JSON mal formado) devuelve `campo` `"body"`. Implementar el handler de `RequestValidationError` con el diccionario de mensajes por `type`, verificando que los tests pasan.
- [x] 3.5 Definir `ErrorApi`, `NoAutenticado`, `SinPermiso` y `CredencialesInvalidas` en `app/api/errores.py`, con tests sobre rutas de prueba que las lanzan. Verificar que responden `401` (`no_autenticado` / `credenciales_invalidas`) con la cabecera `WWW-Authenticate: Bearer` y `403` (`sin_permiso`) sin esa cabecera, todas en formato `{codigo, mensaje}`.

## 4. Usuarios en dominio y persistencia

- [x] 4.1 Escribir tests en `tests/domain/test_usuarios.py` de que `Rol` tiene exactamente `administracion`, `recepcion` y `odontologo`, y de que `Usuario` es inmutable y no tiene atributo `password_hash`. Implementar `app/domain/usuarios.py` en Python puro, verificando que los tests pasan y que el módulo no importa `fastapi`, `app.db` ni `app.api`.
- [ ] 4.2 Escribir tests en `tests/api/test_esquema_usuario.py` (base temporal + `inicializar_esquema`):
  - la tabla `usuario` existe después del arranque;
  - un `username` duplicado lanza `IntegrityError`;
  - el rol `paciente` lanza `IntegrityError`;
  - un administrador con `profesional_id` NULL se inserta sin error;
  - aplicar el esquema dos veces no falla.

  Agregar la tabla a `esquema.sql` con el comentario sobre la ausencia de FK, verificando que los tests pasan.
- [ ] 4.3 Escribir tests en `tests/api/test_repositorio.py`:
  - `insertar_usuario` devuelve el id;
  - `buscar_credenciales` devuelve `(Usuario, hash)` para un username existente y `None` para uno inexistente;
  - `buscar_usuario_por_id` devuelve el usuario con su `activo` y su `rol` actuales.

  Implementar `app/db/repositorio.py` con consultas parametrizadas, verificando que los tests pasan y que no hay SQL armado con f-strings ni con `%` (búsqueda en el archivo).

## 5. Hash y token (sin HTTP)

- [ ] 5.1 Escribir tests en `tests/api/test_seguridad.py`:
  - `hashear("clave-ficticia-123")` no es igual a la contraseña ni la contiene;
  - dos hashes de la misma contraseña son distintos;
  - `verificar` acepta la contraseña correcta y rechaza `otra-clave-ficticia`.

  Implementar `hashear` y `verificar` con `pwdlib` Argon2id, verificando que los tests pasan (RN-ACC-04).
- [ ] 5.2 Escribir tests de `emitir_token(..., ahora)` y `decodificar_token(..., ahora)`, con `ahora` como **parámetro obligatorio** y un instante fijo `T` (por ejemplo `2026-01-05T12:00:00+00:00`):
  - la ida y vuelta en `T` conserva `sub` (string) y `rol`;
  - `exp - iat` es igual a `ACCESS_TOKEN_EXPIRE_MINUTES` minutos;
  - un token emitido en `T`, decodificado con `ahora = T + 59 min`, es válido;
  - con `ahora = T + 60 min` (el límite exacto) lanza `TokenVencido`;
  - con `ahora = T - 1 min` (`iat` en el futuro) es inválido;
  - un token firmado con otra clave, uno con `alg: none` y uno sin `sub` lanzan error.

  Implementar con PyJWT (`algorithms` fijo, `verify_exp`/`verify_iat` desactivados) y la comparación de tiempo propia contra `ahora`, verificando que los tests pasan y que `app/api/seguridad.py` no llama a `datetime.now`.

## 6. Login y autorización

- [ ] 6.1 Implementar `obtener_conexion` en `app/api/dependencias.py` (abre la conexión, hace `yield` y cierra en `finally`), con un test sobre una ruta de prueba que la usa. Verificar que la ruta responde sin `ProgrammingError` de hilo y que la conexión queda cerrada después del request.
- [ ] 6.1b Agregar a `tests/conftest.py` `RelojFijo` (instante inicial fijo en UTC, `__call__` y `avanzar(minutes=...)`) y la fixture `reloj`, y hacer que `cliente` y `cliente_con_rutas_prueba` pasen `reloj` a `create_app`. Escribir tests de que una ruta de prueba que depende de `obtener_ahora` devuelve el instante del `RelojFijo`, y de que avanza después de `avanzar(...)`. Implementar el parámetro `reloj` de `create_app` (guardado en `app.state.reloj`, default `datetime.now(timezone.utc)`) y `obtener_ahora` en `app/api/dependencias.py`, verificando que los tests pasan y que el default de `create_app` es el único lugar de `app/` que lee la hora real.
- [ ] 6.2 Agregar a `tests/conftest.py` las fixtures `crear_usuario` (que inserta un usuario ficticio con hash real) y `token_de` (que emite un token para un usuario usando el instante actual del `RelojFijo`). Escribir el test de que `POST /auth/login` con `recepcion_ficticia` / `clave-ficticia-123` responde `200` con `token_type` `bearer` y un `access_token` decodificable con el id y el rol del usuario. Implementar el router de `app/api/auth.py` y montarlo en `create_app`, verificando que el test pasa.
- [ ] 6.3 Escribir tests de que el login con un usuario inexistente, con una contraseña incorrecta y con un usuario inactivo responde `401` `credenciales_invalidas`, y de que los tres cuerpos son **idénticos**. Implementar la verificación contra el hash ficticio cuando el usuario no existe, verificando que los tests pasan.
- [ ] 6.4 Escribir tests de que `POST /auth/login` con `{}`, con `password` faltante y con `password` numérico responde `422` `dato_invalido` con `detalles` del campo correspondiente. Verificar que pasan con el handler del grupo 3 y el modelo Pydantic con `min_length=1`.
- [ ] 6.5 Escribir tests sobre `GET /prueba/autenticado`: sin cabecera, con `Basic ...`, con texto arbitrario y con un token firmado con otra clave, todos `401` `no_autenticado` con la cabecera `WWW-Authenticate: Bearer`. Con un token válido debe responder `200`. Implementar `usuario_actual` con `HTTPBearer(auto_error=False)`, validando el token con `obtener_ahora`, verificando que los tests pasan (RN-ACC-01).
- [ ] 6.5b Escribir el test de **token vencido moviendo el reloj fijo, sin esperar**:
  - login de `recepcion_ficticia` con el `RelojFijo` en `T` (`ACCESS_TOKEN_EXPIRE_MINUTES=60`);
  - `reloj.avanzar(minutes=59)` → `GET /prueba/autenticado` responde `200`;
  - `reloj.avanzar(minutes=1)` (en `T + 60`) → responde `401` `no_autenticado` con `WWW-Authenticate: Bearer`.

  Verificar que el test pasa, que no usa `sleep` y que su resultado no cambia con la hora real de la máquina.
- [ ] 6.6 Escribir tests de que un token válido de un usuario desactivado después del login responde `401` `no_autenticado`, y de que un usuario cuyo rol cambió de `recepcion` a `odontologo` después del login recibe `403` en `GET /prueba/solo-recepcion`. Verificar que `usuario_actual` recarga el usuario desde la base y usa el rol guardado, no el del token.
- [ ] 6.7 Escribir tests de que `recepcion_ficticia` recibe `403` `sin_permiso` en `GET /prueba/solo-admin` y `200` en `GET /prueba/admin-o-recepcion`, y de que un `administracion_ficticia` recibe `200` en `solo-admin`. Implementar `requiere_rol(*roles)`, verificando que los tests pasan (RN-ACC-02, mecanismo).
- [ ] 6.8 Escribir un test de punta a punta: crear `recepcion_ficticia` y loguearse; verificar que la fila de `usuario` no contiene `clave-ficticia-123` en ninguna columna y que la respuesta del login tampoco la contiene (RN-ACC-04). Verificar también que `GET /health` sigue respondiendo `200` sin token.

## 7. Seed de desarrollo

- [ ] 7.1 Escribir tests en `tests/api/test_seed.py` de `sembrar_admin_demo` sobre una base temporal: la primera llamada crea un único `admin_demo` activo con rol `administracion`, y la segunda llamada con otro hash no crea duplicados ni cambia el `password_hash`. Implementar `app/db/seed.py` con `INSERT ... ON CONFLICT(username) DO NOTHING` dentro de `transaccion()`, verificando que los tests pasan y que `app/db/seed.py` no importa `app.api`.
- [ ] 7.2 Escribir tests de arranque:
  - con `APP_ENV=development` y `SEED_ADMIN_PASSWORD=clave-demo-ficticia` existe `admin_demo`, y `POST /auth/login` con esas credenciales responde `200`;
  - dos arranques sobre la misma base dejan un solo `admin_demo`;
  - con `APP_ENV=test` y la variable definida, la tabla queda vacía;
  - con `development` sin la variable, el arranque no falla y la tabla queda vacía.

  Conectar el seed en el `lifespan`, verificando que los tests pasan.

## 8. Documentación

- [ ] 8.1 **Edición manual de un integrante** (los permisos del agente no permiten leer ni escribir `.env.example`): agregar a `.env.example` los placeholders
  - `JWT_SECRET=<cambiar-por-un-valor-largo-y-aleatorio-de-32-caracteres-o-mas>`
  - `JWT_ALGORITHM=HS256`
  - `ACCESS_TOKEN_EXPIRE_MINUTES=60`
  - `SEED_ADMIN_PASSWORD=<definir-localmente>`

  Verificar que `git diff .env.example` muestra solo placeholders y que `git status` no lista ningún `.env`.
- [ ] 8.2 Actualizar `README.md`:
  - las variables nuevas en la tabla y en los ejemplos de PowerShell y bash;
  - que sin `JWT_SECRET` fuera de development/test la app no arranca;
  - cómo crear `admin_demo` en desarrollo;
  - un ejemplo de `POST /auth/login` y del uso de `Authorization: Bearer`;
  - el formato de error `{codigo, mensaje, detalles?}`;
  - que `/docs` existe solo en development;
  - la sección "Estructura" con los archivos nuevos.

  Verificar que el ejemplo de login documentado funciona contra `uvicorn app.main:app` con `admin_demo`.

## 9. Verificación del change

- [ ] 9.1 Correr `pytest tests` completo, verificando que pasan los tests del baseline de 1.1 y todos los nuevos, y que cada RN tocada (RN-ACC-01, RN-ACC-02 en su mecanismo, RN-ACC-04 y RN-GLO-01) tiene al menos un test.
- [ ] 9.2 Verificar con una búsqueda de imports que `app/domain/` no importa `fastapi`, `jwt`, `pwdlib`, `app.db` ni `app.api`, y que `app/db/` no importa `fastapi` ni `app.api`.
- [ ] 9.3 Verificar que no hay secretos versionados (búsqueda de `JWT_SECRET=` con valores reales y de contraseñas en `app/` y `tests/`), y que todos los usuarios y contraseñas de los tests están rotulados como ficticios.
- [ ] 9.4 Verificar con una búsqueda en `tests/` que ningún test usa `time.sleep`, `datetime.now`, `datetime.utcnow`, `date.today` ni `time.time`, y en `app/` que la única lectura de la hora real es el default del `reloj` en `create_app`.
- [ ] 9.5 Correr `openspec validate c-03-auth-login-roles --strict`, verificando que no reporta errores.

## Workflow follow-up

- Implementar con `/opsx:apply c-03-auth-login-roles`, respetando las reglas duras de `AGENTS.md` y el checkpoint con el equipo al cierre de cada grupo (governance CRÍTICO).
- Verificar el change antes de archivar: suite en verde, login de `admin_demo` en development y `/health` respondiendo.
- Archivar con `/opsx:archive` y marcar `C-03` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
