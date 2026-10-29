# Proposal — C-03 auth-login-roles

## Why

Hoy la API solo expone `GET /health`. No hay usuarios, login, token, autorización por rol ni un formato de error común, así que ningún recurso puede protegerse (RN-ACC-01/02) y cada router futuro tendría que inventar sus propios errores (RN-GLO-01).

Este change va ahora por dos motivos:

- Está en el **camino crítico** (`C-01 → C-03 → C-04 → …`) y es el único del GATE 3.
- **Bloquea a C-04, C-05 y C-06**, que solo pueden avanzar en paralelo cuando exista un mecanismo de autenticación y de chequeo de rol al que engancharse.

C-01 ya está archivado, así que no tiene dependencias pendientes. Su governance es **CRÍTICO**: todas las decisiones de diseño se relevaron y confirmaron con el equipo en `explore.md` antes de escribir este proposal.

## What Changes

- Nueva tabla `usuario` en `app/db/esquema.sql`: `id`, `username` único, `password_hash`, `rol` (CHECK con los tres roles), `profesional_id` `INTEGER NULL` **sin FK de forma definitiva** y `activo`. La existencia del profesional la valida C-07 en la aplicación.
- Contraseñas guardadas solo como hash Argon2id con sal; nunca en texto plano (RN-ACC-04).
- `POST /auth/login` con body JSON `{username, password}`, que devuelve un token firmado (JWT HS256) con el id de usuario, el rol y su vencimiento. Ante credenciales inválidas responde 401 con **el mismo mensaje** para usuario inexistente, contraseña incorrecta y usuario inactivo.
- Mecanismo de autorización reutilizable por los routers siguientes:
  - **usuario actual**: lee el token Bearer, responde 401 si falta, es inválido o está vencido, y **recarga el usuario desde la base en cada request**, así respeta `activo` y los cambios de rol;
  - **requiere rol**: responde 403 si el rol no está permitido.
- Mapeo global de errores a JSON en español con el formato `{codigo, mensaje, detalles?}` para errores de dominio (409/422), validación de entrada (422), autenticación (401), permisos (403) y errores HTTP (404/405) (RN-GLO-01).
- Configuración nueva: `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` y `SEED_ADMIN_PASSWORD`. Si falta `JWT_SECRET` en `development`/`test`, se genera uno aleatorio por proceso. **Si falta en cualquier otro entorno, la app no arranca.**
- Usuario `admin_demo` (rol administración), creado en el arranque **solo en `development`** a partir de `SEED_ADMIN_PASSWORD`, de forma idempotente.
- `/docs` y `/openapi.json` disponibles **solo en `development`** (03 §Rutas públicas).
- Dependencias nuevas: `PyJWT` y `pwdlib[argon2]`.

**Fuera de alcance:**
- `GET /auth/yo`: no está en el scope de CHANGES. Los tests de 401 y 403 usan una ruta protegida definida solo en los tests.
- Alta, edición y baja de usuarios por API (C-07), y usuarios odontólogo con `profesional_id`.
- Logout y revocación de tokens.
- Rate limiting del login.
- Las filas de la matriz RBAC de cada recurso: cada change las declara con el mecanismo de este change.

## Capabilities

### New Capabilities

- `acceso-usuarios`: autenticación y autorización de la API — usuarios con contraseña hasheada, login que emite un token, validación del token por request, chequeo de rol y usuario inicial de desarrollo.
- `errores-api`: contrato de errores de la API — formato JSON único en español con código estable para cada status de RN-GLO-01, más 404/405.

### Modified Capabilities

- `base-tecnica`:
  - Se agrega *Configuración de autenticación*: variables de JWT y del seed, y fallo de arranque sin `JWT_SECRET` fuera de development/test. *Configuración desde variables de entorno* no cambia.
  - Se agrega *Documentación OpenAPI solo en development*.
  - Se modifica *Conexión SQLite transaccional*: la conexión se puede usar desde un hilo distinto al que la abrió.
  - Se modifica *Esquema aplicado al arrancar*: deja de decir que el esquema no crea tablas.

## Impact

- **Código de C-01 que se modifica**:
  - `app/db/conexion.py`: `abrir_conexion` pasa a abrir con **`check_same_thread=False`**. FastAPI ejecuta las dependencias con `yield` y los endpoints síncronos en hilos del threadpool que pueden ser distintos, y `sqlite3` lanza `ProgrammingError` si una conexión se usa fuera del hilo que la creó. Es seguro porque cada request abre y cierra su propia conexión y nunca la comparte. Se agrega un test.
  - `app/config.py`: `Config` suma campos; se extienden los tests de `tests/api/test_config.py`.
  - `app/main.py`: `create_app` acepta un reloj inyectable (para validar vencimientos sin depender de la hora real en los tests), registra los handlers de error, monta el router de auth, condiciona `/docs` a `APP_ENV` y ejecuta el seed en el `lifespan`.
  - `app/db/esquema.sql`: primera tabla real (`usuario`).
  - `tests/conftest.py`: fixtures de usuarios ficticios, tokens por rol y una ruta protegida solo de test.
- **Código nuevo**: `app/api/auth.py`, `app/api/seguridad.py`, `app/api/dependencias.py`, `app/api/errores.py`, `app/db/repositorio.py`, `app/db/seed.py`, `app/domain/usuarios.py`, y `tests/api/rutas_prueba.py` (solo para tests).
- **API**: nuevo `POST /auth/login`. Todos los errores cambian de `{"detail": ...}` (default de FastAPI) a `{codigo, mensaje, detalles?}`. `/docs` deja de estar expuesto fuera de development.
- **Dependencias**: `PyJWT`, `pwdlib[argon2]` en `requirements.txt`.
- **Documentación**: `.env.example` (lo edita a mano un integrante, porque los permisos del agente bloquean ese archivo) y `README.md`.
- **Changes siguientes**: C-04 en adelante protegen sus rutas con el mecanismo de este change; C-07 valida `profesional_id` al crear usuarios odontólogo.
