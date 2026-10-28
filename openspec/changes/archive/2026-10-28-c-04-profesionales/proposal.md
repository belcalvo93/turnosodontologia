# Proposal — C-04 profesionales

## Why

El sistema necesita administrar los profesionales odontológicos (alta, edición, desactivación lógica y listado) para poder asignarles horarios de atención, bloqueos, usuarios con rol odontólogo y turnos. `C-04` está en el camino crítico (`C-01 → C-03 → C-04 → C-09 → C-11 → C-12 → C-15 → C-17`) y desbloquea directamente `C-07` (`gestion-usuarios`), `C-08` (`horarios-atencion`) y `C-09` (`bloqueos`).

## What Changes

- Se agrega la tabla `profesional` en `app/db/esquema.sql` (`id`, `nombre`, `apellido`, `matricula` opcional, `activo` booleano con default `1`) usando `CREATE TABLE IF NOT EXISTS`.
- Se agrega la dataclass `Profesional` en `app/domain/models.py` y la validación pura de dominio (`nombre` y `apellido` obligatorios y no vacíos tras `strip()`, `matricula` opcional normalizada) que lanza `DatoInvalido` (mapeado a HTTP 422).
- Se agregan funciones de persistencia en `app/db/` con SQL parametrizado para crear, listar, obtener por `id` y actualizar parcialmente un profesional (incluyendo baja lógica con `activo=false`, sin borrado físico).
- Se agrega el router de profesionales en `app/api/` montado en `app/main.py` con los endpoints:
  - `GET /profesionales` (autenticado: administración, recepción y odontólogo) — devuelve todos los profesionales, incluyendo los desactivados con `activo=false`.
  - `POST /profesionales` (solo administración) — crea un profesional activo y responde `201`.
  - `PATCH /profesionales/{id}` (solo administración) — edita `nombre`, `apellido`, `matricula` y/o `activo` (baja lógica) y responde `200`, o `404` si el `id` no existe.
- Se agregan tests de dominio (`tests/domain/test_profesionales.py`) y de API (`tests/api/test_profesionales.py`) cubriendo alta válida, `nombre` o `apellido` vacío (`422`), recepción/odontólogo intentando escribir (`403`), request sin token (`401`) y profesional desactivado que sigue listándose como inactivo.

**Fuera de alcance:** borrado físico (`DELETE`), horarios de atención (`C-08`), bloqueos (`C-09`), vinculación de usuarios odontólogos (`C-07`), rechazo de turnos sobre profesional inactivo al reservar (`C-11`) y auditoría de recursos (`IF-06`, el MVP audita solo turnos).

## Capabilities

### New Capabilities

- `profesionales`: gestión de profesionales del consultorio (alta, consulta, edición parcial y baja lógica con control de acceso por rol).

### Modified Capabilities

Ninguna.

## Impact

- **Archivos nuevos:** router de profesionales en `app/api/`, funciones de repositorio de profesionales en `app/db/`, `tests/domain/test_profesionales.py`, `tests/api/test_profesionales.py`.
- **Archivos modificados:** `app/db/esquema.sql` (tabla `profesional`), `app/domain/models.py` (dataclass `Profesional` y validación), `app/main.py` (montaje del router de profesionales).
- **Sin cambios:** `knowledge-base/`, `CHANGES.md` (hasta archivar), `docs/`.
- **Dependencias:** requiere `C-03` (`auth-login-roles`) para las dependencias `usuario_actual`, `requiere_rol` y el mapeo global de errores en español (`RN-GLO-01`). Habilita `C-07`, `C-08` y `C-09` (GATE 4).
