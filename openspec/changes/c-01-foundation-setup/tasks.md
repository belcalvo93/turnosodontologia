# Tasks — C-01 foundation-setup

## 1. Dependencias y estructura

- [x] 1.1 Declarar `fastapi>=0.115`, `uvicorn>=0.30`, `pydantic>=2.7`, `httpx>=0.27` y `pytest>=8.0` en `requirements.txt`, verificando que `python -c "import fastapi, uvicorn, pydantic, httpx, pytest"` funciona y que `pip install -r requirements.txt` no falla
- [x] 1.2 Crear `app/api/__init__.py`, `app/db/__init__.py` y `tests/api/__init__.py`, verificando que `pytest tests` sigue en verde con los 32 tests actuales
- [x] 1.3 Crear `.env.example` con placeholders de `APP_ENV`, `DATABASE_URL` y `CLINIC_TIMEZONE` (sin valores sensibles ni variables de JWT: esas son de C-03), verificando que `git status` no lista ningún `.env`

## 2. Configuración

- [x] 2.1 Implementar `app/config.py` con `Config` (dataclass frozen: `app_env`, `database_path`, `clinic_timezone`) y `cargar_config(entorno=None)` con defaults de desarrollo, verificando con tests en `tests/api/test_config.py`: entorno vacío → `development` / `./turnos.db` / `America/Argentina/Buenos_Aires`
- [x] 2.2 Normalizar `DATABASE_URL` en `cargar_config` (quitar `sqlite:///` y respetar paths absolutos), verificando con tests: `sqlite:///./turnos.db` → `./turnos.db` y un path absoluto de `tmp_path` queda intacto
- [ ] 2.3 Documentar las variables en `README.md` (PowerShell y bash) aclarando que `.env` no se carga automáticamente, verificando que los comandos documentados exportan `DATABASE_URL` y que `python -c "from app.config import cargar_config; print(cargar_config().database_path)"` muestra el path esperado

## 3. Persistencia

- [ ] 3.1 Implementar `abrir_conexion(config)` en `app/db/conexion.py` con `isolation_level=None`, `PRAGMA foreign_keys=ON` y `PRAGMA busy_timeout=5000`, verificando con un test que crea sus propias tablas temporales (el `esquema.sql` de este change solo tiene comentarios) que un `INSERT` con FK inexistente falla y que una FK válida se acepta
- [ ] 3.2 Implementar `transaccion(conexion)` como context manager con `BEGIN IMMEDIATE`, `commit` al salir sin excepción y `rollback` si hay excepción, verificando con tests que crean sus propias tablas temporales (el `esquema.sql` de este change solo tiene comentarios): el `INSERT` confirmado sobrevive en una conexión nueva y el `INSERT` seguido de excepción no deja fila
- [ ] 3.3 Crear `app/db/esquema.sql` (solo comentarios que expliquen la convención `CREATE TABLE IF NOT EXISTS`) e implementar `inicializar_esquema(config, ruta=None)` con `executescript` sobre conexión propia, verificando con tests que aplicarlo dos veces no lanza error y que la base queda usable
- [ ] 3.4 Invocar `inicializar_esquema` desde el `lifespan` de la app, verificando que una base temporal recién creada arranca sin error a través del `TestClient`

## 4. Aplicación y salud

- [ ] 4.1 Implementar `app/api/salud.py` con router `GET /health` que devuelve `{"status": "ok"}` sin tocar la base, verificando que el test de `tests/api/test_salud.py` recibe 200 sin cabecera de autenticación
- [ ] 4.2 Implementar `app/main.py` con `create_app(config=None)` (config en `app.state.config`, routers montados) y `app = create_app()` a nivel módulo, verificando que `uvicorn app.main:app` levanta y `GET /health` responde 200
- [ ] 4.3 Crear `tests/conftest.py` con fixture de `Config` sobre `tmp_path` y fixture de `TestClient` usando `with TestClient(create_app(config))`, verificando que los tests de `tests/api/` pasan sin tocar la base real
- [ ] 4.4 Actualizar la sección "Estructura" y "Estado actual" del `README.md`, verificando que el comando documentado para correr la suite (`pytest tests`) coincide con el que se ejecuta

## 5. Verificación del change

- [ ] 5.1 Correr `pytest tests` completo y verificar que pasan los tests de dominio existentes y los nuevos de `tests/api/`
- [ ] 5.2 Verificar que `app/domain/` no importa `fastapi` ni `app.db`/`app.api` (búsqueda de imports) y que `app/db/` no importa `fastapi`
- [ ] 5.3 Correr `openspec validate c-01-foundation-setup --strict` y verificar que no reporta errores

## Workflow follow-up

- Implementar con `/opsx:apply` respetando las reglas duras de `AGENTS.md`.
- Verificar el change antes de archivar (suite en verde y health respondiendo).
- Archivar con `/opsx:archive` y marcar `C-01` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
