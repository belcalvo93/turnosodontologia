# Turnos Odontológicos

Backend académico para gestionar turnos de un consultorio odontológico (Trabajo de Integración, Metodología I, TUP – UTN FRM). Todos los datos de ejemplo son ficticios.

Desarrollado con Spec-Driven Development usando OpenSpec y Active Stack (ciclo OPSX).

## Estado actual

Implementados los **17 changes del MVP (`C-01` a `C-17`)**. La suite completa pasa en verde: `785 passed`.

- **Base técnica y dominio (`C-01`, `C-02`, `C-10`):** configuración desde variables de entorno, conexión SQLite con transacciones atómicas (`BEGIN IMMEDIATE`), aplicación idempotente del esquema, `GET /health` público y dominio puro (modelos inmutables, intervalos semiabiertos `[inicio, fin)`, reloj inyectado y reglas de alta, reprogramación y cancelación sin base de datos ni HTTP).
- **Acceso y usuarios (`C-03`, `C-07`):** login con JWT firmado (`POST /auth/login`), hash Argon2id, control de acceso por rol (`administracion`, `recepcion`, `odontologo`) y gestión de usuarios internos.
- **Catálogo y disponibilidad (`C-04`, `C-05`, `C-06`, `C-08`, `C-09`, `C-16`):** profesionales, sillones, prestaciones con duración en minutos, pacientes (con DNI único y obra social opcional), horarios de atención semanales y bloqueos horarios con reporte de turnos afectados.
- **Turnos, agenda y auditoría (`C-11`, `C-12`, `C-13`, `C-14`, `C-15`):** alta (`POST /turnos`), consulta (`GET /turnos/{id}`), reprogramación (`POST /turnos/{id}/reprogramar`), cancelación (`POST /turnos/{id}/cancelar`), agenda por profesional y por sillón (`GET /agenda/...`) y consulta de auditoría append-only (`GET /auditoria?turno_id=`).
- **Seed demo, flujo E2E y trazabilidad (`C-17`):** siembra idempotente de 32 filas ficticias en desarrollo, prueba extremo a extremo del flujo de 6 pasos y verificación automática de [trazabilidad RN → test](docs/trazabilidad-rn-test.md).

## Requisitos

- Git
- Python 3.11 o superior

No hace falta Docker ni servidor de base de datos externo.

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
| `CLINIC_TIMEZONE` | Zona horaria del consultorio (define la hora local de turnos y horarios sembrados) | `America/Argentina/Buenos_Aires` |
| `JWT_SECRET` | Clave para firmar los tokens: 32+ caracteres (64+ si usás `HS512`). **Obligatoria fuera de `development`/`test`** | Aleatoria por proceso en `development`/`test` |
| `JWT_ALGORITHM` | Algoritmo de firma: `HS256`, `HS384` o `HS512` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez del token (entero mayor que 0) | `60` |
| `SEED_ADMIN_PASSWORD` | Contraseña inicial de `admin_demo`; habilita el seed demo en `development` | Sin definir (no se siembra nada) |
| `SEED_RECEPCION_PASSWORD` | Contraseña inicial de `recepcion_demo` (solo si el seed está habilitado) | Sin definir (no se crea `recepcion_demo`) |
| `SEED_ODONTOLOGO_PASSWORD` | Contraseña inicial de `odontologo_demo` (solo si el seed está habilitado) | Sin definir (no se crea `odontologo_demo`) |

> **Sin `JWT_SECRET` la app no arranca fuera de `development`/`test`.** Con `APP_ENV=production`, por
> ejemplo, falla al iniciar con `ConfigInvalida: Falta la variable de entorno JWT_SECRET (obligatoria con APP_ENV=production).`
> En `development` y `test`, si falta, se genera un secreto aleatorio en cada arranque: los tokens
> emitidos dejan de valer al reiniciar la API.

> **Dependencia de `CLINIC_TIMEZONE`:** tanto los horarios de atención sembrados (lunes a viernes de `09:00` a `13:00` y de `14:00` a `18:00`) como las fechas de los turnos (`YYYY-MM-DDTHH:MM:SS` sin offset) se interpretan en la hora local del consultorio definida por `CLINIC_TIMEZONE`.

Exportarlas en la sesión actual (valores de ejemplo, ficticios):

