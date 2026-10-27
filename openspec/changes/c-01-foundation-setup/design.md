# Design — C-01 foundation-setup

## Context

C-01 es el GATE 0 del roadmap y no tiene dependencias. Motivación en `proposal.md`; relevamiento y decisiones D1-D5 en `explore.md`.

Estado actual del repo al diseñar:

- Existen `app/domain/` (C-02/C-10), `tests/domain/`, `requirements.txt` (solo `pytest>=8.0`), `.gitignore` (ya ignora `.env`, `*.db`) y `README.md`. Suite: 32 tests verdes.
- **No existen** `app/main.py`, `app/config.py`, `app/api/`, `app/db/`, `.env.example`, `tests/conftest.py` ni `tests/api/`.
- Se ejecuta con el Python global 3.14.7; `AGENTS.md` fija **3.11 como mínimo**. Las dependencias de la API están instaladas globalmente pero no declaradas.
- Restricciones duras relevantes: `domain` no importa FastAPI ni `app/db`/`app/api`; SQL siempre parametrizado; `.env` no se versiona; `snake_case` + type hints.

## Goals / Non-Goals

**Goals:**
- API FastAPI mínima que arranca, aplica el esquema y responde `GET /health` público.
- Configuración leída del entorno con defaults de desarrollo y `DATABASE_URL` normalizada.
- Conexión SQLite con claves foráneas activas y un helper de transacción con commit/rollback.
- Tests con base temporal por test y `TestClient`, sin depender de la base real.

**Non-Goals:**
- Tablas de dominio, repositorios, auth/RBAC, seed y mapeo de errores de negocio (C-03 en adelante).
- Migraciones reales, Docker y PostgreSQL (IN-01/D-01).
- Cambios en `app/domain/` o `tests/domain/`.

## Decisions

- **D1 — `DATABASE_URL` se normaliza.** `cargar_config()` acepta `sqlite:///./turnos.db` (formato de KB 08) y un path plano: si el valor empieza con `sqlite:///`, se quita el prefijo y se guarda un `Path`. Por qué: la KB documenta el formato con prefijo, pero `sqlite3` necesita un path; normalizar en un solo lugar evita lógica dispersa. Alternativa rechazada: parsear URLs genéricas (no hay otro motor).
- **D2 — Configuración con `os.environ` + dataclass.** `Config` es una `dataclass(frozen=True)` con `app_env: str`, `database_path: Path` y `clinic_timezone: str`. `cargar_config(entorno: Mapping[str, str] | None = None)` permite inyectar el entorno en tests sin `monkeypatch`. Sin `pydantic-settings` ni `python-dotenv`: **no se suman dependencias**. Consecuencia aceptada: `.env` no se carga automáticamente; `.env.example` documenta las variables y el README explica cómo exportarlas (PowerShell `$env:VAR="..."`, bash `export VAR=...`).
- **D3 — `create_app(config)` + `app` a nivel módulo.** `create_app(config: Config | None = None) -> FastAPI` guarda la config en `app.state.config` y monta los routers. Al final de `main.py`, `app = create_app()` para que `uvicorn app.main:app` funcione sin argumentos. Por qué: los tests crean su propia app con un `Config` temporal, sin monkeypatch global ni estado compartido. Alternativa rechazada: app global única (obliga a tocar el entorno para testear).
- **D4 — Esquema desde `lifespan`.** `inicializar_esquema(config, ruta=None)` abre **su propia conexión**, lee `app/db/esquema.sql` con `Path(__file__).with_name(...)` y lo aplica con `executescript`. Se invoca desde el `lifespan` de FastAPI (no `on_event`, deprecado) antes de atender requests. Por qué: `executescript` hace commit implícito y no debe interferir con una transacción de request. `esquema.sql` solo tiene comentarios en este change; los siguientes agregan tablas con `CREATE TABLE IF NOT EXISTS`, lo que hace la reaplicación idempotente. No hay sistema de migraciones: se documenta como limitación del alcance.
- **D5 — Transacciones explícitas y compatible 3.11.** Conexión con `isolation_level=None`: en ese modo `sqlite3` no abre transacciones implícitas (queda en autocommit) y la transacción la controla el `BEGIN IMMEDIATE` explícito; además `PRAGMA foreign_keys=ON` + `PRAGMA busy_timeout=5000`. El context manager `transaccion(conexion)` emite `BEGIN IMMEDIATE`, hace `commit()` al salir sin excepción y `rollback()` + re-lanza si hay excepción. Por qué: `BEGIN IMMEDIATE` toma el lock de escritura al inicio (mitiga SE-06) y `isolation_level=None` evita `conn.autocommit`, que existe recién desde 3.12 y rompería el mínimo 3.11. Los PRAGMAs se aplican en `abrir_conexion()` porque son por conexión.
- **D6 — Fechas: no aplica todavía.** C-01 no guarda fechas (no crea tablas). La convención de KB 04 (texto ISO sin offset, conversión manual) se implementará en el primer change que escriba un repositorio. Se deja anotado para no usar los adaptadores de `datetime` de `sqlite3`, deprecados desde 3.12.
- **D7 — `/health` no consulta la base.** Devuelve `{"status": "ok"}` con 200. Por qué: el scope pide un endpoint público de 200; un health con verificación de DB es un change posterior y complicaría el arranque de tests.
- **D8 — Sin manejadores de error en C-01.** El mapeo global a JSON en español (RN-GLO-01) es scope de C-03. `main.py` queda con el lugar donde registrarlos, sin implementarlos, para no duplicar trabajo ni pisar el change siguiente.
- **D9 — Pinning por mínimos.** `fastapi>=0.115`, `uvicorn>=0.30`, `pydantic>=2.7`, `httpx>=0.27`, `pytest>=8.0`. pydantic v2 explícito (KB y FastAPI actual). Sin lock file: el proyecto no lo usa hoy.
- **D10 — SQLite confirmado (D-01/IN-01/SE-22).** Se mantiene para el MVP: escala de SU-06, sin servidor ni contenedores. Mitigación: SQL parametrizado, todo el acceso en `app/db/`, sin sintaxis específica de SQLite más allá de PRAGMAs. Revisión obligatoria antes de C-11.
- **Tests con archivo temporal, no `:memory:`.** La base de test es un archivo en `tmp_path`: `:memory:` no sirve porque `abrir_conexion()` crea una conexión nueva por uso y cada una vería una base distinta. `TestClient` se usa como context manager (`with TestClient(app)`) para que dispare el `lifespan`.
- **Conexión de DB sin FastAPI en `app/db/`.** C-01 expone `abrir_conexion()` y `transaccion()`; ningún endpoint de este change toca la base, así que **no** se introduce una dependencia de FastAPI en `app/db/`. Cuando C-03/C-04 necesiten datos, envolverán `abrir_conexion()` en una dependencia desde `app/api/`, respetando `api -> db` y `db -> domain`.

