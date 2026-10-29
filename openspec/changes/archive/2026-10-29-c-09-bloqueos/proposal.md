# Proposal — C-09 bloqueos

## Why

El consultorio necesita bloquear intervalos de tiempo para un profesional (vacaciones, feriados, licencias) o para un sillón (mantenimiento) de modo que no se puedan agendar turnos en esos rangos (`RN-REC-02`, `RN-TUR-05`). `C-09` forma parte del camino crítico (`C-01 → C-03 → C-04 → C-09 → C-11 → C-12 → C-15 → C-17`) y es una de las 4 dependencias directas de `C-11 crear-turno`.

## What Changes

- Se agrega la tabla `bloqueo` (`id`, `alcance` en `profesional` | `sillon`, `recurso_id`, `inicio`, `fin`, `motivo`) y el índice `idx_bloqueo_alcance_recurso_inicio` sobre `(alcance, recurso_id, inicio)` en `app/db/esquema.sql`.
- Se extiende `Bloqueo` en `app/domain/models.py` con `id: int | None = None` (conservando compatibilidad con `C-10`) y se agrega la validación pura de dominio `validar_datos_bloqueo(...)` que exige `inicio < fin` (`RN-REC-02`), fechas locales sin offset y `alcance` válido, lanzando `DatoInvalido` (`422`) ante valores inválidos.
- Se implementa `app/db/repositorio_bloqueos.py` con SQL parametrizado para verificar la existencia del recurso en `profesional` o `sillon` según `alcance` (lanzando `DatoInvalido` → `422` si no existe), crear, listar y eliminar bloqueos.
- Se implementa el router `app/api/bloqueos.py` montado en `app/main.py` con:
  - `GET /bloqueos` (autenticado: administración, recepción y odontólogo).
  - `POST /bloqueos` (solo administración) — valida dominio y existencia del recurso y devuelve `201`.
  - `DELETE /bloqueos/{id}` (solo administración) — elimina el bloqueo para liberar el horario (`US-005`) o responde `404` si no existe.
- Se agregan tests de dominio (`tests/domain/test_bloqueos.py`) y de API (`tests/api/test_bloqueos.py`) cubriendo `inicio >= fin` (`422`), recurso inexistente (`422`), alta y eliminación de bloqueo, y recepción/odontólogo intentando crear o eliminar (`403`).

**Fuera de alcance:** listar turnos activos afectados al crear un bloqueo (corresponde a `C-16 bloqueos-turnos-afectados`, sujeto a `SE-09`), alcance general "consultorio" (`SE-24`, etapa posterior) y auditoría de recursos (`IF-06`).

## Capabilities

### New Capabilities

- `bloqueos`: gestión de bloqueos horarios sobre profesionales o sillones (alta validando intervalo y recurso existente, consulta y eliminación con control de acceso por rol).

### Modified Capabilities

Ninguna.

## Impact

- **Archivos nuevos:** `app/db/repositorio_bloqueos.py`, `app/api/bloqueos.py`, `tests/domain/test_bloqueos.py`, `tests/api/test_bloqueos.py`.
- **Archivos modificados:** `app/db/esquema.sql` (tabla `bloqueo` e índice), `app/domain/models.py` (`id` opcional en `Bloqueo` y función `validar_datos_bloqueo`), `app/main.py` (montaje del router de bloqueos).
- **Sin cambios:** `knowledge-base/`, `CHANGES.md` (hasta archivar), `docs/`.
- **Dependencias:** requiere `C-02` (`dominio-base`), `C-04` (`profesionales`) y `C-05` (`sillones-prestaciones`), además de `C-03` (`auth-login-roles`). Habilita `C-11` (`crear-turno`).
