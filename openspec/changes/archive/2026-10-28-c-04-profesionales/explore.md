# Explore — C-04 profesionales

> Relevamiento previo al propose. También guardado en Engram: `Exploración C-04 profesionales` (topic `opsx/c-04-profesionales/explore`).
> Durante la exploración no se creó ni modificó ningún otro archivo del proyecto.

## 1. Qué pide C-04 (`CHANGES.md` L218-232)

| Ítem | Contenido |
|---|---|
| Tabla | `profesional` (`id`, `nombre`, `apellido`, `matricula` opcional, `activo`) |
| Endpoints | `GET /profesionales`, `POST /profesionales`, `PATCH /profesionales/{id}` (incluye desactivar con `activo=false`) |
| Permisos | Administración **C L E B**; recepción y odontólogo **solo L** (RN-ACC-02) |
| Tests exigidos | Alta válida, nombre vacío → **422**, recepción creando → **403**, desactivado sigue listándose como inactivo |
| Dependencia | `C-03` (`auth-login-roles`), governance **BAJO** |

De la KB:
- **US-001 (`06_funcionalidades.md`):** dar de alta, editar y desactivar profesionales para asignarles turnos; se crea con `nombre` y `apellido`; un profesional desactivado no acepta turnos nuevos y conserva los históricos; recepción y odontólogo solo pueden listarlos.
- **Modelo (`04_modelo_de_datos.md` §Profesional y §Convenciones):** `id` (entero, PK), `nombre` (texto), `apellido` (texto), `matricula` (texto, opcional; ficticia en ejemplos), `activo` (bool). Constraints: `nombre` y `apellido` no vacíos. No se borra físicamente: se desactiva (`activo = 0`).
- **Reglas (`05_reglas_de_negocio.md`):**
  - `RN-REC-03`: los sillones y profesionales desactivados no aceptan turnos nuevos; los turnos históricos se conservan (el rechazo al crear turno con profesional inactivo se verifica en `C-11`, pero `C-04` debe persistir y exponer `activo`).
  - `RN-ACC-01` / `RN-ACC-02`: toda ruta exige usuario autenticado (401 sin token) y respeta la matriz RBAC de `03_actores_y_roles.md` (fila Profesionales: Administración `C L E B`, Recepción `L`, Odontólogo `L`; 403 si el rol no tiene permiso).
  - `RN-GLO-01`: errores de negocio devuelven JSON en español con código consistente (422 dato inválido, 403 sin permiso, 401 sin autenticar).

## 2. Qué existe hoy (tras C-01 / C-10) y qué falta

**Existe y sirve de base**

- `app/config.py`: `Config` frozen con `database_path`; `cargar_config()`.
- `app/db/conexion.py`: `abrir_conexion(ruta: Path)` con `PRAGMA foreign_keys=ON` y `busy_timeout=5000`, `transaccion(conexion)` con `BEGIN IMMEDIATE`, `inicializar_esquema(ruta_base, ruta_esquema=None)`.
- `app/db/esquema.sql`: comentarios iniciales de `C-01` con la convención `CREATE TABLE IF NOT EXISTS <nombre> (...);`.
- `app/main.py`: `create_app(config)` + `lifespan` que ejecuta `inicializar_esquema`, guarda `app.state.config` y monta `router_salud`.
- `app/domain/models.py`: `Prestacion`, `HorarioAtencion`, `Bloqueo`, `Turno`.
- `app/domain/errores.py`: `ErrorDominio`, `DatoInvalido` (422), `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`.
- `tests/conftest.py`: fixtures `config` (SQLite temporal por test) y `cliente` (`TestClient` con `lifespan`). Suite actual: **44 passed**.

**Falta**

- Tabla `profesional` en `app/db/esquema.sql`.
- Dataclass `Profesional` en `app/domain/models.py` (tampoco está en el scope de `C-02`, que solo lista `Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo`).
- Validación de dominio de `Profesional` (`nombre` y `apellido` no vacíos tras `strip()`, matrícula opcional normalizada) que lance `DatoInvalido` sin depender de FastAPI ni de SQLite (regla dura 1 y 8).
- Funciones de persistencia para crear, listar, obtener por `id` y actualizar parcialmente un profesional en `app/db/`.
- Router con `GET /profesionales`, `POST /profesionales` y `PATCH /profesionales/{id}` montado en `create_app`.
- `app/api/auth.py` con `usuario_actual`, `requiere_rol` y el mapeo global de errores a JSON en español (`RN-GLO-01`), que pertenecen a `C-03`.

## 3. Diseñable y testeable **ya** vs bloqueado por C-03

**Se puede diseñar y testear sin C-03**

