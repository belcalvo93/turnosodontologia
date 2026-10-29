# Explore — C-03 auth-login-roles

> Resumen del relevamiento previo al propose. También guardado en Engram (topic `opsx/c-03-auth-login-roles/explore`).
> Durante la exploración no se escribió código. Solo se creó el change con `openspec new change` y este archivo.

## Problema

C-03 desbloquea todos los recursos protegidos (C-04, C-05 y C-06 esperan este change). Hoy la API tiene un único endpoint, `GET /health`, que es público, y no tiene usuarios, login, token, autorización por rol ni un formato de error común. El change tiene governance **CRÍTICO**: el código se escribe solo con aprobación explícita del equipo.

```
Cliente --POST /auth/login {username, password}--> api/auth.py --> db/repositorio (usuario)
        <-- 200 {access_token, token_type}             | verifica hash (argon2)
                                                        | firma JWT {sub, rol, iat, exp}
Cliente --GET /ruta  Authorization: Bearer <jwt>--> usuario_actual()  --401--> sin token / inválido / vencido / usuario inactivo
                                                     requiere_rol(...) --403--> rol sin permiso
                                                     router            --200
```

## Estado del repo al relevar

- Rama `joaquin-c03-auth-login-roles`, limpia. C-01 y C-10 están archivados; los specs vigentes son `base-tecnica` (4 req.) y `reglas-alta-turno`.
- Python local 3.13.7 con `.venv`; FastAPI **0.162.0**.
- Ninguna librería de auth está instalada: PyJWT, pwdlib, argon2-cffi, bcrypt, passlib y python-multipart faltan todas.
- `.env.example`: los permisos del agente no permiten leerlo. Hay que confirmar a mano qué placeholders tiene hoy.

## 1. Qué hay que construir y qué se reutiliza de C-01

### Se reutiliza

| Pieza de C-01 | Uso en C-03 |
|---|---|
| `app/config.py`: `Config` frozen + `cargar_config(entorno)` inyectable + `_DEFAULTS` | Sumar `jwt_secret`, `jwt_algorithm`, `access_token_expire_minutes`, `seed_admin_password`. Mismo patrón inyectable para tests. |
| `app/db/conexion.py`: `abrir_conexion`, `transaccion` (BEGIN IMMEDIATE), `inicializar_esquema` | Base para la dependencia de conexión por request y para el seed. |
| `app/db/esquema.sql` idempotente (`CREATE TABLE IF NOT EXISTS`) | Acá va la primera tabla real: `usuario`. |
| `app/main.py`: `create_app(config)` + `lifespan` + `app.state.config` | Montar el router de auth, registrar los handlers de error, correr el seed de desarrollo en el lifespan. |
| `app/domain/errores.py`: `ErrorDominio`, `DatoInvalido`, `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo` | El mapeo global de RN-GLO-01 los traduce (422 y 409). |
| `tests/conftest.py`: fixtures `config` (SQLite temporal) y `cliente` (TestClient con lifespan) | Se extienden con fixtures de usuario creado y token por rol. |

### Hay que construir

| Pieza | Dónde |
|---|---|
| Tabla `usuario` (`id`, `username` UNIQUE, `password_hash`, `rol` con CHECK, `profesional_id` nullable, `activo`) | `app/db/esquema.sql` |
| Funciones de acceso: buscar por username o por id, insertar usuario | `app/db/repositorio.py` (nuevo) |
| Rol (StrEnum) y `Usuario` (dataclass) como tipos de dominio | `app/domain/models.py`, Python puro |
| Hash y verificación de contraseñas | `app/api/auth.py` (o un `app/api/seguridad.py` interno) |
| Emisión y validación del token, aisladas para poder cambiar el mecanismo (riesgo D-03 en CHANGES) | `app/api/auth.py` |
| `POST /auth/login`, dependencias `usuario_actual` y `requiere_rol(*roles)` | `app/api/auth.py` |
| Dependencia de conexión por request (no existe todavía) | `app/api/` (dependencia) |
| Handlers globales de error en español (RN-GLO-01) | `app/api/errores.py` (nuevo) + registro en `create_app` |
| Seed de `admin_demo` desde `SEED_ADMIN_PASSWORD`, solo en `development` e idempotente | `app/db/seed.py` (nuevo) |
| Variables nuevas con placeholders | `.env.example`, `README` |
| Dependencias nuevas | `requirements.txt` |

