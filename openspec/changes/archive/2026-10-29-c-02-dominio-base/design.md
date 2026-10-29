# Design — C-02 dominio-base

## Context

`C-02` (`dominio-base`) provee las primitivas fundamentales de `app/domain/` sobre las cuales se construyen los horarios (`C-08`), bloqueos (`C-09`) y el ciclo de vida del turno (`C-10`, `C-11`, `C-12`, `C-13`). Ver `proposal.md` para motivación y `explore.md` para el relevamiento de lo que ya fue adelantado en `C-10` y lo que resta completar.

Restricciones duras aplicables (`AGENTS.md`):
1. `app/domain/` es Python puro: nunca importa FastAPI ni nada de `app/db` o `app/api`.
2. Nunca llamar a `datetime.now()` ni `date.today()` dentro del dominio: el reloj (`ahora: datetime`) se recibe como parámetro (`RN-TUR-09`).
3. Intervalos semiabiertos `[inicio, fin)` en `solapan()`: los turnos contiguos son válidos (`RN-TUR-04`, `SE-10`).
7. Todo error de dominio se traduce en `app/api/errores.py` a un JSON en español con código consistente (`RN-GLO-01`).
11. Cada regla `RN-xx` mapea a al menos un test unitario que corre sin base de datos ni HTTP.
12. `snake_case` y type hints en todas las funciones públicas.

## Goals / Non-Goals

**Goals:**
- Consolidar en `app/domain/models.py` las dataclasses inmutables `Turno`, `Prestacion`, `HorarioAtencion` y `Bloqueo`.
- Proveer en `app/domain/intervalos.py` la comparación de intervalos semiabiertos `solapan(a, b)` (`RN-TUR-04`) y la verificación temporal `es_futuro(turno, ahora)` con reloj inyectado (`RN-TUR-09`).
- Completar en `app/domain/errores.py` los errores base de dominio (`ErrorDominio`, `DatoInvalido`, `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`, `TurnoNoModificable`) y registrar `TurnoNoModificable` en `MAPEO_DOMINIO` de `app/api/errores.py`.
- Cubrir todos los escenarios de borde en `tests/domain/test_intervalos.py` (contiguos, solapamiento parcial, contención, mismo inicio y `es_futuro` antes/igual/después) y la traducción HTTP `409 turno_no_modificable` en `tests/api/test_errores.py`.

**Non-Goals:**
- Validaciones de alta, cancelación o reprogramación de turnos (`C-10`, `C-12`, `C-13`).
- Consultas a base de datos SQLite o endpoints de negocio.

## Decisions

- **D1 — Protocolo estructural `Intervalo` para `solapan` y `es_futuro`.** En `app/domain/intervalos.py`, `Intervalo(Protocol)` define las propiedades `inicio: datetime` y `fin: datetime`. Tanto `solapan(a: Intervalo, b: Intervalo) -> bool` como `es_futuro(turno: Intervalo, ahora: datetime) -> bool` operan sobre ese protocolo.
  *Por qué:* permite usar las mismas funciones puras tanto con `Turno` como con `Bloqueo` sin herencia acoplada ni duplicación.

- **D2 — Semántica estricta de `es_futuro(turno, ahora)` (`RN-TUR-09`).** Devuelve `turno.inicio > ahora`. Si `ahora < turno.inicio` es `True` (futuro); si `ahora == turno.inicio` (en el instante exacto de inicio) o `ahora > turno.inicio` (en curso o pasado) es `False`.
  *Por qué:* `RN-TUR-09` en `knowledge-base/05_reglas_de_negocio.md` especifica explícitamente que con `ahora = 09:00`, un turno de las `10:00` es aceptado, uno de las `08:30` es rechazado y uno de las `09:00` exactas es rechazado.

- **D3 — `TurnoNoModificable` y mapeo HTTP `409`.** Se define `class TurnoNoModificable(ErrorDominio)` en `app/domain/errores.py` y se agrega `TurnoNoModificable: (409, "turno_no_modificable")` en `MAPEO_DOMINIO` de `app/api/errores.py`.
  *Por qué:* `CHANGES.md` (C-12 y C-13) establece que intentar cancelar o reprogramar un turno pasado, en curso o ya cancelado responde `409`, y `tests/api/test_errores.py::test_todo_error_de_dominio_de_la_app_tiene_entrada_en_el_mapeo` verifica que toda subclase de `ErrorDominio` tenga su entrada en `MAPEO_DOMINIO`.

## Risks / Trade-offs

- **[Coordinación con `C-12` en rama `bruno-c12-cancelar-turno`]** → Mitigación: se utilizan exactamente las mismas firmas y nombres (`es_futuro(intervalo: Intervalo, ahora: datetime) -> bool` y `TurnoNoModificable: (409, "turno_no_modificable")`) para que el merge posterior con `C-12` sea limpio y sin conflictos semánticos.
- **[Fechas naive en hora local del consultorio (`SE-05`)]** → Mitigación: todas las comparaciones en `intervalos.py` reciben objetos `datetime` homogéneos en hora local del consultorio inyectados desde la frontera.

## Migration Plan

Sin migración de datos (no modifica tablas SQLite). Rollback: revertir el commit del change.

## Open Questions

Ninguna.
