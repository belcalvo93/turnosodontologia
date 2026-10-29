# Design — C-09 bloqueos

## Context

`C-09` forma parte del GATE 4 (depende de `C-02`, `C-04` y `C-05`, más `C-03` para autenticación/RBAC) y se ubica en el camino crítico inmediatamente antes de `C-11 crear-turno`. Motivación en `proposal.md`; relevamiento en `explore.md`.

Estado y restricciones:
- `app/domain/models.py` ya cuenta con `AlcanceBloqueo = Literal["profesional", "sillon"]` y la dataclass `Bloqueo(alcance, recurso_id, inicio, fin, motivo="")`, utilizada por `validar_alta` en `app/domain/reglas_turno.py` (`C-10`).
- `C-04` crea la tabla `profesional` y `C-05` crea la tabla `sillon`.
- Reglas duras aplicables (`AGENTS.md`):
  1. `app/domain/` es Python puro (sin FastAPI ni DB).
  4. Consultas SQL parametrizadas.
  7. Errores en JSON en español (`422` dato inválido, `403` sin permiso, `401` sin autenticar, `404` no encontrado).
  8. La regla `inicio < fin` (`RN-REC-02`) se valida en `app/domain/`.

## Goals / Non-Goals

**Goals:**
- Validar `RN-REC-02` (`inicio < fin` y alcance `profesional` | `sillon`) en dominio puro sin tocar DB ni HTTP.
- Persistir bloqueos en SQLite con el índice `(alcance, recurso_id, inicio)` requerido por `04_modelo_de_datos.md` y `CHANGES.md`.
- Verificar dentro de la transacción de escritura que el `recurso_id` exista en `profesional` o `sillon` según `alcance`, devolviendo `422` si no existe.
- Exponer `GET /bloqueos`, `POST /bloqueos` y `DELETE /bloqueos/{id}` con control de roles (`administracion` C L B; `recepcion` y `odontologo` L).

**Non-Goals:**
- Listar o modificar turnos existentes que caigan dentro del nuevo bloqueo (queda explícitamente para `C-16 bloqueos-turnos-afectados` una vez decidida `SE-09`).
- Alcance global `"consultorio"` (`SE-24`, fuera del MVP).
- Auditoría de bloqueos (`IF-06`: el MVP audita solo turnos).

## Decisions

- **D1 — Esquema SQLite e índice.** En `app/db/esquema.sql` se agrega:
  ```sql
  CREATE TABLE IF NOT EXISTS bloqueo (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      alcance TEXT NOT NULL CHECK (alcance IN ('profesional', 'sillon')),
      recurso_id INTEGER NOT NULL,
      inicio TEXT NOT NULL,
      fin TEXT NOT NULL,
      motivo TEXT NOT NULL DEFAULT '',
      CHECK (inicio < fin)
  );

  CREATE INDEX IF NOT EXISTS idx_bloqueo_alcance_recurso_inicio
      ON bloqueo (alcance, recurso_id, inicio);
  ```
  *Por qué:* `inicio` y `fin` se almacenan como texto ISO 8601 local sin offset (`YYYY-MM-DDTHH:MM:SS`), lo que preserva el orden lexicográfico en el `CHECK (inicio < fin)` y en el índice compuesto `(alcance, recurso_id, inicio)` que luego consultarán `C-11` (`crear-turno`) y `C-14` (`agenda`).

- **D2 — Validación polimórfica de `recurso_id` en transacción.** Como `recurso_id` apunta a `profesional(id)` cuando `alcance = 'profesional'` y a `sillon(id)` cuando `alcance = 'sillon'`, SQLite no permite declarar una clave foránea condicional. `crear_bloqueo` ejecuta dentro de `transaccion(conexion)` un `SELECT 1 FROM profesional WHERE id = ?` (o `FROM sillon WHERE id = ?`) antes del `INSERT`; si no encuentra fila, lanza `DatoInvalido("El recurso indicado no existe.")`, que la capa API traduce a `422`.

- **D3 — Extensión compatible de `Bloqueo` en `app/domain/models.py`.** Se agrega el atributo opcional `id: int | None = None` a `Bloqueo` y la función pura `validar_datos_bloqueo(alcance: str, recurso_id: int, inicio: datetime, fin: datetime, motivo: str = "") -> Bloqueo`.
  - Si `alcance` no es `"profesional"` ni `"sillon"`, lanza `DatoInvalido`.
  - Si `inicio.tzinfo is not None` o `fin.tzinfo is not None`, lanza `DatoInvalido` (convención de `04_modelo_de_datos.md`: fechas locales sin offset).
  - Si `inicio >= fin`, lanza `DatoInvalido` (`RN-REC-02`).
  *Por qué:* mantiene los 26 tests existentes de `C-10` intactos y permite probar `RN-REC-02` en `tests/domain/test_bloqueos.py` sin base ni HTTP.

- **D4 — Eliminación física en `DELETE /bloqueos/{id}`.** A diferencia de `profesional` y `sillon` (que usan baja lógica `activo=false`), los bloqueos se eliminan físicamente con `DELETE FROM bloqueo WHERE id = ?`, tal como especifican `US-005` (*"Se puede eliminar un bloqueo y el horario vuelve a estar disponible"*) y `CHANGES.md` (`GET/POST/DELETE /bloqueos`). Responde `204` (o `200` sin cuerpo/confirmación) cuando borra la fila y `404` cuando `cursor.rowcount == 0`.

## Estructura resultante (archivos tocados por C-09)

```
app/
├── main.py                        # monta router de bloqueos
├── domain/
│   └── models.py                  # Bloqueo (+ id opcional) y validar_datos_bloqueo()
├── db/
│   ├── esquema.sql                # + tabla bloqueo e índice idx_bloqueo_alcance_recurso_inicio
│   └── repositorio_bloqueos.py    # crear_bloqueo, listar_bloqueos, eliminar_bloqueo
└── api/
    └── bloqueos.py                # GET/POST /bloqueos, DELETE /bloqueos/{id}
tests/
├── domain/
│   └── test_bloqueos.py           # tests unitarios de RN-REC-02 (inicio < fin, alcance, sin tz)
└── api/
    └── test_bloqueos.py           # tests de API (201, 422 inicio>=fin, 422 recurso inexistente, DELETE, 403, 401)
```

## Risks / Trade-offs

- **[`recurso_id` sin FK declarativa en SQLite]** → Mitigación: verificación explícita dentro de la misma `transaccion()` (`BEGIN IMMEDIATE`) antes de insertar; además, profesionales y sillones no tienen borrado físico (`activo = 0`), por lo que un `recurso_id` válido nunca queda huérfano.
- **[Comparación de texto ISO 8601 en SQLite]** → Mitigación: el repositorio serializa siempre con `inicio.isoformat(timespec="seconds")` (`YYYY-MM-DDTHH:MM:SS`), garantizando formato uniforme.

## Migration Plan

La tabla `bloqueo` y su índice se crean con `IF NOT EXISTS` al iniciar la aplicación. Rollback: revertir el merge del change.

## Open Questions

Ninguna (`SE-09` sobre turnos afectados al crear un bloqueo pertenece a `C-16`, como documenta `CHANGES.md` L127 y L300).