### Fuera del scope listado (decidido)

- ✅ **`/docs` solo en desarrollo — ENTRA en C-03** (03 §Rutas públicas): hoy `/docs` y `/openapi.json` quedan expuestos en cualquier entorno. Se resuelve con `docs_url`/`openapi_url` condicionados a `APP_ENV`.
- ❌ **`GET /auth/yo` — NO ENTRA**: no figura en el scope de C-03 en CHANGES.md. Los tests de 401 y 403 usan una ruta protegida que se define solo en los tests.

## 2. Decisiones abiertas

### D3-1 — Mecanismo de token (D-03 / SE-17)

| Opción | A favor | En contra |
|---|---|---|
| **JWT HS256 sin estado** | Es el candidato de la KB; `JWT_*` ya está en 08; no necesita tabla. | Revocarlo es difícil: un logout real necesita una denylist. |
| Token opaco guardado en DB | Se revoca borrando la fila; logout trivial. | Otra tabla, limpieza de vencidos, lectura de DB en cada request. |
| Sesión con cookie | Cómodo para un navegador. | Requiere CSRF; el MVP es solo API. |

> **Estado: CONFIRMADO por el equipo** — JWT recargando el usuario desde la base en cada request, para que se respeten `activo` y los cambios de rol.

**Decisión: JWT HS256** con claims `sub` (id de usuario como string), `rol`, `iat` y `exp`, y vida corta (`ACCESS_TOKEN_EXPIRE_MINUTES=60`). La mitigación clave: `usuario_actual` **recarga el usuario desde la DB en cada request**. Con eso:
- un usuario desactivado (`activo=0`) pierde el acceso en el acto (401), lo que achica el problema de revocación;
- el rol que vale es **el de la DB**, no el del token, así que un cambio de rol se aplica sin esperar al vencimiento. El `rol` queda en el token porque lo pide el scope, pero solo como dato informativo.

**Librería: PyJWT** (`PyJWT>=2.8`). La documentación actual de FastAPI la usa; `python-jose` está sin mantenimiento. Al decodificar, pasar siempre `algorithms=[config.jwt_algorithm]` fijo (eso bloquea `alg: none` y la confusión de algoritmos) y exigir `exp` y `sub`.

**`JWT_SECRET` faltante** (✅ CONFIRMADO): no debe haber un secreto por defecto en el código, porque sería un secreto versionado (regla dura 9). Hay que considerar que `app/main.py` ejecuta `app = create_app()` al importarse, y los tests importan ese módulo sin variables de entorno. Propuesta: en `development`/`test` sin `JWT_SECRET`, generar uno aleatorio por proceso (`secrets.token_urlsafe(32)`; los tokens se invalidan al reiniciar, lo que en desarrollo está bien); en cualquier otro entorno, fallar al arrancar.

### D3-2 — Algoritmo de hash

| Opción | Comentario |
|---|---|
| **Argon2id con `pwdlib[argon2]`** | Es lo que usa hoy el tutorial de FastAPI; `pwdlib` envuelve `argon2-cffi` con una API de dos funciones y re-hash. |
| Argon2id con `argon2-cffi` directo | Una capa menos, mismo algoritmo. |
| bcrypt (`bcrypt` directo) | Válido, pero trunca a 72 bytes. |
| passlib | **Descartar**: sin mantenimiento, se rompe con bcrypt ≥ 4.1 y depende de `crypt`, que no existe desde Python 3.13. |

> **Estado: CONFIRMADO por el equipo.**

