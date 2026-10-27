# Explore — C-01 foundation-setup

> Resumen del relevamiento previo al propose. También guardado en Engram: `Explore C-01 foundation-setup` (topic `opsx/c-01-foundation-setup/explore`, obs. #109) y `Decisiones C-01 D1-D5` (topic `opsx/c-01-foundation-setup/decisiones`, obs. #110).
> Durante la exploración no se creó ni modificó ningún archivo del proyecto.

## Problema

C-01 es el primer change del roadmap y el único del GATE 0: deja el esqueleto técnico sobre el que se apoyan C-02 (dominio puro) y C-03 (auth y roles). Hoy el repo tiene la lógica de dominio de C-10, pero **no tiene aplicación FastAPI, ni configuración, ni capa de persistencia**: nada puede levantar ni responder HTTP.

Objetivo: una app mínima que arranque, aplique el esquema en una SQLite y responda `GET /health`, con tests que usen una base temporal y demuestren que una transacción hace rollback ante excepción. Sin reglas de negocio, sin auth, sin tablas de dominio (cada change agrega las suyas).

## Estado del repo al relevar

- `main` limpio (sin cambios sin commitear), último commit `a04d63d`.
- `.active-orchestrator-state.json` en `step: "done"`: la fundación (discovery, KB, roadmap, skills, AGENTS.md) está completa.
- C-10 `reglas-alta-turno` implementado y archivado en `openspec/changes/archive/2026-10-15-c-10-reglas-alta-turno/`; su spec vive en `openspec/specs/reglas-alta-turno/spec.md`.
- Suite actual: `pytest tests` → **32 passed** (0.08 s).
- No existe `pyproject.toml` ni `.venv`; se corre con el Python global **3.14.7**.
- Dependencias instaladas globalmente pero **no declaradas**: fastapi 0.141.1, starlette 1.7.0, uvicorn 0.53.0, pydantic 2.13.5, httpx 0.28.1, pytest 9.1.1.
- C-10 dejó una base técnica mínima que adelanta parte de C-01 y de C-02 (ver abajo). **Ese código no se toca en C-01**: `app/domain/` es territorio de C-02/C-10.

## Qué de C-01 está hecho y qué falta

| Ítem del scope de C-01 | Estado | Detalle |
|---|---|---|
| `requirements.txt` con FastAPI, uvicorn, pydantic, pytest y httpx | ⚠️ Parcial | Existe, pero solo declara `pytest>=8.0` |
| Estructura `app/{domain,api,db}/` y `tests/{domain,api}/` | ⚠️ Parcial | `app/domain/` y `tests/domain/` existen (C-02/C-10); **faltan** `app/api/`, `app/db/` y `tests/api/` |
| `app/config.py` (`APP_ENV`, `DATABASE_URL`, `CLINIC_TIMEZONE`) | ❌ Falta | No existe |
| `.env.example` con placeholders; `.env` en `.gitignore` | ⚠️ Parcial | `.gitignore` ya ignora `.env`, `*.db`, `.venv`, `__pycache__`, `.pytest_cache`; **falta** `.env.example` |
| `app/db/conexion.py`: SQLite, `PRAGMA foreign_keys=ON`, helper de transacción | ❌ Falta | No existe `app/db/` |
| `app/db/esquema.sql` inicial + aplicación al arrancar | ❌ Falta | No existe `app/db/` |
| `app/main.py` con `GET /health` público | ❌ Falta | No existe `app/main.py` |
| `tests/conftest.py`: SQLite temporal por test + `TestClient` | ❌ Falta | No existe |
| Tests: `GET /health` → 200; transacción con rollback | ❌ Faltan | Hay 32 tests, todos de dominio |

### Lo que dejó C-10 (no es de C-01)

- `requirements.txt` (solo pytest), `.gitignore`, `README.md` con instalación y comandos.
- `app/__init__.py`, `app/domain/{__init__,models,intervalos,errores,reglas_turno}.py`.
- `tests/__init__.py`, `tests/domain/{__init__,test_estructura,test_intervalos,test_reglas_turno}.py`.
- `openspec/config.yaml`, `openspec/specs/reglas-alta-turno/`.

### Observación sobre C-02

`CHANGES.md` marca C-02 como pendiente, pero C-10 adelantó la mayor parte: `models.py`, `intervalos.solapan()`, `errores.py` y `validar_alta`. Falta de C-02: `es_futuro()`, `validar_cancelacion`/`validar_reprogramacion` y `TurnoNoModificable`. No afecta a C-01, pero hay que decidir al proponer C-02 si se plantea completo o solo como "lo que falta" para no reescribir código ya testeado.

## Decisiones cerradas (D1-D5)

| # | Decisión | Resolución |
|---|---|---|
| **D1** | Formato de `DATABASE_URL` | Aceptar el formato de KB 08 (`sqlite:///./turnos.db`) y también un path plano; la config normaliza quitando el prefijo `sqlite:///`. Default de desarrollo: `./turnos.db`. En tests se inyecta un archivo en `tmp_path`. |
| **D2** | Carga de configuración | `os.environ` + `dataclass(frozen=True)`. **Sin** `pydantic-settings` ni `python-dotenv`: no se suman dependencias. Consecuencia: `.env` **no** se carga automáticamente; `.env.example` es solo documentación y el README debe explicar cómo exportar las variables (PowerShell `$env:VAR="..."`, bash `export VAR=...`). Si C-03 necesita carga automática de `.env`, se revisa en ese change. |
| **D3** | Forma de la app | `create_app(config)` guarda la config en `app.state.config`; `app = create_app()` a nivel módulo para uvicorn. Los tests crean su propia app con config propia (sin monkeypatch global). El router de salud vive en `app/api/salud.py` y `main.py` lo monta (coherente con la estructura de KB 08). |
| **D4** | Aplicación del esquema | `esquema.sql` con solo comentarios en C-01; `inicializar_esquema()` lo aplica con `executescript` desde el `lifespan` de FastAPI (no `on_event`, deprecado). Los changes siguientes agregan tablas con `CREATE TABLE IF NOT EXISTS`; se documenta que **no** hay sistema de migraciones. |
| **D5** | Transacciones y concurrencia | `isolation_level=None` (evita `conn.autocommit`, que es 3.12+, y mantiene compatibilidad con 3.11), escrituras con `BEGIN IMMEDIATE`, `PRAGMA foreign_keys=ON` por conexión y `busy_timeout=5000`. Context manager `transaccion(conn)` con commit/rollback (`BEGIN IMMEDIATE` implícito en la apertura). Conexión por request vía dependencia de FastAPI. |

## Decisiones diferidas al propose (D6-D10)

| # | Decisión | Opciones | Recomendación |
|---|---|---|---|
| D6 | Fechas en SQLite | Adaptadores `sqlite3` vs. texto ISO manual | Texto ISO sin offset (KB 04) convertido a mano en `app/db/repositorio.py`: los adaptadores de `datetime` están deprecados desde Python 3.12 y acá corre 3.14 |
| D7 | Alcance de `/health` | Solo `{"status":"ok"}` vs. chequear DB | Solo status; el scope pide 200 público. Un health con verificación de DB es un change posterior |
| D8 | Mapeo global de errores (RN-GLO-01) | En C-01 vs. en C-03 | C-01 deja el lugar preparado en `main.py` sin implementarlo; C-03 lo completa (es su scope) |
| D9 | Pinning de versiones | `>=x` vs. exacto | Mínimos por rango y pydantic v2 explícito |
| D10 | SQLite vs. PostgreSQL (IN-01, SE-22, D-01) | Confirmar o migrar | Confirmar SQLite para el MVP (escala de SU-06, sin Docker). Mitigación: SQL parametrizado, acceso solo en `app/db/`, sin sintaxis SQLite-específica más allá de PRAGMAs. Punto de revisión obligatorio antes de C-11 |

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Python de referencia ambiguo: AGENTS exige ≥3.11, se desarrolla con 3.14 | Usar APIs nuevas sin querer (p. ej. `conn.autocommit`) | Fijar 3.11 como referencia en el design; prohibir `autocommit` |
| Adaptadores `datetime`/`date` de `sqlite3` deprecados (3.12+) | `DeprecationWarning` y ruptura futura | Guardar texto ISO y convertir en el repositorio (D6) |
| `executescript` hace commit implícito | El esquema podría interferir con una transacción abierta | Aplicar el esquema en su propia conexión, antes de servir requests, desde `lifespan` |
| SQLite: un solo escritor a la vez (SE-06, IN-01) | Reservas simultáneas | `BEGIN IMMEDIATE` + `busy_timeout`; validar e insertar en una única transacción en C-11 |
| Dependencias no declaradas (instaladas solo en el entorno global) | El repo no es reproducible | Completar `requirements.txt` en C-01 |
| C-01 y C-03 tocan `main.py` | Conflicto de merge / pisan el mapeo de errores | C-03 va después de C-01 (GATE 1); C-01 deja el punto de registro preparado y no implementa RN-GLO-01 |

## Fuera de alcance de C-01

- Tablas de dominio, auth, seed y mapeo de errores de negocio (C-03 en adelante).
- Migraciones reales, Docker y PostgreSQL (IN-01/D-01).
- Cualquier cambio a `app/domain/`, `tests/domain/`, `knowledge-base/` o `CHANGES.md`.

## Fuentes

- `CHANGES.md` §C-01 (scope, dependencias, governance BAJO) y §Riesgos del roadmap.
- `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Variables de entorno, §Seguridad, §Testing.
- `knowledge-base/09_decisiones_y_supuestos.md` §D-01 (stack provisional), §D-07 (persistencia sin ORM).
- `knowledge-base/02_descripcion_general.md` §API REST (incluye `GET /health` y la convención de errores).
- `knowledge-base/04_modelo_de_datos.md` §Convenciones (fechas ISO sin offset, baja lógica).
- `knowledge-base/10_preguntas_abiertas.md` §IN-01 y §SE-22 (SQLite vs. PostgreSQL).
- Repo: `requirements.txt`, `.gitignore`, `README.md`, `app/domain/`, `tests/domain/`, `openspec/`.