```powershell
# Windows (PowerShell)
$env:APP_ENV="development"
$env:DATABASE_URL="sqlite:///./turnos.db"
$env:CLINIC_TIMEZONE="America/Argentina/Buenos_Aires"
$env:JWT_SECRET="cambiar-por-un-secreto-propio-de-32-caracteres-o-mas"
$env:JWT_ALGORITHM="HS256"
$env:ACCESS_TOKEN_EXPIRE_MINUTES="60"
$env:SEED_ADMIN_PASSWORD="clave-admin-demo-ficticia"
$env:SEED_RECEPCION_PASSWORD="clave-recepcion-demo-ficticia"
$env:SEED_ODONTOLOGO_PASSWORD="clave-odontologo-demo-ficticia"
```

```bash
# Linux / macOS (bash)
export APP_ENV=development
export DATABASE_URL=sqlite:///./turnos.db
export CLINIC_TIMEZONE=America/Argentina/Buenos_Aires
export JWT_SECRET=cambiar-por-un-secreto-propio-de-32-caracteres-o-mas
export JWT_ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=60
export SEED_ADMIN_PASSWORD=clave-admin-demo-ficticia
export SEED_RECEPCION_PASSWORD=clave-recepcion-demo-ficticia
export SEED_ODONTOLOGO_PASSWORD=clave-odontologo-demo-ficticia
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

Resultado esperado: `785 passed`. Los tests de dominio corren sin base de datos ni HTTP; los de `tests/api/` usan una SQLite temporal por test y un reloj fijo (`RelojFijo`), así que no dependen de la hora ni de la zona horaria de la máquina.

La cobertura de las 31 reglas de negocio de `knowledge-base/05_reglas_de_negocio.md` está documentada en [`docs/trazabilidad-rn-test.md`](docs/trazabilidad-rn-test.md) y verificada automáticamente por `tests/test_trazabilidad.py`.

## Levantar la API

```bash
uvicorn app.main:app
```

`GET /health` responde `200` con `{"status": "ok"}`, sin token.

La documentación interactiva (`/docs`, `/redoc` y `/openapi.json`) existe **solo con `APP_ENV=development`**. En cualquier otro entorno esas rutas responden `404`.

### Usuarios y catálogo demo en desarrollo

Al arrancar con `APP_ENV=development` y `SEED_ADMIN_PASSWORD` definida, el sistema siembra de forma idempotente el catálogo demo ficticio y hasta 3 usuarios demo (**32 filas** en total cuando están definidas las tres contraseñas):

- **Catálogo demo (29 filas):**
  - 2 profesionales activos: `"Odontólogo Ficticio A"` (matrícula `"0001 (ficticia)"`) y `"Odontóloga Ficticia B"` (matrícula `"0002 (ficticia)"`).
  - 20 horarios de atención: lunes (`0`) a viernes (`4`), de `09:00` a `13:00` y de `14:00` a `18:00`, para ambos profesionales.
  - 2 sillones activos: `"Sillón 1"` y `"Sillón 2"`.
  - 3 prestaciones activas: `"Consulta ficticia"` (`30` min), `"Limpieza ficticia"` (`45` min) y `"Tratamiento ficticio"` (`60` min).
  - 2 pacientes: `"Paciente Ficticio 1"` (DNI `"00000001 (ficticio)"`, obra social `"Obra Social Ficticia A"`) y `"Paciente Ficticio 2"` (DNI `"00000002 (ficticio)"`, sin obra social).
- **Usuarios demo (hasta 3 filas):**
  - `admin_demo` (rol `administracion`, activo, `profesional_id: null`) — requiere `SEED_ADMIN_PASSWORD`.
  - `recepcion_demo` (rol `recepcion`, activo, `profesional_id: null`) — se crea si además está definida `SEED_RECEPCION_PASSWORD`.
  - `odontologo_demo` (rol `odontologo`, activo, vinculado al `"Odontólogo Ficticio A"`) — se crea si además está definida `SEED_ODONTOLOGO_PASSWORD`.

- **No hace falta borrar `turnos.db`:** el seed es aditivo e idempotente (`ON CONFLICT DO NOTHING` y `WHERE NOT EXISTS`). Una base de desarrollo existente recibe las filas faltantes en el siguiente arranque sin duplicar profesionales ni horarios y sin modificar usuarios ya existentes.
- En cualquier otro entorno (`test`, `production`) o si falta `SEED_ADMIN_PASSWORD`, no se siembra nada.

### Flujo E2E de 6 pasos (ejemplo real)

Con la API levantada en `development` y las tres variables `SEED_*_PASSWORD` definidas, el flujo completo de extremo a extremo (verificado en `tests/api/test_flujo_e2e.py`) recorre los 6 pasos siguientes. Todas las rutas protegidas llevan la cabecera `Authorization: Bearer <access_token>`.

#### 1. Login de recepción (`POST /auth/login` → `200`)

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "recepcion_demo", "password": "clave-recepcion-demo-ficticia"}'
```