**Decisión: Argon2id con `pwdlib[argon2]`**. Hay que aislarlo en dos funciones (`hashear`, `verificar`) para poder cambiarlo.

**Detalle de seguridad**: cuando el username no existe, igual se verifica contra un hash ficticio, para que el tiempo de respuesta no revele qué usuarios existen. Usuario inexistente, contraseña incorrecta y usuario inactivo devuelven **el mismo 401 con el mismo mensaje**.

### D3-3 — Body del login: JSON o formulario

| Opción | A favor | En contra |
|---|---|---|
| **JSON con Pydantic** `{username, password}` | Igual al resto de la API; validación y 422 uniformes; sin dependencias nuevas. | El botón "Authorize" de Swagger no hace el login solo: hay que pegar el token. |
| Formulario (`OAuth2PasswordRequestForm`) | Swagger hace el login completo con `OAuth2PasswordBearer`. | Agrega `python-multipart`; es el único endpoint con form-encoding; sus 422 salen con otra forma. |

> **Estado: CONFIRMADO por el equipo** — body JSON con Pydantic + `HTTPBearer(auto_error=False)`.

**Decisión: JSON** con el esquema `HTTPBearer` para leer el header (Swagger muestra igual un campo para pegar el token). La respuesta es `{"access_token": "...", "token_type": "bearer"}`.

Verificado con FastAPI 0.162: `HTTPBearer()` sin header **ya devuelve 401** con `WWW-Authenticate: Bearer` (versiones viejas devolvían 403), pero el cuerpo es `{"detail": "Not authenticated"}`, en inglés. Se usa `HTTPBearer(auto_error=False)` y se lanza nuestro propio 401: no depende del comportamiento de cada versión.

### D3-4 — `profesional_id` cuando la tabla `profesional` llega recién en C-04

**Hallazgo verificado:** con `PRAGMA foreign_keys=ON`, una FK hacia una tabla que no existe **hace fallar todo INSERT en `usuario`, incluso con `profesional_id = NULL`** (`sqlite3.OperationalError: no such table: main.profesional`). Por eso **no se puede** declarar `REFERENCES profesional(id)` ya en C-03.

| Opción | A favor | En contra |
|---|---|---|
| **A. `profesional_id INTEGER NULL` sin FK, de forma definitiva.** La integridad la valida la aplicación en C-07. | Respeta el scope; es lo que planeó CHANGES ("C-03 crea la columna nullable; C-07 valida que exista el profesional"). No requiere rehacer tablas ni migraciones. | La base no garantiza la integridad referencial de esa columna: depende de que C-07 la valide en cada alta o edición de usuario. |
| B. Crear una tabla `profesional` mínima en C-03 | FK real desde el primer día. | Invade C-04 (governance distinto, otro integrante). |
| C. No crear la columna; agregarla en C-07 con `ALTER TABLE ... ADD COLUMN ... REFERENCES` | SQLite lo permite si el default es NULL. | `ALTER` no es idempotente y no hay migraciones: el segundo arranque falla. |

> **Estado: CONFIRMADO por el equipo, con un ajuste** a la recomendación original.

**Decisión: A, sin FK en ningún change.** C-04 **no** agrega la FK después: SQLite no permite agregar una FK a una tabla existente sin rehacerla (crear una tabla nueva, copiar los datos y renombrarla), y el proyecto no tiene sistema de migraciones. Por eso `profesional_id` queda como `INTEGER NULL` sin `REFERENCES` de forma permanente. Como dice el riesgo de CHANGES, **C-07 valida en la aplicación** que el profesional exista (y que esté activo, si así se define) al crear o editar un usuario odontólogo. También valida la regla "odontólogo ⇒ `profesional_id` obligatorio". `esquema.sql` lleva un comentario junto a la columna que explica por qué no tiene FK y quién valida la integridad. Queda descartada la recomendación original de que C-04 agregara `REFERENCES` reordenando `esquema.sql`. En C-03 solo se pone `CHECK (rol IN ('administracion','recepcion','odontologo'))` y `CHECK (activo IN (0,1))`.

