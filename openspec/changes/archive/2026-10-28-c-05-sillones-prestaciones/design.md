# Design — C-05 sillones-prestaciones

## Context

Ver `proposal.md` para motivación. Estado y restricciones que condicionan el enfoque:

- `C-01` dejó `app/db/conexion.py` (`abrir_conexion`, `transaccion` con `BEGIN IMMEDIATE`, `inicializar_esquema`), `app/db/esquema.sql` y `app/main.py` (`create_app`).
- `C-03` archivado aporta `app/api/auth.py` (`usuario_actual` → `401`, `requiere_rol(*roles)` → `403`), `app/api/dependencias.py` (`obtener_conexion` por request) y el mapeo global de errores a JSON en español en `app/api/errores.py` (`RN-GLO-01`).
- `C-04` archivado es el modelo a seguir: dataclass + validación pura en `app/domain/models.py`, repositorio dedicado con SQL parametrizado, router dedicado, tests de dominio/repositorio/API y `PATCH` con `exclude_unset=True`.
- `models.py` ya define `Prestacion(id, nombre, duracion_minutos, activa=True)` para `C-10`; `Sillon` no existe.
- Reglas duras aplicables (`AGENTS.md`): 1 (dominio puro), 4 (SQL parametrizado), 7 (errores en español con código), 8 (reglas de negocio en `app/domain/`, Pydantic solo en la frontera), 11 (cada RN-xx con test), 12 (`snake_case` y type hints).

## Goals / Non-Goals

**Goals:**

- Persistir sillones y prestaciones con baja lógica y nombre único, reutilizando el esquema idempotente y la transacción existentes.
- Validar en dominio la duración entera positiva (RN-REC-01) sin depender de DB ni HTTP.
- Exponer seis endpoints (`GET/POST/PATCH` por recurso) respetando la matriz RBAC: administración escribe, los tres roles leen.
- Dejar lecturas por `id` y listados listos para que `C-09` (bloqueos por sillón) y `C-11` (crear turno) verifiquen existencia y estado activo.
- Traducir el `UNIQUE(nombre)` a un `409` estable sin filtrar el error de SQLite.

**Non-Goals:**

- `DELETE` físico y filtros por estado en el listado.
- Validar el estado activo del sillón o de la prestación al reservar: se hace en `C-11`.
- Unicidad case-insensitive o insensible a acentos.
- Auditoría de recursos (`IF-06`: el MVP audita solo turnos).

## Decisions

- **D1 — Esquema SQLite.** Se agregan las tablas al final de `app/db/esquema.sql`, después de `profesional`:
  ```sql
  CREATE TABLE IF NOT EXISTS sillon (
      id     INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre TEXT    NOT NULL UNIQUE CHECK (length(trim(nombre)) > 0),
      activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
  );
  CREATE TABLE IF NOT EXISTS prestacion (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre           TEXT    NOT NULL UNIQUE CHECK (length(trim(nombre)) > 0),
      duracion_minutos INTEGER NOT NULL CHECK (duracion_minutos > 0),
      activa           INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0, 1))
  );
  ```
  *Por qué:* `CREATE TABLE IF NOT EXISTS` mantiene idempotente a `inicializar_esquema()`; `UNIQUE` implementa el nombre único de RN-REC-01 con índice implícito y sin chequeo previo (evita carreras); los `CHECK` refuerzan las invariantes como red de seguridad. `activo`/`activa` respetan literalmente la asimetría de `knowledge-base/04_modelo_de_datos.md`, igual que `Prestacion.activa` de `C-10`.
  *Alternativa descartada:* `COLLATE NOCASE` para unicidad case-insensitive (solo cubre ASCII, deja fuera ñ y acentos, y contradice la convención `strip()` + `UNIQUE` de `C-04`).

