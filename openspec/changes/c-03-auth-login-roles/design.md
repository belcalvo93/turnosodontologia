# Design — C-03 auth-login-roles

## Context

Motivación y alcance: ver `proposal.md`. Decisiones relevadas y confirmadas por el equipo: ver `explore.md`. Requisitos: ver `specs/acceso-usuarios`, `specs/errores-api` y `specs/base-tecnica`.

Estado que condiciona el diseño:

- C-01 dejó `create_app(config)` con `lifespan`, `Config` frozen construida por `cargar_config(entorno)` (inyectable), `abrir_conexion` / `transaccion` / `inicializar_esquema` en `app/db/conexion.py`, y un `esquema.sql` sin tablas.
- `app/main.py` ejecuta `app = create_app()` al importarse, y `tests/api/test_main.py` importa ese módulo sin variables de entorno.
- Todavía no hay ninguna dependencia de conexión por request: C-03 es el primer change que lee la base dentro de un request.
- Regla de capas (KB 08): `api → domain + db`, `db → domain` (solo tipos), `domain → nada`.
- FastAPI 0.162: `HTTPBearer()` sin header responde 401, pero con `{"detail": "Not authenticated"}` en inglés.
- SQLite con `foreign_keys=ON` rechaza cualquier INSERT en una tabla que tenga una FK hacia una tabla inexistente, incluso con valor `NULL`.

## Goals / Non-Goals

**Goals:**
- Que emitir y validar el token esté aislado en un solo módulo, para poder cambiar de mecanismo (riesgo D-03) sin tocar los routers.
- Que los routers de C-04 en adelante se protejan con una sola línea por ruta (`Depends(requiere_rol(...))`).
- Que todo error, propio o del framework, salga en el formato `{codigo, mensaje, detalles?}`.
- Que las funciones de hash y de token se puedan probar sin HTTP ni base.
- Que ningún test dependa de la hora real ni de esperar: el tiempo entra por parámetro o por un reloj inyectado en la app (decisión 11).

**Non-Goals:**
- Refresh tokens, logout, revocación y denylist.
- Rate limiting o bloqueo por intentos fallidos.
- Traducir de forma exhaustiva todos los tipos de error de Pydantic: se cubren los frecuentes y el resto usa un mensaje genérico.
- Capturar excepciones no previstas (que no sean `ErrorDominio`) para convertirlas al formato propio: siguen el comportamiento por defecto (500).

## Estructura

```
app/
  config.py            [mod] + jwt_secret, jwt_algorithm, access_token_expire_minutes,
                             seed_admin_password; ConfigInvalida
  main.py              [mod] create_app(config, reloj=None); docs solo en dev,
                             registrar_manejadores(), router auth, seed en lifespan
  domain/
    usuarios.py        [nuevo] Rol (StrEnum), Usuario (dataclass frozen) — Python puro
  db/
    conexion.py        [mod] abrir_conexion(..., check_same_thread=False)
    esquema.sql        [mod] CREATE TABLE IF NOT EXISTS usuario (...)
    repositorio.py     [nuevo] insertar_usuario, buscar_credenciales, buscar_usuario_por_id
    seed.py            [nuevo] sembrar_admin_demo(conexion, password_hash)
  api/
    seguridad.py       [nuevo] hashear, verificar, emitir_token, decodificar_token (sin FastAPI)
    dependencias.py    [nuevo] obtener_conexion (yield; abre y cierra por request),
                               obtener_ahora (lee app.state.reloj)
    auth.py            [nuevo] router POST /auth/login, usuario_actual, requiere_rol(*roles)
    errores.py         [nuevo] NoAutenticado, SinPermiso, CredencialesInvalidas,
                               registrar_manejadores(app)
tests/
  conftest.py          [mod] RelojFijo + fixture reloj; fixtures crear_usuario, token_de,
                             cliente_con_rutas_prueba (todas con el reloj fijo)
  api/rutas_prueba.py  [nuevo] router SOLO de test: rutas protegidas y rutas que lanzan
                               errores de dominio
```

```
request --> HTTPBearer(auto_error=False) --> usuario_actual
                                               |-- sin credencial / no "Bearer"    --> NoAutenticado (401)
                                               |-- decodificar_token(token, ahora) --> NoAutenticado (401)
                                               |   falla (firma/claims/vencido)     (ahora = obtener_ahora)
                                               |-- repositorio: no existe/inactivo --> NoAutenticado (401)
                                               v
                                             Usuario (rol leído de la DB)
                                               v
                                         requiere_rol(*roles) --rol no admitido--> SinPermiso (403)
                                               v
                                             router
```