Respuesta `200`:

```json
{"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
```

#### 2. Crear turno (`POST /turnos` → `201`)

Reserva de una `"Consulta ficticia"` (30 minutos) para el lunes a las `10:00` en hora local del consultorio (`CLINIC_TIMEZONE`):

```bash
curl -X POST http://127.0.0.1:8000/turnos \
  -H "Authorization: Bearer <token_recepcion>" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 1,
    "profesional_id": 1,
    "sillon_id": 1,
    "prestacion_id": 1,
    "inicio": "2026-01-05T10:00:00"
  }'
```

Respuesta `201`:

```json
{
  "id": 1,
  "paciente_id": 1,
  "profesional_id": 1,
  "sillon_id": 1,
  "prestacion_id": 1,
  "inicio": "2026-01-05T10:00:00",
  "fin": "2026-01-05T10:30:00",
  "estado": "reservado"
}
```

#### 3. Reprogramar turno (`POST /turnos/1/reprogramar` → `200`)

```bash
curl -X POST http://127.0.0.1:8000/turnos/1/reprogramar \
  -H "Authorization: Bearer <token_recepcion>" \
  -H "Content-Type: application/json" \
  -d '{"nuevo_inicio": "2026-01-05T11:00:00"}'
```

Respuesta `200`:

```json
{
  "id": 1,
  "paciente_id": 1,
  "profesional_id": 1,
  "sillon_id": 1,
  "prestacion_id": 1,
  "inicio": "2026-01-05T11:00:00",
  "fin": "2026-01-05T11:30:00",
  "estado": "reservado"
}
```

#### 4. Cancelar turno (`POST /turnos/1/cancelar` → `200`)

```bash
curl -X POST http://127.0.0.1:8000/turnos/1/cancelar \
  -H "Authorization: Bearer <token_recepcion>"
```

Respuesta `200`:

```json
{
  "id": 1,
  "paciente_id": 1,
  "profesional_id": 1,
  "sillon_id": 1,
  "prestacion_id": 1,
  "inicio": "2026-01-05T11:00:00",
  "fin": "2026-01-05T11:30:00",
  "estado": "cancelado"
}
```

