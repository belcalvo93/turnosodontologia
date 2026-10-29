# Explore — C-05 sillones-prestaciones

> Relevamiento previo al propose. También guardado en Engram: `Exploración C-05 sillones-prestaciones` (topic `opsx/c-05-sillones-prestaciones/explore`, obs. #112).
> Durante la exploración no se creó ni modificó ningún otro archivo del proyecto.

## 1. Qué pide C-05 (`CHANGES.md` L233-246)

| Ítem | Contenido |
|---|---|
| Tablas | `sillon` (`nombre` único, `activo`) y `prestacion` (`nombre` único, `duracion_minutos > 0`, `activa`) |
| Endpoints | `GET/POST /sillones`, `PATCH /sillones/{id}`; `GET/POST /prestaciones`, `PATCH /prestaciones/{id}` |
| Permisos | Administración **C L E B**; recepción y odontólogo **solo L** |
| Tests exigidos | nombre duplicado → **409**, duración 0 o negativa → **422** (RN-REC-01), recepción creando → **403** |
| Dependencia | `C-03` (auth-login-roles), governance BAJO |

De la KB: US-002/US-003 (alta, edición y **desactivación**; un sillón desactivado no acepta turnos nuevos), RN-REC-01 (duración entera > 0; nombres únicos), RN-REC-03 (desactivados no aceptan turnos nuevos, históricos conservados) y la convención de 04: **no se borra físicamente, se desactiva**.

## 2. Qué existe hoy (tras C-01 / C-10) y qué falta

**Existe y sirve de base**

- `app/config.py`: `Config` frozen con `database_path`; `cargar_config()`.
- `app/db/conexion.py`: `abrir_conexion(ruta: Path)`, `transaccion(conexion)` con `BEGIN IMMEDIATE`, `inicializar_esquema(ruta_base, ruta_esquema=None)`.
- `app/db/esquema.sql`: solo comentarios; documenta la convención `CREATE TABLE IF NOT EXISTS` y que **no hay migraciones**.
- `app/main.py`: `create_app(config)` + `lifespan` que aplica el esquema, `app.state.config`, router `/health`.
- `tests/conftest.py`: `config` (SQLite temporal por test) y `cliente` (`TestClient` como context manager, dispara lifespan).
- `app/domain/models.py`: `Prestacion(id, nombre, duracion_minutos, activa=True)`.
- `app/domain/errores.py`: `ErrorDominio`, `DatoInvalido` (422), `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`.

**Falta**

- Tablas `sillon` y `prestacion` en `esquema.sql`.
- Dataclass `Sillon` (no está en `models.py`; C-02 tampoco la incluye en su scope).
- `app/db/repositorio.py` (no existe) y cualquier repositorio de recursos.
- `app/api/recursos.py` (no existe) y el montaje de routers en `create_app`.
- Una dependencia de conexión por request: hoy nadie lee `app.state.config.database_path` fuera del `lifespan`.
- Handler global de errores → JSON en español (RN-GLO-01); no hay ninguno.
- `app/api/auth.py` con `usuario_actual` y `requiere_rol` (C-03).

El working tree está limpio y `openspec/changes/` solo tiene `archive/` (el directorio fantasma de C-01 ya no está).

## 3. Diseñable y testeable **ya** vs bloqueado por C-03

**Se puede diseñar y testear sin C-03**

| Área | Qué se prueba |
|---|---|
| Esquema | Tablas creadas al arrancar, `UNIQUE(nombre)`, `CHECK(duracion_minutos > 0)`, `activo/activa` con default 1, reaplicar el esquema dos veces |
| Dominio puro | `duracion_minutos <= 0` → `DatoInvalido`; nombre vacío/blanco → `DatoInvalido`; normalización de nombre |
| API | `POST` válido (201), duplicado (409), vacío (422), duración 0/negativa (422), `GET` lista, `PATCH` de nombre/`activo`/`activa`, `PATCH` id inexistente (404) |
| Baja lógica | Tras `PATCH {activo:false}` la fila sigue existiendo y se lista como inactiva; no se expone `DELETE` |
| Persistencia | `sqlite3.IntegrityError` de UNIQUE traducido a 409; concurrencia de dos altas con el mismo nombre |
| Contrato | `Prestacion.duracion_minutos` como entero > 0, que es lo que consume `validar_alta` de C-10 |

**Bloqueado por C-03**

- **401** sin token en los 6 endpoints.
- **403** de recepción y odontólogo al crear/editar.
- **200** de recepción/odontólogo en los `GET`.
- **201/200** de administración sobre rutas ya protegidas.
- La matriz RBAC real de `03` §RBAC (fila Sillones/boxes y Prestaciones: `C L E B` / `L` / `L`).
- El **cuerpo JSON en español** de 409/422/404 (RN-GLO-01): los handlers son de C-03. Se pueden asegurar los **status codes** ahora, pero no el formato del body.
- Las fixtures de cliente autenticado (token de administración/recepción), que C-03 debería proveer.

Consecuencia práctica: C-05 completo no se puede archivar antes de C-03, porque le faltarían los tests de 403/401 y el contrato de errores. Sí se puede adelantar **tablas + dominio + repositorio** con TDD, sin endpoints, y dejar el change abierto.

## 4. Riesgos y decisiones antes del propose

| # | Riesgo / duda | Recomendación |
|---|---|---|
| 1 | **C-04 y C-05 son paralelos** (ambos Agente B/C según el roadmap) y tocan `esquema.sql`, `main.py`, `models.py` y probablemente `repositorio.py`/`recursos.py` | Acordar dueño de archivos compartidos o un módulo por recurso (`app/api/sillones.py`, `app/api/prestaciones.py`) antes de arrancar |
| 2 | Falta `Sillon` en `models.py`; agregarla toca un archivo de C-02, que sigue `[ ]` | Agregarla en C-05 (dataclass frozen, `id`, `nombre`, `activo=True`) y anotarlo en el design; no esperar a C-02 |
| 3 | `sillon.activo` vs `prestacion.activa` (la KB usa nombres distintos) | Seguir la KB literal para no romper `Prestacion` de C-10; documentar la asimetría |
| 4 | Unicidad: ¿case-insensitive? ¿`trim`? SQLite `UNIQUE` es case-sensitive y `NOCASE` solo cubre ASCII (no ñ/acentos) | Normalizar con `strip()` al guardar y UNIQUE simple; documentar que "Sillón 1" y "sillón 1" son distintos, o forzar `NOCASE` aceptando la limitación |
| 5 | Validación de duración: `Pydantic Field(gt=0)` vs función de dominio (regla dura 8) | Pydantic valida forma/tipo; la **regla** RN-REC-01 vive en `app/domain/` y se testea sin HTTP. Definir cuál produce el 422 para no duplicar mensajes |
| 6 | Precisión del 409: ¿se chequea antes de insertar o se deja que falle el UNIQUE? | Dejar que falle el UNIQUE dentro de `transaccion()` y traducir `IntegrityError`; el chequeo previo es carrera |
| 7 | Desactivar un sillón con turnos futuros: RN-REC-03 solo dice "no acepta nuevos" | Permitir la baja y conservar turnos; listar/warn queda fuera de scope |
| 8 | `GET` de colección: ¿incluye inactivos? ¿`?activo=true`? | Incluir todos con su flag (como C-04: "desactivado sigue listándose"); filtro opcional fuera de scope |
| 9 | `PATCH` parcial: distinguir campo omitido de `null` | `exclude_unset=True`; renombrar a nombre existente → 409, a vacío → 422 |
| 10 | 404 no figura en RN-GLO-01 | Definir body en español y agregarlo al mapeo de C-03 |
| 11 | `201` vs `200` en `POST` y `Location` | Usar 201 + body con `id` (convención REST); confirmarlo en el propose |
| 12 | Nombre de la capability en OpenSpec | `sillones-prestaciones` es el change; como capability conviene `gestion-recursos` o dos (`sillones`, `prestaciones`) |
| 13 | Auditoría de recursos | Fuera de scope: IF-06 dice que el MVP audita solo turnos (RN-AUD-01) |
| 14 | La dependencia de conexión por request no puede vivir en `app/db/` (regla dura 1: `db` no importa FastAPI) | Crearla en `app/api/deps.py` leyendo `request.app.state.config.database_path`, compartida con C-04 |

## 5. Resumen

C-05 es un CRUD de dos recursos con baja lógica, sin auditoría y con tres reglas duras de negocio: nombre único (409), duración entera > 0 (422, RN-REC-01) y solo administración crea/edita (403, RN-REC-03 + RBAC). La persistencia y las validaciones son **totalmente testeables ya**; los permisos, el 401/403 y el formato español de errores dependen de C-03, que es CRITICO y dueño de `app/api/auth.py` y del mapeo global. El roadmap ya ubica C-05 en el paso 3, con C-03 en el paso 2, así que lo natural es **esperar C-03 para el propose completo**; si se quiere adelantar, hacerlo solo con tablas + dominio + repositorio y no archivar.

**Fuentes consultadas**

- `CHANGES.md` §C-05 (scope, dependencias, governance BAJO), §C-03, §C-04 y §Riesgos del roadmap.
- `knowledge-base/04_modelo_de_datos.md` §Convenciones, §Sillon, §Prestacion.
- `knowledge-base/05_reglas_de_negocio.md` §RN-REC-01, §RN-REC-03.
- `knowledge-base/06_funcionalidades.md` §US-002, §US-003.
- `knowledge-base/03_actores_y_roles.md` §RBAC, §Rutas públicas.
- `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Testing, §Seguridad.
- `knowledge-base/10_preguntas_abiertas.md` §IF-06 (alcance de auditoría).
- Repo: `app/config.py`, `app/main.py`, `app/api/salud.py`, `app/db/conexion.py`, `app/db/esquema.sql`, `app/domain/{models,errores}.py`, `tests/conftest.py`, `openspec/specs/base-tecnica/spec.md`.
