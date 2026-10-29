# Proposal — C-06 pacientes

## Why

Recepción necesita cargar y mantener los pacientes a los que luego se les asigna un turno (US-011). Sin la entidad `Paciente`, `C-11 crear-turno` no tiene a quién referenciar su `paciente_id` ni contra qué validar la existencia del paciente. `C-06` está en la fase 2 del roadmap, depende de `C-03` (ya archivado) y es dependencia directa de `C-11`.

## What Changes

- Se agrega la tabla `paciente` (`nombre`, `apellido`, `dni` obligatorios; `dni` único; `telefono`, `obra_social` y `nro_afiliado` opcionales) al final de `app/db/esquema.sql` con `CREATE TABLE IF NOT EXISTS`. Sin `activo`, sin baja lógica y sin `DELETE`.
- Se agrega la dataclass `Paciente` y la validación pura `validar_datos_paciente(...)` en `app/domain/models.py`: `strip()` de nombre, apellido y DNI; rechazo de vacíos con `DatoInvalido`; opcionales normalizados con `strip()` y `"" → None`.
- Se agrega el error de dominio `DniDuplicado` en `app/domain/errores.py` y su mapeo global a `409` con código `dni_duplicado` en `app/api/errores.py`. El mensaje en español no repite el DNI recibido.
- Se agrega `app/db/repositorio_pacientes.py` con SQL parametrizado: `crear_paciente`, `listar_pacientes`, `obtener_paciente_por_id` y `actualizar_paciente` con centinela `_SIN_CAMBIO`. El `UNIQUE(dni)` se traduce a `DniDuplicado` dentro de una `transaccion()`.
- Se agrega `app/api/pacientes.py`, montado en `app/main.py`:
  - `GET /pacientes` → `200` para administración y recepción; odontólogo `403` hasta que `C-11` permita acotar la lectura a sus turnos.
  - `POST /pacientes` → `201` para administración y recepción.
  - `PATCH /pacientes/{id}` → `200` para administración y recepción; `404` con `codigo` `no_encontrado`; `409` por DNI duplicado; `422` por datos inválidos o `null` en campos obligatorios.
- Se agregan tests de dominio, repositorio y API, con un test por regla: alta con y sin datos opcionales, normalización con `strip()`, campos obligatorios vacíos, DNI duplicado, listado, edición de cada campo, limpieza de opcionales con `null`, `null` rechazado en obligatorios, `404`, `403` y `401`.

**Fuera de alcance:** baja lógica o borrado de pacientes, búsqueda o filtro por DNI, exportación, validación del número de afiliado contra la obra social, liquidación a obras sociales (IF-02), lectura del odontólogo acotada a sus turnos (se habilita en `C-11`), auditoría de pacientes (IF-06: el MVP audita solo turnos) y normalización del DNI más allá de `strip()`.

## Capabilities

### New Capabilities

- `pacientes`: alta, listado y edición parcial de pacientes con DNI único y datos opcionales de contacto y cobertura, con control de acceso por rol y sin baja lógica.

### Modified Capabilities

- `errores-api`: se agrega el código `409 / dni_duplicado` al contrato único de errores para conflictos de unicidad del DNI, sin exponer el error de SQLite ni repetir el valor recibido.

## Impact

- **Archivos nuevos:** `app/api/pacientes.py`, `app/db/repositorio_pacientes.py`, `tests/domain/test_pacientes.py`, `tests/api/test_repositorio_pacientes.py`, `tests/api/test_pacientes.py`.
- **Archivos modificados:** `app/db/esquema.sql` (tabla `paciente`), `app/domain/models.py` (`Paciente` y `validar_datos_paciente`), `app/domain/errores.py` (`DniDuplicado`), `app/api/errores.py` (mapeo `409 dni_duplicado`), `app/main.py` (montaje del router).
- **Sin cambios:** `knowledge-base/`, `CHANGES.md`, `docs/`.
- **Decisiones de alcance:** DNI obligatorio y único con solo `strip()` (SE-15 resuelta para el MVP, con la limitación de pacientes sin DNI documentada); sin `activo` ni `DELETE`; `nro_afiliado` puede existir sin `obra_social`; obra social como texto libre sin liquidación (IF-02 resuelta para el MVP).
- **Dependencias:** `C-03` archivado (auth, RBAC, conexión y contrato de errores). Habilita `C-11 crear-turno`, que usará `obtener_paciente_por_id` y habilitará la lectura del odontólogo acotada a sus turnos.