## Decisions

### 1. Token: JWT HS256 con PyJWT; el usuario se recarga desde la base en cada request
- Claims: `sub` = id del usuario **como string**, `rol`, `iat` y `exp`. PyJWT ≥ 2.10 exige que `sub` sea string.
- `decodificar_token(token, config, ahora)` llama a `jwt.decode(..., algorithms=[config.jwt_algorithm], options={"require": ["exp", "iat", "sub"], "verify_exp": False, "verify_iat": False})`. Pasar una lista fija de algoritmos bloquea `alg: none` y la confusión de algoritmos. La firma y la presencia de los claims las sigue verificando PyJWT; el **tiempo** lo verificamos nosotros contra `ahora` (ver decisión 11).
- `emitir_token(usuario, config, ahora)` recibe `ahora` de forma **obligatoria**, sin default. Usa UTC, porque `exp` del JWT es epoch UTC; la zona del consultorio no interviene.
- `usuario_actual` usa el `sub` para recargar el usuario. El `rol` del token es solo informativo: autoriza el que está guardado en la base. Así `activo` y los cambios de rol se aplican en el acto, y eso acota la desventaja de no poder revocar tokens.
- Alternativas descartadas (ver explore D3-1): token opaco en la base (otra tabla y su limpieza) y sesión con cookie (necesita CSRF; el MVP es solo API). Descartamos `python-jose` porque está sin mantenimiento.

### 2. Configuración de autenticación sin secretos versionados
- `cargar_config` suma los cuatro campos. Si falta `JWT_SECRET`:
  - en `development` o `test`, se genera `secrets.token_urlsafe(32)`. Es distinto en cada carga, y los tokens se invalidan al reiniciar, lo cual es aceptable fuera de producción;
  - en cualquier otro entorno, lanza `ConfigInvalida` nombrando la variable. Como `app = create_app()` corre al importar `app.main`, uvicorn falla al arrancar.
- `JWT_ALGORITHM` solo admite `HS256`, `HS384` o `HS512` (el secreto es simétrico). `ACCESS_TOKEN_EXPIRE_MINUTES` tiene que ser un entero mayor que 0. Cualquier otro valor lanza `ConfigInvalida`.
- `ConfigInvalida` hereda de `ValueError` y vive en `app/config.py`.

### 3. Hash: Argon2id con `pwdlib[argon2]`
- `seguridad.hashear(password)` y `seguridad.verificar(password, hash)` envuelven `PasswordHash((Argon2Hasher(),))`. Aislarlo en dos funciones permite cambiar el algoritmo.
- **Contra la enumeración de usuarios**: si el username no existe, igual se verifica la contraseña contra un hash ficticio, calculado una sola vez de forma perezosa (`functools.cache`). Usuario inexistente, contraseña incorrecta y usuario inactivo lanzan la misma `CredencialesInvalidas`.
- Descartamos passlib (sin mantenimiento, depende de `crypt`, que no existe desde Python 3.13) y bcrypt (trunca a 72 bytes).

### 4. Login con JSON y `HTTPBearer(auto_error=False)`
- El body es un modelo Pydantic `{username: str (min_length=1), password: str (min_length=1)}` y la respuesta es `{access_token, token_type: "bearer"}`.
- Con `auto_error=False`, una credencial ausente llega como `None` y la convertimos en nuestro `NoAutenticado`. Así no dependemos del comportamiento de cada versión de FastAPI, que cambió de 403 a 401.
- Descartamos `OAuth2PasswordRequestForm`: obliga a sumar `python-multipart` y deja un único endpoint con form-encoding.

### 5. Conexión por request: `check_same_thread=False`
- `obtener_conexion(request)` abre `abrir_conexion(request.app.state.config.database_path)`, hace `yield` y la cierra en `finally`.
- FastAPI puede ejecutar la parte inicial de la dependencia, el endpoint y el cierre en hilos distintos del threadpool. Por eso `abrir_conexion` pasa `check_same_thread=False`. Es seguro porque cada conexión pertenece a un solo request y nunca se comparte.
- Descartamos endpoints `async`, porque bloquearían el event loop con I/O síncrona de `sqlite3`.
- El login solo lee, así que no abre transacción. El seed escribe dentro de `transaccion()`.

### 6. Tabla `usuario`

