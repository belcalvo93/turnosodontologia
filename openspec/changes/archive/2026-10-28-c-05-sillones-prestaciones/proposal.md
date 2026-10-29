# Proposal — C-05 sillones-prestaciones

## Why

El consultorio necesita administrar los dos recursos que, junto con el profesional, definen cada turno: los sillones/boxes donde se atiende y las prestaciones cuya duración determina el fin del turno (RN-TUR-01). Sin ellos, `C-09` (bloqueos por sillón) y `C-11` (crear turno) no tienen contra qué validar. `C-05` está en la fase 3 del roadmap y depende de `C-03`, ya archivado.

## What Changes

- Se agregan las tablas `sillon` (`nombre` único y no vacío, `activo` con default `1`) y `prestacion` (`nombre` único y no vacío, `duracion_minutos` entero `> 0`, `activa` con default `1`) en `app/db/esquema.sql` usando `CREATE TABLE IF NOT EXISTS`.
- Se agrega la dataclass `Sillon` y las validaciones puras de dominio `validar_datos_sillon(nombre)` y `validar_datos_prestacion(nombre, duracion_minutos)` en `app/domain/models.py`. La dataclass `Prestacion` ya existe y se conserva tal cual.
- Se agrega el error de dominio `NombreDuplicado` (`app/domain/errores.py`) y su mapeo global a `409` con código `nombre_duplicado` en `app/api/errores.py`, reutilizando el contrato de errores de `C-03`.
- Se agregan dos repositorios SQLite con consultas parametrizadas: `app/db/repositorio_sillones.py` y `app/db/repositorio_prestaciones.py`. El `UNIQUE(nombre)` se traduce a `NombreDuplicado` dentro de una `transaccion()`.
- Se agregan dos routers montados en `app/main.py`:
  - `GET/POST /sillones` y `PATCH /sillones/{id}`.
  - `GET/POST /prestaciones` y `PATCH /prestaciones/{id}`.
  - `GET` disponible para los tres roles autenticados; `POST` y `PATCH` solo para `administracion` (`requiere_rol(Rol.ADMINISTRACION)`), con `401` sin token y `403` para recepción/odontólogo.
  - Baja lógica (`activo=false` / `activa=false`), sin `DELETE` físico.
- Se agregan tests de dominio (`tests/domain/test_sillones.py`, `tests/domain/test_prestaciones.py`), de repositorio (`tests/api/test_repositorio_sillones.py`, `tests/api/test_repositorio_prestaciones.py`) y de API (`tests/api/test_sillones.py`, `tests/api/test_prestaciones.py`) cubriendo `201`, `409` por nombre duplicado, `422` por nombre vacío o duración `0`/negativa (RN-REC-01), `404`, `403`, `401` y baja lógica que sigue listándose.

**Fuera de alcance:** borrado físico (`DELETE`), filtros por estado en el listado, rechazo de turnos sobre sillón inactivo al reservar (se valida en `C-11`), bloqueos (`C-09`), auditoría de recursos (`IF-06`: el MVP audita solo turnos) y unicidad case-insensitive.

## Capabilities

### New Capabilities

- `sillones`: alta, listado, edición parcial y desactivación lógica de sillones/boxes con nombre único y control de acceso por rol.
- `prestaciones`: alta, listado, edición parcial y desactivación lógica de prestaciones con nombre único y duración entera mayor que cero (RN-REC-01).

### Modified Capabilities

- `errores-api`: se agrega el código `409 / nombre_duplicado` al contrato único de errores para conflictos de unicidad, sin exponer el error de SQLite.

## Impact

- **Archivos nuevos:** `app/api/sillones.py`, `app/api/prestaciones.py`, `app/db/repositorio_sillones.py`, `app/db/repositorio_prestaciones.py`, `tests/domain/test_sillones.py`, `tests/domain/test_prestaciones.py`, `tests/api/test_repositorio_sillones.py`, `tests/api/test_repositorio_prestaciones.py`, `tests/api/test_sillones.py`, `tests/api/test_prestaciones.py`.
- **Archivos modificados:** `app/db/esquema.sql` (tablas `sillon` y `prestacion`), `app/domain/models.py` (`Sillon` y validaciones), `app/domain/errores.py` (`NombreDuplicado`), `app/api/errores.py` (mapeo `409 nombre_duplicado`), `app/main.py` (montaje de dos routers).
- **Sin cambios:** `knowledge-base/`, `CHANGES.md`, `docs/`.
- **Dependencias:** `C-03` archivado (aporta `usuario_actual`, `requiere_rol`, `obtener_conexion`, `transaccion` y el mapeo global de errores). Habilita `C-09` (bloqueos por sillón) y `C-11` (crear turno con sillón y prestación).
