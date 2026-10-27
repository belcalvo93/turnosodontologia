# Verify — C-01 foundation-setup

- **Fecha:** 2026-10-27
- **Responsable:** Belén Calvo
- **Comando:** `pytest tests -v` (OpenSpec no ofrece una fase de verificación propia en esta instalación; la suite se ejecutó a mano)
- **Entorno:** Windows, Python 3.14.7, pytest 9.1.1
- **Resultado:** 44 passed in 0.14s (32 de `tests/domain/` + 12 de `tests/api/`), 1 warning. Sin tests en rojo.

## Cobertura de los escenarios del spec

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Defaults de desarrollo | `test_entorno_vacio_usa_defaults_de_desarrollo` | PASSED |
| DATABASE_URL con esquema de URL | `test_database_url_con_esquema_de_url_se_normaliza` | PASSED |
| Path explícito de la base | `test_database_url_con_path_absoluto_queda_intacto` | PASSED |
| Claves foráneas activas | `test_abrir_conexion_hace_cumplir_las_claves_foraneas` | PASSED |
| Commit al cerrar la transacción | `test_transaccion_confirma_al_salir_sin_excepcion` | PASSED |
| Rollback ante excepción | `test_transaccion_revierte_ante_excepcion_y_propaga` | PASSED |
| Arranque con esquema vacío | `test_arranque_inicializa_el_esquema` | PASSED |
| Aplicación repetida del esquema | `test_inicializar_esquema_se_puede_aplicar_dos_veces`, `test_inicializar_esquema_deja_la_base_usable` | PASSED |
| Consulta de salud sin token | `test_health_responde_200_sin_autenticacion` | PASSED |

## Chequeos adicionales

- Límites de imports entre capas (regla dura 1 de AGENTS.md): `app/domain/` no importa `fastapi`, `app.db` ni `app.api`; `app/db/` no importa `fastapi` ni `app.config` (tras el refactor del apply). Búsqueda por patrón de imports: sin coincidencias en ambos casos; los imports reales de `app/db/` son solo `sqlite3`, `collections.abc`, `contextlib` y `pathlib`.
- No se versiona ningún `.env`: `git ls-files` no lista `.env`, `.gitignore` lo excluye (línea 4) y el repo solo incluye `.env.example` con placeholders.
- Clon limpio de la rama en otra carpeta: `python -m venv` nuevo, `pip install -r requirements.txt` y `pytest tests` → 44 passed, 1 warning (Python 3.14.7, pytest 9.1.1, FastAPI 0.162.0).
- La suite no crea `turnos.db` en la raíz: verificado después de correr `pytest tests` (los tests usan una SQLite temporal por test vía `tmp_path`).
- Verificación manual de la API con `uvicorn app.main:app`: `GET /health` → `200 {"status":"ok"}`. Con la config default el arranque crea `turnos.db` (ignorado por git); el archivo de la prueba se eliminó.
- `openspec validate c-01-foundation-setup --strict` → `Change 'c-01-foundation-setup' is valid`.

## Observaciones del apply

- **Refactor de `app/db/` para respetar la regla dura 1.** La primera versión recibía `Config` y `app/db/conexion.py` importaba `app.config`, fuera del grafo `db -> domain`. Se ajustaron primero los tests a `abrir_conexion(ruta: Path)` e `inicializar_esquema(ruta_base: Path, ruta_esquema: Path | None = None)` (rojo con `AttributeError`), después la implementación y `app/main.py` (`inicializar_esquema(config_app.database_path)`), y se actualizaron las firmas en `design.md` (D4 y D5) y `tasks.md` (3.1 y 3.3).
- **Warning de Starlette 1.7 sobre `httpx2`.** `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead`. Los tests pasan; no se agregó la dependencia y queda como deuda en `requirements.txt` (`httpx>=0.27`).
- **C-02 quedó parcialmente adelantado por C-10.** Ya existen `app/domain/models.py`, `intervalos.py`, `errores.py` y `reglas_turno.py`; faltan `es_futuro()`, `validar_cancelacion`/`validar_reprogramacion` y `TurnoNoModificable`. `CHANGES.md` sigue marcando C-02 como pendiente: hay que decidir si se propone completo o solo con lo faltante.
- **No se probó con Python 3.11**, el mínimo declarado en `AGENTS.md`: tanto el entorno de desarrollo como el clon limpio usan Python 3.14.7. La compatibilidad se cuidó en el código (`isolation_level=None` en lugar de `conn.autocommit`, disponible recién desde 3.12), pero no está verificada empíricamente en 3.11.
