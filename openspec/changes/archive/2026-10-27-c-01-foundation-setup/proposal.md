# Proposal — C-01 foundation-setup

## Why

Hoy el repo tiene reglas de dominio puras (C-10) pero **no tiene aplicación**: no hay FastAPI, ni configuración, ni capa de persistencia. Nada puede levantar ni responder HTTP, y C-02/C-03 no tienen base sobre la que apoyarse.

C-01 es el único change del GATE 0 y el primero del camino crítico (`C-01 → C-03 → C-04 → C-09 → C-11 → C-12 → C-15 → C-17`). Su objetivo es dejar el esqueleto técnico mínimo, reproducible y testeable sobre el que cada change posterior agrega sus tablas y sus routers, sin adelantar reglas de negocio ni autenticación.

## What Changes

- `requirements.txt` declara las dependencias de la API y de tests: FastAPI, uvicorn, pydantic v2, pytest y httpx (TestClient). Hoy solo declara `pytest`.
- Nueva estructura `app/api/` y `app/db/` (con `__init__.py`) y `tests/api/`, completando la estructura de `knowledge-base/08`. No se modifica `app/domain/` ni `tests/domain/`.
- Nuevo `app/config.py`: `Config` como dataclass frozen construida desde variables de entorno (`APP_ENV`, `DATABASE_URL`, `CLINIC_TIMEZONE`) con defaults de desarrollo, y normalización de `DATABASE_URL` (acepta `sqlite:///./turnos.db` y path plano).
- Nuevo `.env.example` con solo placeholders; `.env` ya está ignorado en `.gitignore`. El README explica cómo exportar las variables (no hay carga automática de `.env`).
- Nuevo `app/db/conexion.py`: conexión SQLite con `PRAGMA foreign_keys=ON` y `busy_timeout`, y context manager `transaccion()` con `BEGIN IMMEDIATE` / commit / rollback.
- Nuevo `app/db/esquema.sql` (solo comentarios en este change) y `inicializar_esquema()` aplicado desde el `lifespan` de FastAPI. Los changes siguientes agregan tablas con `CREATE TABLE IF NOT EXISTS`.
- Nueva app FastAPI creada por `create_app(config)` (con `app = create_app()` a nivel módulo para uvicorn) y router `app/api/salud.py` con `GET /health` público.
- Nuevo `tests/conftest.py` con SQLite temporal por test y `TestClient` que dispara el `lifespan`, más los tests de `/health`, de configuración y de transacción.

**Fuera de alcance:** tablas de dominio, auth/RBAC, seed, mapeo global de errores (RN-GLO-01, va en C-03), migraciones reales, Docker y PostgreSQL.

## Capabilities

### New Capabilities

- `base-tecnica`: plataforma mínima de la API — configuración por variables de entorno, conexión SQLite transaccional, aplicación del esquema al arrancar y endpoint de salud público.

### Modified Capabilities

Ninguna: no hay specs previas afectadas (`openspec/specs/` solo contiene `reglas-alta-turno`, de C-10).

## Impact

- **Archivos nuevos:** `app/config.py`, `app/main.py`, `app/api/{__init__,salud}.py`, `app/db/{__init__,conexion}.py`, `app/db/esquema.sql`, `.env.example`, `tests/conftest.py`, `tests/api/`.
- **Archivos modificados:** `requirements.txt` (declarar dependencias) y `README.md` (sección de variables de entorno y cómo levantar la API).
- **Sin cambios:** `app/domain/`, `tests/domain/`, `knowledge-base/`, `CHANGES.md`, `docs/`.
- **Dependencias:** ninguna hacia atrás. Habilita C-02 y C-03 (GATE 1) y, a través de ellas, todo el MVP.
- **Riesgo asumido:** se confirma SQLite (D-01/IN-01/SE-22) con acceso a datos concentrado en `app/db/` y SQL parametrizado; punto de revisión obligatorio antes de C-11.