### D3-5 — Formato del JSON de error (RN-GLO-01)

| Opción | Ejemplo |
|---|---|
| Default de FastAPI | `{"detail": "..."}`, o una lista en inglés para los 422 |
| **Propio y plano** | `{"codigo": "conflicto_agenda", "mensaje": "El turno se superpone con otro turno del profesional.", "detalles": [...]}` |
| RFC 9457 (problem+json) | `{"type","title","status","detail"}`: más formal, poco valor en un MVP |

> **Estado: CONFIRMADO por el equipo** — handlers para dominio, validación, HTTP y auth.

**Decisión: formato propio y plano**: `codigo` (string estable en snake_case, para máquinas), `mensaje` (en español, para personas) y `detalles` opcional (lista de `{campo, mensaje}` solo en 422 de validación). El status HTTP sigue siendo la fuente del código numérico.

Para que sea **global**, hay que registrar handlers para:

| Origen | Status | `codigo` |
|---|---|---|
| `DatoInvalido` | 422 | `dato_invalido` |
| `ConflictoAgenda` / `FueraDeHorario` / `DentroDeBloqueo` | 409 | `conflicto_agenda` / `fuera_de_horario` / `dentro_de_bloqueo` |
| `RequestValidationError` (Pydantic) | 422 | `dato_invalido` + `detalles` traducidos |
| Sin autenticar | 401 (+ `WWW-Authenticate: Bearer`) | `no_autenticado` |
| Rol sin permiso | 403 | `sin_permiso` |
| `StarletteHTTPException` 404 / 405 | 404 / 405 | `no_encontrado` / `metodo_no_permitido` |

`NoAutenticado` y `SinPermiso` son errores de la capa API, no del dominio, así que no van en `app/domain/errores.py`. Un `ErrorDominio` sin mapeo explícito debería caer en 422 o en 500: hay que decidir cuál en el design (recomiendo 500 y que un test haga explícito el mapeo de cada subclase).

## 3. Riesgos

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | **SQLite y el threadpool**: FastAPI corre las dependencias síncronas con `yield` y los endpoints síncronos en hilos que pueden ser distintos. `sqlite3` con `check_same_thread=True` (el default) lanza `ProgrammingError`. | Abrir la conexión por request con `check_same_thread=False` (es segura porque no se comparte entre requests). Implica tocar `abrir_conexion` de C-01, con su test. |
| R2 | `app = create_app()` al importar `app.main` hace que un `JWT_SECRET` obligatorio rompa la importación en los tests. | Ver D3-1: secreto aleatorio en `development`/`test`, fallo al arrancar en los demás entornos. |
| R3 | Enumeración de usuarios por mensaje o por tiempo de respuesta. | Mismo 401 y mismo mensaje; verificación contra un hash ficticio. |
| R4 | Confusión de algoritmo o `alg: none` en JWT. | `algorithms=[...]` fijo; test con un token `none` y otro firmado con otra clave. |
| R5 | Fuerza bruta sobre el login. | Fuera del MVP: dejarlo anotado como deuda (no hay rate limiting). |
| R6 | `profesional_id` no tiene FK: la base acepta ids de profesionales inexistentes. | Ver D3-4: C-07 valida la existencia en la aplicación (con tests propios); un comentario en `esquema.sql` lo documenta. Hasta C-07, C-03 no crea usuarios odontólogo (el seed solo crea `admin_demo`). |
| R7 | Matriz RBAC no validada (SE-12, alta). | C-03 solo entrega el mecanismo `requiere_rol`; cada router posterior declara su fila. No bloquea C-03, pero sigue abierta para C-04 en adelante. |
| R8 | Tests de token vencido que dependen del reloj real. | Emisión con `ahora` inyectable (la regla dura 2 es del dominio, pero el mismo patrón hace el test determinístico). |
| R9 | `config` crece: `test_config.py` puede comparar los campos exactos de `Config`. | Revisar y extender esos tests en la red de seguridad (Strict TDD, paso 0). |
| R10 | Advertencia de Starlette (`httpx` → `httpx2`) en el TestClient. | Es ruido, no es de C-03; anotarlo. |

