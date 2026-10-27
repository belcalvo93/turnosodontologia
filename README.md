# Turnos Odontológicos

Backend académico para gestionar turnos de un consultorio odontológico (Trabajo de Integración, Metodología I, TUP – UTN FRM). Todos los datos de ejemplo son ficticios.

Desarrollado con Spec-Driven Development usando OpenSpec y Active Stack (ciclo OPSX).

## Estado actual

Implementados **C-01 `foundation-setup`** y **C-10 `reglas-alta-turno`**. La suite pasa en verde: `44 passed`.

**C-01 — base técnica:** configuración desde variables de entorno, conexión SQLite con transacciones atómicas (`BEGIN IMMEDIATE`, commit y rollback), aplicación del esquema al arrancar y `GET /health` público.

**C-10 — reglas de alta de turno** en dominio puro, sin base de datos ni HTTP:

- Calcula el fin del turno a partir de la duración de la prestación.
- Rechaza turnos fuera del horario de atención del profesional.
- Rechaza turnos dentro de un bloqueo del profesional o del sillón.
- Rechaza solapamientos por profesional, sillón o paciente, con intervalos semiabiertos `[inicio, fin)`: los turnos contiguos son válidos.

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
| `APP_ENV` | Entorno de ejecución | `development` |
| `DATABASE_URL` | Ruta de la base SQLite (acepta `sqlite:///ruta` o un path plano) | `./turnos.db` |
| `CLINIC_TIMEZONE` | Zona horaria del consultorio | `America/Argentina/Buenos_Aires` |

Exportarlas en la sesión actual:

```powershell
# Windows (PowerShell)
$env:APP_ENV="development"
$env:DATABASE_URL="sqlite:///./turnos.db"
$env:CLINIC_TIMEZONE="America/Argentina/Buenos_Aires"
```

```bash
# Linux / macOS (bash)
export APP_ENV=development
export DATABASE_URL=sqlite:///./turnos.db
export CLINIC_TIMEZONE=America/Argentina/Buenos_Aires
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

Resultado esperado: `44 passed`. Los tests de dominio corren sin base de datos ni HTTP; los de `tests/api/` usan una SQLite temporal por test.

## Levantar la API

```bash
uvicorn app.main:app
```

`GET /health` responde `200` con `{"status": "ok"}`.

## Estructura

```
app/main.py                 App FastAPI (create_app, lifespan y routers)
app/config.py               Configuración desde variables de entorno
app/api/                    Routers HTTP (salud; auth y recursos en los próximos changes)
app/domain/                 Lógica de dominio pura (modelos, intervalos, errores y reglas de alta)
app/db/                     Conexión SQLite, transacciones y esquema
tests/domain/               Tests unitarios de dominio (pytest)
tests/api/                  Tests de API y de base con SQLite temporal
tests/conftest.py           Fixtures de configuración y TestClient
.env.example                Variables de entorno de referencia (placeholders)
knowledge-base/             Base de conocimiento del proyecto (10 archivos)
docs/discovery/             Informe de Discovery y verificación de fuentes
openspec/specs/             Specs vigentes del sistema
openspec/changes/archive/   Changes archivados (proposal, design, specs, tasks y verify)
CHANGES.md                  Roadmap de changes del MVP
AGENTS.md / CLAUDE.md       Reglas para los agentes de IA
```

## Seguridad y datos

- El repositorio no contiene claves ni credenciales.
- Todos los datos de pacientes, profesionales y sillones de los tests son ficticios.