```sql
CREATE TABLE IF NOT EXISTS usuario (
    id             INTEGER PRIMARY KEY,
    username       TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    rol            TEXT    NOT NULL CHECK (rol IN ('administracion', 'recepcion', 'odontologo')),
    -- Sin FK a propósito y de forma definitiva: SQLite no permite agregar una FK a una
    -- tabla existente sin rehacerla y no hay migraciones. C-07 valida en la aplicación
    -- que el profesional exista al crear o editar un usuario odontólogo.
    profesional_id INTEGER NULL,
    activo         INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);
```

- `Rol` (StrEnum) y `Usuario` (dataclass frozen, **sin** `password_hash`) viven en el nuevo `app/domain/usuarios.py`. Un archivo propio evita conflictos con `models.py`, que es territorio de C-02 y avanza en paralelo.
- `buscar_credenciales(conexion, username)` devuelve `(Usuario, password_hash) | None`, así el hash nunca viaja dentro del objeto de dominio.
- Todas las consultas van parametrizadas (regla dura 4).

### 7. Errores: `{codigo, mensaje, detalles?}`

`registrar_manejadores(app)` en `app/api/errores.py`:

| Excepción | Status | `codigo` | `mensaje` |
|---|---|---|---|
| `CredencialesInvalidas` | 401 + `WWW-Authenticate: Bearer` | `credenciales_invalidas` | "Usuario o contraseña incorrectos." |
| `NoAutenticado` | 401 + `WWW-Authenticate: Bearer` | `no_autenticado` | "Se requiere un token de acceso válido." |
| `SinPermiso` | 403 | `sin_permiso` | "Tu rol no tiene permiso para esta operación." |
| `ConflictoAgenda` | 409 | `conflicto_agenda` | `str(exc)` (el dominio ya lo trae en español) |
| `FueraDeHorario` | 409 | `fuera_de_horario` | `str(exc)` |
| `DentroDeBloqueo` | 409 | `dentro_de_bloqueo` | `str(exc)` |
| `DatoInvalido` | 422 | `dato_invalido` | `str(exc)` |
| `RequestValidationError` | 422 | `dato_invalido` | "Los datos enviados no son válidos." + `detalles` |
| `StarletteHTTPException` 404 / 405 | 404 / 405 | `no_encontrado` / `metodo_no_permitido` | texto fijo en español |
| `StarletteHTTPException` (otro status) | el mismo | `error_http` | texto fijo en español |
| `ErrorDominio` sin mapeo propio | 500 | `error_interno` | "Error interno." |

- El mapeo de los errores de dominio es una tabla `{clase: (status, codigo)}`. Un test recorre las subclases de `ErrorDominio` y verifica que cada una tenga entrada, para que un error nuevo no caiga en 500 sin que nadie lo note. El fallback a 500 (`error_interno`) es una red de seguridad, no un comportamiento esperado. **Aceptado por el equipo**, igual que los dos códigos 401 separados (`credenciales_invalidas` / `no_autenticado`) y la validación de `JWT_ALGORITHM` y `ACCESS_TOKEN_EXPIRE_MINUTES`.
- `detalles` de validación: `campo` es el `loc` de Pydantic sin el prefijo `body`, unido con `.`. `mensaje` sale de un diccionario por `type`:
  - `missing` → "Campo obligatorio."
  - `string_type` → "Debe ser un texto."
  - `string_too_short` → "No puede estar vacío."
  - `json_invalid` → "El cuerpo no es un JSON válido."
  - cualquier otro → "Valor inválido."
- `NoAutenticado`, `SinPermiso` y `CredencialesInvalidas` son errores de la capa API (heredan de una base `ErrorApi`), no de dominio.

### 8. `/docs` solo en development
- `FastAPI(docs_url=..., redoc_url=..., openapi_url=...)` reciben su valor solo si `config.app_env == "development"`, y `None` en cualquier otro entorno. Con `None`, FastAPI no registra la ruta y el request termina en el 404 del formato propio.

### 9. Seed de `admin_demo`
- En el `lifespan`, después de `inicializar_esquema`: si `app_env == "development"` y hay `seed_admin_password`, `main` calcula el hash (con `api/seguridad`) y llama a `db.seed.sembrar_admin_demo(conexion, hash)`.
- `sembrar_admin_demo` hace `INSERT ... ON CONFLICT(username) DO NOTHING` dentro de `transaccion()`. Es idempotente y no pisa la contraseña de un `admin_demo` que ya existe.
- `db` no importa nada de `api`: recibe el hash ya calculado.