## 4. Tests necesarios (cada RN con ≥1 test)

**Unitarios (sin HTTP):**
- Hash ≠ texto plano; `verificar` acepta la contraseña correcta y rechaza la incorrecta; dos hashes de la misma contraseña son distintos (sal). — RN-ACC-04
- Token: ida y vuelta conserva `sub` y `rol`; vencido → error (con `ahora` inyectado); firma con otra clave → error; `alg: none` → error; sin `exp` o sin `sub` → error.
- Config: defaults de las variables nuevas; `ACCESS_TOKEN_EXPIRE_MINUTES` no numérico → error; `JWT_SECRET` aleatorio en dev o test; fallo fuera de dev o test.

**DB:**
- La columna `password_hash` guardada no contiene la contraseña original. — RN-ACC-04
- `username` duplicado → `IntegrityError`; `rol` fuera del enum → `IntegrityError`.
- Insertar un usuario con `profesional_id NULL` funciona (cubre el hallazgo D3-4).

**API (TestClient + SQLite temporal):**
- `POST /auth/login` correcto → 200 con `access_token` y `token_type="bearer"`.
- Contraseña incorrecta, usuario inexistente o usuario inactivo → 401 con **cuerpo idéntico**.
- Body sin campos → 422 con `codigo="dato_invalido"`, `mensaje` en español y `detalles`.
- Ruta protegida sin header, con header mal formado, con token basura o con token vencido → 401 con `WWW-Authenticate: Bearer`. — RN-ACC-01
- Token válido de un usuario desactivado después del login → 401.
- Rol no permitido → 403 `sin_permiso`; rol permitido → 200. — RN-ACC-02 (mecanismo)
- `GET /health` sigue público.
- Un test por código de RN-GLO-01: 401, 403, 409 y 422 (el 409 con una ruta de test que lance `ConflictoAgenda`). Más 404 y 405 en formato español.
- `/docs` y `/openapi.json` → 404 cuando `APP_ENV` no es `development`; disponibles en `development`.
- Seed: con `development` y `SEED_ADMIN_PASSWORD` crea `admin_demo` una sola vez (idempotente); en `test` o sin la variable no crea nada.

Para probar `usuario_actual` y `requiere_rol` sin depender de routers de C-04 en adelante: un router mínimo con rutas protegidas, definido y montado **solo desde una fixture de test** (decidido; `GET /auth/yo` no entra).

## Resumen de recomendaciones

| Decisión | Estado | Valor |
|---|---|---|
| Token | ✅ Confirmada | JWT HS256 (PyJWT), 60 min; usuario y rol recargados de la DB en cada request (respeta `activo` y los cambios de rol) |
| `profesional_id` | ✅ Confirmada (con ajuste) | `INTEGER NULL` sin FK **de forma definitiva**; ningún change agrega la FK; C-07 valida la existencia del profesional en la aplicación |
| Hash | ✅ Confirmada | Argon2id con `pwdlib[argon2]` |
| Body de login | ✅ Confirmada | JSON con Pydantic + `HTTPBearer(auto_error=False)` |
| Error JSON | ✅ Confirmada | `{codigo, mensaje, detalles?}` plano, con handlers para dominio, validación, HTTP y auth (RN-GLO-01) |
| `JWT_SECRET` faltante | ✅ Confirmada | Aleatorio en `development`/`test`; fallo al arrancar en otros entornos |
| `/docs` | ✅ Confirmada | Solo en `development` (03 §Rutas públicas) — entra en C-03 |
| `GET /auth/yo` | ❌ Descartada | No está en el scope de CHANGES.md; los tests de 401/403 usan una ruta protegida definida solo en los tests |

Todas las decisiones del explore están confirmadas por el equipo.

**Siguiente paso:** `/opsx:propose c-03-auth-login-roles`.
