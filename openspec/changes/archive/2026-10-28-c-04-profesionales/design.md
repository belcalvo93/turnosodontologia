# Design — C-04 profesionales

## Context

`C-04` es el primer change de recursos del consultorio (GATE 3, después de `C-03 auth-login-roles`) y forma parte del camino crítico (`C-01 → C-03 → C-04 → C-09 → C-11 → C-12 → C-15 → C-17`). Ver `proposal.md` para motivación y `explore.md` para el relevamiento del repositorio.

Estado actual y restricciones técnicas:
- `C-01` dejó `app/config.py`, `app/db/conexion.py` (`abrir_conexion`, `transaccion`, `inicializar_esquema`), `app/db/esquema.sql` y `app/main.py` (`create_app`).
- `C-03` provee `app/api/auth.py` con las dependencias `usuario_actual` (401) y `requiere_rol(*roles)` (403), además del mapeo global de errores a JSON en español (`RN-GLO-01`).
- En GATE 3 corren en paralelo `C-04` (`profesionales`), `C-05` (`sillones-prestaciones`) y `C-06` (`pacientes`).
- Reglas duras aplicables (`AGENTS.md`):
  1. `app/domain/` es Python puro (no importa FastAPI ni `app/db`/`app/api`).
  4. SQL siempre parametrizado (`?`), nunca concatenación.
  7. Errores en JSON en español con código consistente (`422` dato inválido, `403` sin permiso, `401` sin autenticar, `404` no encontrado).
  8. La validación de negocio vive en `app/domain/`; Pydantic valida el esquema de entrada/salida en la frontera HTTP.

## Goals / Non-Goals

**Goals:**
- Persistir profesionales en la tabla `profesional` de SQLite con baja lógica (`activo`).
- Validar las invariantes de negocio de `Profesional` en `app/domain/` sin depender de DB ni HTTP.
- Exponer `GET /profesionales`, `POST /profesionales` y `PATCH /profesionales/{id}` respetando la matriz RBAC de `knowledge-base/03_actores_y_roles.md`.
- Dejar primitivas de lectura por `id` en `app/db/` listas para que `C-07` (`gestion-usuarios`), `C-08` (`horarios-atencion`), `C-09` (`bloqueos`) y `C-11` (`crear-turno`) verifiquen existencia y estado `activo` del profesional.

**Non-Goals:**
- Borrado físico (`DELETE /profesionales/{id}`).
- Horarios de atención (`C-08`) y bloqueos (`C-09`).
- Validación de turnos nuevos contra profesional inactivo (se ejecuta en `C-11` al reservar).
- Auditoría de cambios sobre profesionales (`IF-06`: el MVP audita únicamente turnos).

## Decisions

- **D1 — Esquema SQLite de `profesional`.** Se agrega en `app/db/esquema.sql`:
  ```sql
  CREATE TABLE IF NOT EXISTS profesional (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
      apellido TEXT NOT NULL CHECK (length(trim(apellido)) > 0),
      matricula TEXT,
      activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
  );
  ```
  *Por qué:* `CREATE TABLE IF NOT EXISTS` mantiene la idempotencia de `inicializar_esquema()` establecida en `C-01`. Los `CHECK` en base refuerzan la regla de dominio de `nombre` y `apellido` no vacíos. `matricula` es nullable y sin `UNIQUE` porque `knowledge-base/04_modelo_de_datos.md` y `CHANGES.md` la definen como opcional sin restricción de unicidad.

- **D2 — Modelo y validación en `app/domain/`.** Se agrega la dataclass inmutable `Profesional(id: int | None = None, nombre: str, apellido: str, matricula: str | None = None, activo: bool = True)` en `app/domain/models.py` y una función pura `validar_datos_profesional(nombre: str, apellido: str, matricula: str | None = None) -> tuple[str, str, str | None]` que hace `strip()`, verifica que `nombre` y `apellido` no queden vacíos (lanzando `DatoInvalido` con mensaje claro en español si fallan) y normaliza `matricula` vacía o de espacios a `None`.
  *Por qué:* cumple las reglas duras 1, 8 y 11 (`app/domain/` concentra la regla y se testea sin DB ni HTTP en `tests/domain/test_profesionales.py`), y el router traduce `DatoInvalido` a HTTP `422`.

