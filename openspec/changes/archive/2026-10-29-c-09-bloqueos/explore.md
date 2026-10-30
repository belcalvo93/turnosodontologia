# Explore — C-09 bloqueos

> Relevamiento previo al propose. También guardado en Engram: `Exploración C-09 bloqueos` (topic `opsx/c-09-bloqueos/explore`).
> Durante la exploración no se creó ni modificó ningún otro archivo del proyecto.

## 1. Qué pide C-09 (`CHANGES.md` L294-310)

| Ítem | Contenido |
|---|---|
| Tabla | `bloqueo` (`id`, `alcance` profesional\|sillón, `recurso_id`, `inicio`, `fin`, `motivo`) con índice (`alcance`, `recurso_id`, `inicio`) |
| Dominio | `inicio < fin` (`RN-REC-02`) |
| Endpoints | `GET /bloqueos`, `POST /bloqueos`, `DELETE /bloqueos/{id}` |
| Permisos | Administración **C L B**; recepción y odontólogo **solo L** (`03_actores_y_roles.md`) |
| Fuera de alcance | Listar turnos afectados por el bloqueo (va en `C-16`, sujeto a `SE-09`); alcance "consultorio" general (`SE-24`, etapa posterior) |
| Tests exigidos | `inicio >= fin` → **422**, recurso inexistente → **422**, eliminar bloqueo, recepción creando → **403** |
| Dependencias | `C-02` (`dominio-base`), `C-04` (`profesionales`), `C-05` (`sillones-prestaciones`); governance **MEDIO** |

De la KB:
- **US-005 (`06_funcionalidades.md`):** bloquear intervalos de un profesional (vacaciones, feriados) o de un sillón (mantenimiento) para que no se den turnos en esos intervalos; se puede eliminar un bloqueo y el horario vuelve a estar disponible.
- **Flujo 5 (`07_flujos_principales.md`):** `POST /bloqueos` con alcance (`profesional` o `sillon`), recurso, `inicio`, `fin` y `motivo`; el dominio valida `inicio < fin` (`RN-REC-02`); `inicio >= fin` → `422`, recurso inexistente → `422`.
- **Modelo (`04_modelo_de_datos.md` §Bloqueo y §Convenciones):** fechas guardadas como texto ISO 8601 local sin offset (`YYYY-MM-DDTHH:MM:SS`); índice `(alcance, recurso_id, inicio)`.

## 2. Qué existe hoy y qué falta

**Existe y sirve de base**

- `app/domain/models.py`: ya define `AlcanceBloqueo = Literal["profesional", "sillon"]` y la dataclass `Bloqueo(alcance, recurso_id, inicio, fin, motivo="")` (adelantada en `C-10`).
- `app/domain/errores.py`: `DatoInvalido` (se mapea a `422`).
- `app/domain/reglas_turno.py`: ya consume `Sequence[Bloqueo]` en `validar_alta` (`RN-TUR-05`).
- `app/db/conexion.py`: `abrir_conexion`, `transaccion`, `inicializar_esquema`.

**Falta**

- Agregar `id: int | None = None` a `Bloqueo` en `app/domain/models.py` (con default `None` para no romper ningún test de `C-10`) y la validación de dominio de `Bloqueo` (`inicio < fin`, `alcance` válido, `motivo` normalizado) que lance `DatoInvalido`.
- Tabla `bloqueo` e índice `idx_bloqueo_alcance_recurso_inicio` en `app/db/esquema.sql`.
- Repositorio `app/db/repositorio_bloqueos.py`: conversión manual entre `datetime` sin offset e ISO 8601 (`isoformat()` / `datetime.fromisoformat()`), verificación de existencia del recurso en `profesional` o `sillon` según `alcance`, inserción, listado y borrado físico (`DELETE`, ya que US-005 e índice `CHANGES.md` piden eliminar bloqueos).
- Router `app/api/bloqueos.py`: `GET /bloqueos`, `POST /bloqueos` (`201`) y `DELETE /bloqueos/{id}` (`204` o `200`, y `404` si no existe).

## 3. Riesgos y decisiones para el propose

| # | Riesgo / duda | Recomendación |
|---|---|---|
| 1 | **Relación polimórfica `(alcance, recurso_id)` en SQLite** | SQLite no soporta FK condicional a `profesional(id)` o `sillon(id)` según el valor de `alcance`. La tabla `bloqueo` define `CHECK (alcance IN ('profesional', 'sillon'))` y `CHECK (inicio < fin)`, y el repositorio verifica dentro de la misma transacción que el `recurso_id` exista en `profesional` (cuando `alcance == 'profesional'`) o en `sillon` (cuando `alcance == 'sillon'`); si no existe, lanza `DatoInvalido` → `422` |
| 2 | **Compatibilidad de `Bloqueo` con `C-10`** | En `app/domain/models.py`, `Bloqueo` ya existe con `kw_only=True`. Agregar `id: int | None = None` como campo opcional al final preserva el 100 % de compatibilidad con `tests/domain/test_reglas_turno.py` |
| 3 | **Formato de fechas en SQLite (D6 de C-01 / KB 04)** | Guardar `inicio` y `fin` como texto ISO 8601 sin zona horaria (`YYYY-MM-DDTHH:MM:SS`). Si la API recibe un `datetime` con `tzinfo`, rechazarlo con `DatoInvalido` (422) o exigir fechas locales sin offset conforme a `04_modelo_de_datos.md` |
| 4 | **Borrado de bloqueo (`DELETE /bloqueos/{id}`)** | A diferencia de profesionales y sillones (que usan baja lógica porque tienen turnos históricos asociados), un bloqueo se elimina físicamente (`DELETE FROM bloqueo WHERE id = ?`) como pide `CHANGES.md` (`GET/POST/DELETE /bloqueos` y test *"eliminar bloqueo"*) y `US-005` (*"Se puede eliminar un bloqueo y el horario vuelve a estar disponible"*). Si el `id` no existe, responde `404` |
| 5 | **Separación con `C-16 bloqueos-turnos-afectados`** | `CHANGES.md` L300 aclara: *"Fuera de alcance de este change: listar turnos afectados por el bloqueo (va en C-16)"*. En `C-09`, `POST /bloqueos` devuelve el bloqueo creado (`201`) sin consultar la tabla `turno` (que recién se crea en `C-11`) |

## 4. Resumen

`C-09 bloqueos` está en el camino crítico entre `C-04`/`C-05` y `C-11 crear-turno`. Incorpora la validación de dominio `inicio < fin` (`RN-REC-02`), la tabla `bloqueo` con su índice `(alcance, recurso_id, inicio)`, la verificación de existencia del profesional o sillón referenciado (`422` si no existe) y los endpoints `GET /bloqueos`, `POST /bloqueos` y `DELETE /bloqueos/{id}` protegidos por rol.

**Fuentes consultadas**

- `CHANGES.md` §C-09, §Camino crítico y §Riesgos del roadmap (`SE-09`, `SE-24`).
- `knowledge-base/04_modelo_de_datos.md` §Bloqueo, §Convenciones.
- `knowledge-base/06_funcionalidades.md` §US-005.
- `knowledge-base/07_flujos_principales.md` §Flujo 5.
- `knowledge-base/05_reglas_de_negocio.md` §RN-REC-02, §RN-TUR-05, §RN-ACC-02, §RN-GLO-01.
- `knowledge-base/10_preguntas_abiertas.md` §SE-09, §SE-24.
- Repo: `app/domain/models.py`, `app/domain/reglas_turno.py`, `app/domain/errores.py`, `app/db/conexion.py`.