| Área | Qué se prueba |
|---|---|
| Esquema | Creación de tabla `profesional` al arrancar, `CHECK` de `nombre` y `apellido` no vacíos, `activo` con default `1`, idempotencia al reaplicar `inicializar_esquema` |
| Dominio puro | Construcción/validación de `Profesional`: `nombre` o `apellido` vacío o solo espacios → `DatoInvalido`; normalización con `strip()`; `matricula` opcional (`None` o texto limpio); `activo=True` por defecto |
| Persistencia | Alta, listado ordenado por `id`, búsqueda por `id`, actualización parcial (`nombre`, `apellido`, `matricula`, `activo=False`) y conservación de la fila al desactivar |
| API funcional | `POST /profesionales` válido (201), `nombre` o `apellido` vacío (422), `GET /profesionales` incluyendo activos e inactivos, `PATCH /profesionales/{id}` para editar datos o desactivar (`activo=false`), `PATCH` a `id` inexistente (404) |

**Bloqueado por C-03 (`auth-login-roles`)**

- **401** sin token o con token inválido en `GET /profesionales`, `POST /profesionales` y `PATCH /profesionales/{id}`.
- **403** cuando recepción u odontólogo intentan `POST /profesionales` o `PATCH /profesionales/{id}` (`RN-ACC-02`).
- **200** cuando recepción u odontólogo consultan `GET /profesionales`.
- El formato exacto del cuerpo JSON en español de `RN-GLO-01` y las dependencias `usuario_actual` / `requiere_rol` de `app/api/auth.py`.

Consecuencia: el **Explore** y el **Propose** completos de `C-04` se pueden cerrar ahora mismo. La ejecución final de `/opsx:apply` y `/opsx:archive` espera a que `C-03` esté mergeado en `main` para integrar las dependencias reales de `app/api/auth.py` y pasar los tests de 401/403.

## 4. Riesgos y decisiones para el propose

| # | Riesgo / duda | Recomendación |
|---|---|---|
| 1 | **`C-04` es camino crítico** (`C-01 → C-03 → C-04 → C-09 → C-11...`) y habilita `C-07`, `C-08` y `C-09` | Dejar la tabla `profesional` y las funciones de lectura por `id` claras y reutilizables: `C-07` necesita verificar que `profesional_id` exista y esté activo; `C-08` y `C-09` necesitan verificar que el profesional exista |
| 2 | **Paralelismo en GATE 3 con `C-05` (Belén) y `C-06`** | Todos tocan `app/db/esquema.sql`, `app/domain/models.py` y `app/main.py`. Para minimizar conflictos de merge en archivos nuevos, conviene ubicar el repositorio y el router de profesionales en módulos propios o secciones claramente separadas |
| 3 | **`matricula` en `profesional`: ¿es única o solo opcional?** | `CHANGES.md` (L221) y `04_modelo_de_datos.md` (§Profesional) dicen `matricula` opcional y no piden constraint `UNIQUE` (a diferencia de `sillon.nombre`, `prestacion.nombre` y `paciente.dni`). No agregar `UNIQUE` no pedido; si se envía vacía o `null`, normalizar a `None` |
| 4 | **Validación de `nombre` y `apellido` vacíos (422)** | Validar tanto en el esquema Pydantic de entrada como en una función pura de dominio (`validar_datos_profesional` -> `DatoInvalido`), cumpliendo la regla dura 8 (la lógica vive en `app/domain/` y se testea sin HTTP ni DB) |
| 5 | **Comportamiento del listado `GET /profesionales` con inactivos** | `CHANGES.md` L224 exige explícitamente el test *"desactivado sigue listándose como inactivo"*. Por lo tanto, `GET /profesionales` devuelve todos los profesionales (activos e inactivos) con su campo `activo: bool` |
| 6 | **Semántica de `PATCH /profesionales/{id}`** | Actualización parcial (`exclude_unset=True`): permite modificar `nombre`, `apellido`, `matricula` y/o `activo`. Si no existe el `id`, responde 404. Si se envía `nombre` o `apellido` vacío, responde 422. No existe endpoint `DELETE` (baja lógica mediante `activo=false`) |
| 7 | **Auditoría** | Fuera de alcance: el MVP solo audita turnos (`RN-AUD-01`, `IF-06`) |

## 5. Resumen

`C-04 profesionales` incorpora el primer recurso del consultorio sobre la base de `C-01` y `C-03`: tabla `profesional`, modelo y validación en dominio puro, persistencia SQLite parametrizada y endpoints `GET /profesionales`, `POST /profesionales` y `PATCH /profesionales/{id}` con baja lógica (`activo=false`) y control de roles (`administracion` escribe; `recepcion` y `odontologo` leen).

**Fuentes consultadas**

- `CHANGES.md` §C-04, §Árbol de dependencias, §Camino crítico y §Riesgos del roadmap.
- `knowledge-base/04_modelo_de_datos.md` §Convenciones, §Profesional, §Seed data inicial.
- `knowledge-base/06_funcionalidades.md` §US-001.
- `knowledge-base/03_actores_y_roles.md` §RBAC, §Rutas públicas.
- `knowledge-base/05_reglas_de_negocio.md` §RN-REC-03, §RN-ACC-01, §RN-ACC-02, §RN-GLO-01.
- `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Seguridad, §Testing.
- Repo: `app/config.py`, `app/main.py`, `app/db/conexion.py`, `app/db/esquema.sql`, `app/domain/{models,errores}.py`, `tests/conftest.py`.