### 10. Rutas protegidas solo de test
- `tests/api/rutas_prueba.py` define un router con:
  - `GET /prueba/solo-admin`: `requiere_rol(ADMINISTRACION)`;
  - `GET /prueba/admin-o-recepcion`;
  - `GET /prueba/solo-recepcion`;
  - `GET /prueba/autenticado`: solo `usuario_actual`;
  - rutas que lanzan cada error de dominio.
- La fixture `cliente_con_rutas_prueba` crea la app, monta ese router y abre el `TestClient`. Ninguna de estas rutas existe en `app/`.

### 11. Reloj inyectado: ningún test depende de la hora real ni de esperar
- **Problema**: si se deja que PyJWT valide `exp` e `iat`, los compara contra la hora real del sistema (no se le puede pasar un "ahora"). Un test de token vencido dependería del reloj real, aunque no espere.
- **Funciones puras** (`app/api/seguridad.py`): `emitir_token(..., ahora)` y `decodificar_token(..., ahora)` reciben `ahora: datetime` (UTC, con tzinfo) como **parámetro obligatorio**. Ninguna de las dos llama a `datetime.now()`.
  - Vencido: `exp <= ahora` → `TokenVencido`. En el instante exacto de `exp`, el token ya está vencido, por coherencia con los intervalos semiabiertos `[iat, exp)`.
  - Emitido en el futuro: `iat > ahora` → token inválido.
  - Ambos errores terminan en `NoAutenticado` (401).
- **Reloj configurable en la app**: `create_app(config, reloj=None)` guarda en `app.state.reloj` un `Callable[[], datetime]`. El default es `lambda: datetime.now(timezone.utc)`, y es **el único lugar** de `app/` que lee la hora real. Una dependencia `obtener_ahora(request)` en `app/api/dependencias.py` devuelve `request.app.state.reloj()`. El login la usa para emitir y `usuario_actual` para validar.
- **En los tests**: un `RelojFijo` (en `tests/conftest.py`) con un instante inicial fijo y `avanzar(minutes=...)`. La fixture `reloj` se inyecta en `create_app` y en las fixtures que emiten tokens. El vencimiento se prueba **moviendo el reloj fijo**, no esperando:
  - login en T → `avanzar(59)` → 200;
  - `avanzar(1)` (T+60) → 401 `no_autenticado`.
- Alternativas descartadas:
  - `freezegun` / `time-machine`: suman una dependencia y parchean la hora global en vez de hacer explícita la dependencia del tiempo.
  - Emitir con un `ahora` en el pasado y validar con la hora real: no espera, pero sigue dependiendo del reloj del sistema.
  - `ACCESS_TOKEN_EXPIRE_MINUTES` muy chico + `sleep`: lento y frágil.

## Risks / Trade-offs

- [No se pueden revocar los tokens antes de que venzan] → Duración de 60 min, y la recarga del usuario en cada request corta el acceso al desactivarlo. El logout queda fuera del MVP.
- [La base no garantiza la integridad de `profesional_id`] → C-07 la valida en la aplicación con tests propios. El comentario en `esquema.sql` documenta el motivo. C-03 no crea usuarios odontólogo.
- [Cada request protegido hace una lectura extra en la base] → Es una consulta por PK sobre SQLite local, de costo despreciable para el MVP.
- [Secreto aleatorio en dev: los tokens se invalidan al reiniciar] → Es aceptable en desarrollo. Quien quiera tokens estables define `JWT_SECRET` en su entorno.
- [PyJWT advierte si la clave HMAC tiene menos de 32 bytes] → El placeholder de `.env.example` pide un valor de 32 caracteres o más. Los tests usan secretos ficticios de 32 caracteres o más.
- [Argon2 hace más lentos los tests (~decenas de ms por hash)] → Los tests crean pocos usuarios por caso. Si la suite se vuelve lenta, se pueden bajar los parámetros de costo solo en los tests.
- [Sin rate limiting, el login admite fuerza bruta] → Deuda explícita, fuera del MVP.
- [Cambiar los 404/405 al formato propio afecta a clientes que esperaban `detail`] → Todavía no hay clientes: es el momento de fijar el contrato.

## Migration Plan

No hay datos para migrar. Una `turnos.db` local existente recibe la tabla `usuario` al próximo arranque (`CREATE TABLE IF NOT EXISTS`). Rollback: revertir el change y, si hace falta, borrar la `turnos.db` local (solo tiene datos ficticios).