- **D2 — Modelo de dominio.** Se agrega `Sillon(id: int | None = None, nombre: str, activo: bool = True)` en `app/domain/models.py` con el mismo estilo `frozen=True, kw_only=True` de `Profesional` (`id` al final y opcional porque se asigna al insertar). `Prestacion` **no se modifica**: ya existe con `id` requerido para `C-10` y el repositorio siempre la construye con `lastrowid`.
  *Por qué:* no romper el contrato que consume la validación de turnos y mantener cada modelo con el estilo con el que fue creado.

- **D3 — Validaciones puras y reparto con Pydantic.** Se agregan en `app/domain/models.py`:
  - `validar_datos_sillon(nombre) -> str`: `strip()`, rechaza vacío con `DatoInvalido`.
  - `validar_datos_prestacion(nombre, duracion_minutos) -> tuple[str, int]`: `strip()` del nombre y rechazo de vacío; rechazo de `duracion_minutos <= 0` con mensaje en español (RN-REC-01).
  Pydantic valida forma y tipo en la frontera (`nombre: str`, `duracion_minutos: int`); el dominio valida la regla de negocio.
  *Por qué:* regla dura 8. El test de dominio de duración `0`/negativa cubre RN-REC-01 sin DB ni HTTP (regla dura 11).
  *Alternativa descartada:* `Field(gt=0)` en Pydantic como única validación; duplicaría el mensaje y dejaría la regla fuera del dominio.

- **D4 — Nombre duplicado → `409 nombre_duplicado`.** Se agrega `NombreDuplicado(ErrorDominio)` en `app/domain/errores.py` y su entrada `(409, "nombre_duplicado")` en `MAPEO_DOMINIO` de `app/api/errores.py`. Cada repositorio envuelve el `sqlite3.IntegrityError` de `crear_*`/`actualizar_*`: si el mensaje contiene `UNIQUE`, lanza `NombreDuplicado` con un mensaje en español específico del recurso; cualquier otra violación se re-lanza (sería un bug).
  *Por qué:* regla dura 7 (nada ad-hoc, código estable y español) y el `409` debe ser carrera-segura: se deja fallar el `UNIQUE` dentro de `transaccion()` en vez de consultar antes de insertar. `db → domain` está permitido por la regla dura 1. El código se reutilizará en `C-06` para el DNI duplicado.
  *Alternativas descartadas:* `HTTPException(409)` desde el router (el handler genérico lo convertiría en `error_http`, sin código propio); reutilizar `ConflictoAgenda` (semántica de agenda y código engañoso); chequeo previo con `SELECT` (carrera entre request y request).

- **D5 — Un router y un repositorio por recurso.** `app/api/sillones.py` + `app/db/repositorio_sillones.py` y `app/api/prestaciones.py` + `app/db/repositorio_prestaciones.py`, montados en `app/main.py`. Ambos routers reutilizan `obtener_conexion`, `usuario_actual` (GET), `requiere_rol(Rol.ADMINISTRACION)` (POST/PATCH), `transaccion` y los handlers de `app/api/errores.py`.
  *Por qué:* lo pedido explícitamente y lo que `C-04` documentó como mitigación de conflictos con `C-06`, que corre en paralelo y toca `esquema.sql`, `models.py` y `main.py`.
  *Alternativa descartada:* un `app/api/recursos.py` único (KB 08): concentraría los conflictos de merge de los tres changes paralelos.

- **D6 — Semántica de `PATCH` y baja lógica.** Modelos Pydantic de entrada con todos los campos opcionales y `model_dump(exclude_unset=True)` para distinguir campo omitido de campo enviado. Enviar `null` en un campo no anulable responde `422`; `{"activo": false}` / `{"activa": false}` desactiva sin borrar. El candidato se arma combinando el valor actual con los cambios, se revalida en dominio y se persiste con un `UPDATE` que reescribe todas las columnas (patrón `_SIN_CAMBIO` de `C-04`).
  *Por qué:* paridad de comportamiento con `C-04`, que ya está en la KB del proyecto, y evita perder campos no enviados.