## Estructura resultante

```
app/
├── main.py                 # create_app(config), lifespan, app = create_app()
├── config.py               # Config + cargar_config()
├── api/
│   ├── __init__.py
│   └── salud.py            # router GET /health
├── domain/                 # sin cambios (C-02/C-10)
└── db/
    ├── __init__.py
    ├── conexion.py         # abrir_conexion(), transaccion(), inicializar_esquema()
    └── esquema.sql         # solo comentarios en C-01
tests/
├── conftest.py             # Config temporal, cliente TestClient con lifespan
├── domain/                 # sin cambios
└── api/
    ├── __init__.py
    ├── test_config.py      # defaults, prefijo sqlite:///, path absoluto
    ├── test_conexion.py    # FK activas, commit, rollback, esquema idempotente
    └── test_salud.py       # GET /health -> 200
.env.example
```

> `tests/api/` aloja también los tests de config y conexión porque `knowledge-base/08` define solo `tests/{domain,api}`; no se agrega un directorio nuevo.

## Risks / Trade-offs

- **[Python de referencia 3.11 vs. entorno 3.14]** Podrían colarse APIs nuevas (p. ej. `conn.autocommit`) → se prohíbe `autocommit`, se usa `isolation_level=None` y el design fija 3.11 como referencia.
- **[`executescript` hace commit implícito]** Podría romper una transacción abierta → el esquema se aplica en su propia conexión, antes de atender requests.
- **[@lifespan no corre si el `TestClient` no se usa como context manager]** Los tests de `/health` fallarían sin esquema inicializado → `tests/conftest.py` usa `with TestClient(app)`.
- **[Base temporal por test]** Más lento que `:memory:` pero aislado y realista → aceptado; la suite es chica.
- **[Sin carga de `.env`]** Un desarrollador nuevo puede esperar que las variables se lean del archivo → el README lo dice explícitamente y `.env.example` aclara que no se carga solo.
- **[SQLite, un escritor a la vez]** Reservas simultáneas (SE-06) → `BEGIN IMMEDIATE` + `busy_timeout`; la validación+inserción atómica se resuelve en C-11.
- **[C-01 y C-03 tocan `main.py`]** Conflicto de merge → C-03 va después (GATE 1); C-01 no implementa RN-GLO-01.

## Migration Plan

Sin migración: no hay datos, endpoints ni tablas previas. Rollback: borrar los archivos nuevos y revertir `requirements.txt`/`README.md`; C-02 y C-10 no dependen de nada de C-01 en tiempo de ejecución (solo el scaffold de tests).

## Open Questions

Ninguna que afecte specs o tareas. Quedan para sus changes: D6 (convención de fechas en repositorios), C-03 (RN-GLO-01 y carga de secretos JWT) y C-11 (revisión de SQLite).