- **D3 — Módulos dedicados para minimizar conflictos de merge con `C-05` y `C-06`.** Aunque `knowledge-base/08` muestra `app/api/recursos.py` y `app/db/repositorio.py` de forma general, `C-04`, `C-05` y `C-06` se desarrollan en ramas paralelas. Las funciones de persistencia de profesionales se implementan en `app/db/repositorio_profesionales.py` (y se reexportan en `app/db/repositorio.py` si existe) y el router HTTP en `app/api/profesionales.py`, montado en `app/main.py`.
  *Por qué:* evita conflictos de merge de bloque completo con `C-05` (`sillones-prestaciones`), reduciendo la superficie de contacto únicamente a líneas aditivas en `app/db/esquema.sql`, `app/domain/models.py` y `app/main.py`.

- **D4 — Semántica de `PATCH /profesionales/{id}` y baja lógica.** El modelo Pydantic de entrada `ProfesionalActualizar` declara todos los campos opcionales (`nombre: str | None = None`, `apellido: str | None = None`, `matricula: str | None = None`, `activo: bool | None = None`). Se usa `model_dump(exclude_unset=True)` para distinguir entre un campo no enviado (se conserva el valor actual) y un campo enviado explícitamente (p. ej. `{"matricula": null}` limpia la matrícula; `{"activo": false}` desactiva el profesional). Si se envían `nombre` o `apellido` como `null` o string vacío/espacios, se lanza `DatoInvalido` → `422`. Si el `id` no existe en la tabla, se responde `404` con JSON en español.

- **D5 — Listado `GET /profesionales` ordenado e inclusivo.** Devuelve todos los registros ordenados por `id ASC`, incluyendo tanto `activo = True` como `activo = False`.
  *Por qué:* `CHANGES.md` exige verificar que *"desactivado sigue listándose como inactivo"*, y administración necesita ver los profesionales inactivos para poder reactivarlos o consultar el historial.

## Estructura resultante (archivos tocados por C-04)

```
app/
├── main.py                          # monta router de profesionales
├── domain/
│   └── models.py                    # + Profesional y validar_datos_profesional()
├── db/
│   ├── esquema.sql                  # + CREATE TABLE IF NOT EXISTS profesional
│   └── repositorio_profesionales.py # crear, listar, obtener_por_id, actualizar
└── api/
    └── profesionales.py             # GET/POST /profesionales, PATCH /profesionales/{id}
tests/
├── domain/
│   └── test_profesionales.py        # tests unitarios puros (sin DB ni HTTP)
└── api/
    └── test_profesionales.py        # tests con TestClient y SQLite temporal (201, 200, 422, 404, 403, 401)
```

## Risks / Trade-offs

- **[Conflicto de merge en `esquema.sql`, `models.py` y `main.py` con `C-03`/`C-05`]** → Mitigación: cambios estrictamente aditivos al final de cada sección y router/repositorio en archivos dedicados (`profesionales.py`, `repositorio_profesionales.py`).
- **[Dependencia de `C-03` para `auth.py` y handler global `RN-GLO-01`]** → Mitigación: el `apply` de `C-04` se ejecuta una vez mergeado `C-03` en `main`, reutilizando exactamente las dependencias `usuario_actual` y `requiere_rol` que defina `C-03`.
- **[`nombre` o `apellido` con espacios laterales]** → Mitigación: `validar_datos_profesional` aplica `strip()` antes de validar longitud y devuelve los valores limpios para persistir.

## Migration Plan

La tabla `profesional` se agrega con `CREATE TABLE IF NOT EXISTS` en `app/db/esquema.sql`, por lo que `inicializar_esquema()` la crea automáticamente al iniciar la aplicación. Rollback: revertir el merge del change.

## Open Questions

Ninguna.
