# Turnos Odontológicos

Backend académico para gestionar turnos de un consultorio odontológico (Trabajo de Integración, Metodología I, TUP – UTN FRM). Todos los datos de ejemplo son ficticios.

Desarrollado con Spec-Driven Development usando OpenSpec y Active Stack (ciclo OPSX).

## Estado actual

Implementados **C-01 `foundation-setup`**, **C-10 `reglas-alta-turno`** y **C-03 `auth-login-roles`**. La suite pasa en verde: `194 passed`.

**C-01 — base técnica:** configuración desde variables de entorno, conexión SQLite con transacciones atómicas (`BEGIN IMMEDIATE`, commit y rollback), aplicación del esquema al arrancar y `GET /health` público.

**C-10 — reglas de alta de turno** en dominio puro, sin base de datos ni HTTP:

- Calcula el fin del turno a partir de la duración de la prestación.
- Rechaza turnos fuera del horario de atención del profesional.
- Rechaza turnos dentro de un bloqueo del profesional o del sillón.
- Rechaza solapamientos por profesional, sillón o paciente, con intervalos semiabiertos `[inicio, fin)`: los turnos contiguos son válidos.

**C-03 — acceso y roles:**

- `POST /auth/login` con usuario y contraseña devuelve un token JWT firmado. Las contraseñas se guardan solo como hash Argon2id.
- Un login fallido responde siempre el mismo `401`, exista o no el usuario.
- Las rutas protegidas exigen `Authorization: Bearer <token>`. El usuario y su rol se recargan desde la base en cada request.
- `requiere_rol(...)` limita una ruta a ciertos roles (`administracion`, `recepcion`, `odontologo`).
- Todos los errores se devuelven como JSON en español con un código (ver [Formato de error](#formato-de-error)).

## Requisitos

- Git
- Python 3.11 o superior

No hace falta Docker ni base de datos.

## Instalación

```bash
git clone https://github.com/belcalvo93/turnosodontologia.git
cd turnosodontologia
python -m venv .venv
```

Activar el entorno virtual:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

> En Windows, si PowerShell muestra "la ejecución de scripts está deshabilitada", correr antes
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` (solo afecta a esa ventana).

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

> En Linux / macOS puede ser necesario usar `python3` en lugar de `python`.

## Variables de entorno

La configuración se lee del entorno del proceso. **No hay carga automática de `.env`**: el proyecto no usa `python-dotenv`, así que un archivo `.env` no se lee solo; usalo como referencia local junto con `.env.example` y exportá las variables antes de correr la API.

| Variable | Descripción | Default |
|----------|-------------|---------|
| `APP_ENV` | Entorno de ejecución (`development`, `test`, `production`, ...) | `development` |
| `DATABASE_URL` | Ruta de la base SQLite (acepta `sqlite:///ruta` o un path plano) | `./turnos.db` |
| `CLINIC_TIMEZONE` | Zona horaria del consultorio | `America/Argentina/Buenos_Aires` |
| `JWT_SECRET` | Clave para firmar los tokens: 32+ caracteres (64+ si usás `HS512`). **Obligatoria fuera de `development`/`test`** | Aleatoria por proceso en `development`/`test` |
| `JWT_ALGORITHM` | Algoritmo de firma: `HS256`, `HS384` o `HS512` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez del token (entero mayor que 0) | `60` |
| `SEED_ADMIN_PASSWORD` | Contraseña del usuario `admin_demo`, que se crea solo en `development` | Sin definir (no se crea) |

> **Sin `JWT_SECRET` la app no arranca fuera de `development`/`test`.** Con `APP_ENV=production`, por
> ejemplo, falla al iniciar con `ConfigInvalida: Falta la variable de entorno JWT_SECRET (obligatoria con APP_ENV=production).`
> En `development` y `test`, si falta, se genera un secreto aleatorio en cada arranque: los tokens
> emitidos dejan de valer al reiniciar la API.

Exportarlas en la sesión actual (valores de ejemplo, ficticios):

```powershell
# Windows (PowerShell)
$env:APP_ENV="development"
$env:DATABASE_URL="sqlite:///./turnos.db"
$env:CLINIC_TIMEZONE="America/Argentina/Buenos_Aires"
$env:JWT_SECRET="cambiar-por-un-secreto-propio-de-32-caracteres-o-mas"
$env:JWT_ALGORITHM="HS256"
$env:ACCESS_TOKEN_EXPIRE_MINUTES="60"
$env:SEED_ADMIN_PASSWORD="clave-demo-ficticia"
```

```bash
# Linux / macOS (bash)
export APP_ENV=development
export DATABASE_URL=sqlite:///./turnos.db
export CLINIC_TIMEZONE=America/Argentina/Buenos_Aires
export JWT_SECRET=cambiar-por-un-secreto-propio-de-32-caracteres-o-mas
export JWT_ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=60
export SEED_ADMIN_PASSWORD=clave-demo-ficticia
```

Verificar que la configuración se resuelve:

```bash
python -c "from app.config import cargar_config; print(cargar_config().database_path)"
```

Resultado esperado: `turnos.db` con los defaults (sin variables exportadas).

## Correr los tests

Desde la raíz del repositorio, con el entorno virtual activo:

```bash
pytest tests
```

Resultado esperado: `194 passed`. Los tests de dominio corren sin base de datos ni HTTP; los de `tests/api/` usan una SQLite temporal por test y un reloj fijo, así que no dependen de la hora de la máquina.

## Levantar la API

```bash
uvicorn app.main:app
```

`GET /health` responde `200` con `{"status": "ok"}`, sin token.

La documentación interactiva (`/docs`, `/redoc` y `/openapi.json`) existe **solo con `APP_ENV=development`**. En cualquier otro entorno esas rutas responden `404`.

### Usuario `admin_demo` en desarrollo

Para tener un usuario con el que loguearse, arrancá la API con `APP_ENV=development` y `SEED_ADMIN_PASSWORD` definida, como en los ejemplos de arriba. Al arrancar se crea `admin_demo`, con rol `administracion` y esa contraseña.

- Si `admin_demo` ya existe, no se modifica: cambiar `SEED_ADMIN_PASSWORD` después no le cambia la contraseña.
- En cualquier otro entorno, o sin la variable, no se crea ningún usuario.

### Login y uso del token

Con la API levantada como se explica arriba:

```powershell
# Windows (PowerShell)
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"username": "admin_demo", "password": "clave-demo-ficticia"}'
$login.access_token
```

```bash
# Linux / macOS (bash)
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_demo", "password": "clave-demo-ficticia"}'
```

Respuesta `200`:

```json
{"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
```

El token vence a los `ACCESS_TOKEN_EXPIRE_MINUTES` minutos. Las rutas protegidas se llaman con la cabecera `Authorization: Bearer <access_token>`:

```bash
curl http://127.0.0.1:8000/<ruta-protegida> -H "Authorization: Bearer <access_token>"
```

> Este change deja listo el mecanismo, pero todavía no hay rutas protegidas en la API: las agregan
> los changes C-04 en adelante. Sin token, con un token inválido o con uno vencido, una ruta protegida
> responde `401` `no_autenticado`; con un rol sin permiso, `403` `sin_permiso`.

### Formato de error

Todos los errores responden con el mismo JSON en español: `{codigo, mensaje, detalles?}`. `detalles` aparece solo en los errores de validación, con un elemento por campo.

Credenciales incorrectas (`401`, con la cabecera `WWW-Authenticate: Bearer`):

```json
{"codigo": "credenciales_invalidas", "mensaje": "Usuario o contraseña incorrectos."}
```

Body inválido (`422`), por ejemplo un login sin `password`:

```json
{"codigo": "dato_invalido", "mensaje": "Los datos enviados no son válidos.", "detalles": [{"campo": "password", "mensaje": "Campo obligatorio."}]}
```

| Status | `codigo` | Cuándo |
|--------|----------|--------|
| `401` | `no_autenticado` | Falta el token, es inválido o venció |
| `401` | `credenciales_invalidas` | Login fallido (mismo cuerpo exista o no el usuario) |
| `403` | `sin_permiso` | El rol del usuario no tiene permiso para la ruta |
| `404` | `no_encontrado` | La ruta no existe |
| `405` | `metodo_no_permitido` | Método HTTP no admitido en la ruta |
| `409` | `conflicto_agenda` | El turno se superpone con otro |
| `409` | `fuera_de_horario` | El turno no encaja en el horario de atención |
| `409` | `dentro_de_bloqueo` | El turno cae dentro de un bloqueo |
| `422` | `dato_invalido` | Datos de entrada o de dominio inválidos |
| otro | `error_http` | Otro error HTTP del framework (conserva su status) |
| `500` | `error_interno` | Error inesperado |

## Estructura

```
app/main.py                 App FastAPI (create_app, reloj inyectable, lifespan con esquema y seed, routers)
app/config.py               Configuración desde variables de entorno
app/api/auth.py             POST /auth/login, usuario_actual y requiere_rol
app/api/seguridad.py        Hash de contraseñas (Argon2id) y emisión y validación del token JWT
app/api/dependencias.py     Dependencias por request: conexión SQLite y hora actual
app/api/errores.py          Mapeo global de errores a {codigo, mensaje, detalles?}
app/api/salud.py            GET /health
app/domain/                 Lógica de dominio pura (modelos, intervalos, errores, reglas de alta y usuarios)
app/db/conexion.py          Conexión SQLite, transacciones y aplicación del esquema
app/db/esquema.sql          Esquema de la base (tabla usuario)
app/db/repositorio.py       Consultas parametrizadas de usuarios
app/db/seed.py              Seed de desarrollo de admin_demo
tests/domain/               Tests unitarios de dominio (pytest)
tests/api/                  Tests de API y de base con SQLite temporal
tests/api/rutas_prueba.py   Rutas protegidas solo para tests (no existen en app/)
tests/conftest.py           Fixtures: configuración, reloj fijo, usuarios, tokens y TestClient
.env.example                Variables de entorno de referencia (placeholders)
knowledge-base/             Base de conocimiento del proyecto (10 archivos)
docs/discovery/             Informe de Discovery y verificación de fuentes
openspec/specs/             Specs vigentes del sistema
openspec/changes/           Changes en curso y archivados (proposal, design, specs, tasks y verify)
CHANGES.md                  Roadmap de changes del MVP
AGENTS.md / CLAUDE.md       Reglas para los agentes de IA
```

## Seguridad y datos

- El repositorio no contiene claves ni credenciales: los valores de los ejemplos son ficticios y `.env` no se versiona.
- Las contraseñas se guardan solo como hash Argon2id con sal, nunca en texto plano.
- Todos los datos de pacientes, profesionales, sillones y usuarios de los tests son ficticios.