#### 5. Login de administración (`POST /auth/login` → `200`)

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin_demo", "password": "clave-admin-demo-ficticia"}'
```

Respuesta `200`:

```json
{"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
```

#### 6. Consultar auditoría del turno (`GET /auditoria?turno_id=1` → `200`)

```bash
curl "http://127.0.0.1:8000/auditoria?turno_id=1" \
  -H "Authorization: Bearer <token_admin>"
```

Respuesta `200`:

```json
{
  "turno_id": 1,
  "registros": [
    {
      "id": 1,
      "turno_id": 1,
      "accion": "crear",
      "usuario_id": 2,
      "username": "recepcion_demo",
      "ocurrio_en": "2026-01-05T09:00:00",
      "antes": null,
      "despues": {
        "id": 1,
        "paciente_id": 1,
        "profesional_id": 1,
        "sillon_id": 1,
        "prestacion_id": 1,
        "inicio": "2026-01-05T10:00:00",
        "fin": "2026-01-05T10:30:00",
        "estado": "reservado"
      }
    },
    {
      "id": 2,
      "turno_id": 1,
      "accion": "reprogramar",
      "usuario_id": 2,
      "username": "recepcion_demo",
      "ocurrio_en": "2026-01-05T09:00:00",
      "antes": {
        "id": 1,
        "paciente_id": 1,
        "profesional_id": 1,
        "sillon_id": 1,
        "prestacion_id": 1,
        "inicio": "2026-01-05T10:00:00",
        "fin": "2026-01-05T10:30:00",
        "estado": "reservado"
      },
      "despues": {
        "id": 1,
        "paciente_id": 1,
        "profesional_id": 1,
        "sillon_id": 1,
        "prestacion_id": 1,
        "inicio": "2026-01-05T11:00:00",
        "fin": "2026-01-05T11:30:00",
        "estado": "reservado"
      }
    },
    {
      "id": 3,
      "turno_id": 1,
      "accion": "cancelar",
      "usuario_id": 2,
      "username": "recepcion_demo",
      "ocurrio_en": "2026-01-05T09:00:00",
      "antes": {
        "id": 1,
        "paciente_id": 1,
        "profesional_id": 1,
        "sillon_id": 1,
        "prestacion_id": 1,
        "inicio": "2026-01-05T11:00:00",
        "fin": "2026-01-05T11:30:00",
        "estado": "reservado"
      },
      "despues": {
        "id": 1,
        "paciente_id": 1,
        "profesional_id": 1,
        "sillon_id": 1,
        "prestacion_id": 1,
        "inicio": "2026-01-05T11:00:00",
        "fin": "2026-01-05T11:30:00",
        "estado": "cancelado"
      }
    }
  ]
}
```

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
| `409` | `turno_no_modificable` | El turno no se puede modificar (pasado, en curso o cancelado) |
| `422` | `dato_invalido` | Datos de entrada o de dominio inválidos |
| otro | `error_http` | Otro error HTTP del framework (conserva su status) |
| `500` | `error_interno` | Error inesperado |

## Estructura

```
app/main.py                        App FastAPI (create_app, reloj inyectable, lifespan con esquema y seed demo, routers)
app/config.py                      Configuración desde variables de entorno
app/api/auth.py                    POST /auth/login, usuario_actual y requiere_rol
app/api/seguridad.py               Hash de contraseñas (Argon2id) y emisión y validación del token JWT
app/api/dependencias.py            Dependencias por request: conexión SQLite y hora actual local
app/api/errores.py                 Mapeo global de errores a {codigo, mensaje, detalles?}
app/api/salud.py                   GET /health
app/api/profesionales.py           CRUD de profesionales
app/api/horarios.py                Configuración y consulta de horarios de atención
app/api/sillones.py                CRUD de sillones/boxes
app/api/prestaciones.py            CRUD de prestaciones
app/api/pacientes.py               CRUD de pacientes
app/api/usuarios.py                Gestión de usuarios y roles
app/api/bloqueos.py                Alta, listado y baja de bloqueos horarios
app/api/turnos.py                  POST /turnos, GET /turnos/{id}, reprogramar y cancelar
app/api/agenda.py                  GET /agenda/profesionales/{id} y /agenda/sillones/{id}
app/api/auditoria.py               GET /auditoria?turno_id= (historial append-only)
app/domain/                        Lógica de dominio pura (modelos, intervalos, errores, reglas de turnos, bloqueos y usuarios)
app/db/conexion.py                 Conexión SQLite, transacciones y aplicación del esquema
app/db/esquema.sql                 Esquema de la base (tablas e índices del MVP y triggers append-only)
app/db/repositorio*.py             Consultas parametrizadas por entidad (usuarios, recursos, turnos, agenda, auditoría)
app/db/seed.py                     Seed demo idempotente (catálogo ficticio y usuarios admin_demo, recepcion_demo y odontologo_demo)
tests/domain/                      Tests unitarios de dominio puro (pytest)
tests/api/                         Tests de API, repositorios, seed y flujo E2E con SQLite temporal
tests/trazabilidad.py              Helpers puros de verificación de trazabilidad RN → test
tests/test_trazabilidad.py         Verificación automática de la tabla de trazabilidad contra KB 05 y el AST de tests
tests/conftest.py                  Fixtures: configuración, reloj fijo, usuarios, tokens y TestClient
docs/trazabilidad-rn-test.md       Tabla de trazabilidad de las 31 reglas RN-xx a su test exacto
.env.example                       Variables de entorno de referencia (placeholders)
knowledge-base/                    Base de conocimiento del proyecto (10 archivos)
docs/discovery/                    Informe de Discovery y verificación de fuentes
openspec/specs/                    Specs vigentes del sistema
openspec/changes/                  Changes en curso y archivados (proposal, design, specs, tasks y verify)
CHANGES.md                         Roadmap de changes del MVP
AGENTS.md / CLAUDE.md              Reglas para los agentes de IA
```

## Seguridad y datos

- El repositorio no contiene claves ni credenciales: los valores de los ejemplos son ficticios y `.env` no se versiona.
- Las contraseñas se guardan solo como hash Argon2id con sal, nunca en texto plano.
- Todos los datos de pacientes, profesionales, sillones y usuarios del seed y de los tests son ficticios y están rotulados (`"(ficticio)"` / `"(ficticia)"`).