- **D7 — Listados completos y ordenados.** `GET` devuelve activos e inactivos ordenados por `id ASC`, sin filtros por query string.
  *Por qué:* administración necesita ver y reactivar registros desactivados; el filtro es alcance nuevo no pedido en `CHANGES.md`.

- **D8 — Respuestas y errores de la API.** `POST` responde `201` con el recurso creado (`id`, `nombre`, `activo`/`activa` y, en prestaciones, `duracion_minutos`); `PATCH` responde `200` con el recurso actualizado; `PATCH` sobre `id` inexistente responde `HTTPException(404)` (el handler global lo traduce a `no_encontrado` en español, como en `C-04`).
  *Por qué:* convención REST ya usada por el change anterior y un único contrato de error.

## Estructura resultante (archivos tocados por C-05)

```
app/
├── main.py                            # monta routers de sillones y prestaciones
├── domain/
│   ├── models.py                      # + Sillon, validar_datos_sillon(), validar_datos_prestacion()
│   └── errores.py                     # + NombreDuplicado
├── db/
│   ├── esquema.sql                    # + CREATE TABLE IF NOT EXISTS sillon / prestacion
│   ├── repositorio_sillones.py        # crear, listar, obtener_por_id, actualizar
│   └── repositorio_prestaciones.py    # crear, listar, obtener_por_id, actualizar
└── api/
    ├── errores.py                     # + mapeo 409 nombre_duplicado
    ├── sillones.py                    # GET/POST /sillones, PATCH /sillones/{id}
    └── prestaciones.py                # GET/POST /prestaciones, PATCH /prestaciones/{id}
tests/
├── domain/
│   ├── test_sillones.py               # validación pura de nombre
│   └── test_prestaciones.py           # RN-REC-01 sin DB ni HTTP
└── api/
    ├── test_repositorio_sillones.py   # esquema, UNIQUE, CRUD, baja lógica
    ├── test_repositorio_prestaciones.py
    ├── test_sillones.py               # 201, 409, 422, 404, 403, 401
    └── test_prestaciones.py           # 201, 409, 422 (duración), 404, 403, 401
```

## Risks / Trade-offs

- **[Conflicto de merge con `C-06` en `esquema.sql`, `models.py`, `errores.py`, `main.py`]** → cambios estrictamente aditivos al final de cada archivo, módulos dedicados por recurso y ningún renombrado de lo existente.
- **[`UNIQUE` case-sensitive: `"Sillón 1"` y `"sillón 1"` conviven]** → se documenta como comportamiento aceptado del MVP; el `strip()` evita duplicados por espacios, que es el caso realista. Cambiar a `NOCASE` queda para una decisión posterior.
- **[Traducción de `IntegrityError` dependiente del texto `UNIQUE` de SQLite]** → el mensaje es estable en SQLite y solo se traduce esa violación; cualquier otro `IntegrityError` sigue propagándose como error interno para no tapar bugs.
- **[Prestaciones inactivas usadas por turnos históricos]** → la baja es lógica y el listado las conserva; `C-11` es quien decide si acepta turnos nuevos.
- **[Duplicación de la validación nombre no vacío entre dominio y `CHECK`]** → deliberada: el `CHECK` protege la base ante escrituras fuera de la API y el dominio produce el `422` con mensaje en español.

## Migration Plan

Las tablas se crean con `CREATE TABLE IF NOT EXISTS` al iniciar la app; no hay migraciones ni backfill. Rollback: revertir el merge del change (las tablas nuevas pueden quedarse vacías sin afectar a los changes previos).

## Open Questions

Ninguna. Las dudas del `explore.md` quedaron resueltas en D1–D8: dos capabilities (`sillones` y `prestaciones`), `409` con código `nombre_duplicado`, caso sensible, listados sin filtro y `404` provisto por el handler de `C-03`.
