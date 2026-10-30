# Proposal — C-14 agenda

## Why

El personal del consultorio odontológico (administración y recepción) necesita visualizar la ocupación diaria y semanal tanto de cada profesional como de cada sillón dental para organizar la atención, verificar huecos libres y evitar superposiciones (`US-009`, `US-010`, `Flujo 6`). Asimismo, cada odontólogo necesita consultar su propia agenda de pacientes sin tener visibilidad sobre la agenda de sus colegas (`RN-ACC-03`, `03_actores_y_roles.md`).

`C-14` forma parte de la `Fase 4` (Consultas y trazabilidad) y se ejecuta en paralelo con `C-12` (`cancelar-turno`) y `C-13` (`reprogramar-turno`) una vez que `C-11` (`crear-turno`) esté disponible.

## What Changes

1. **Capa de Persistencia (`app/db/repositorio_agenda.py`):**
   - Función `consultar_agenda_profesional(conexion, profesional_id, desde, hasta)`:
     - Recupera turnos activos (`estado = 'reservado'`) del profesional en el rango `[desde, hasta]`.
     - Recupera bloqueos vigentes con `alcance = 'profesional'` y `recurso_id = profesional_id` en el rango.
     - Ordena todos los resultados cronológicamente por `inicio ASC`.
   - Función `consultar_agenda_sillon(conexion, sillon_id, desde, hasta)`:
     - Recupera turnos activos (`estado = 'reservado'`) del sillón en el rango `[desde, hasta]`.
     - Recupera bloqueos vigentes con `alcance = 'sillon'` y `recurso_id = sillon_id` en el rango.
     - Ordena todos los resultados cronológicamente por `inicio ASC`.

2. **Capa API (`app/api/agenda.py`):**
   - Endpoints:
     - `GET /agenda/profesionales/{id}?desde={iso}&hasta={iso}`
     - `GET /agenda/sillones/{id}?desde={iso}&hasta={iso}`
   - Control de acceso:
     - `administracion` y `recepcion`: acceso total a ambas rutas.
     - `odontologo`: solo puede invocar `GET /agenda/profesionales/{id}` cuando `id == usuario.profesional_id`. Si intenta consultar otro profesional o un sillón, recibe HTTP 403 (`SinPermiso`).
     - Usuario no autenticado: HTTP 401 (`NoAutenticado`).
   - Validación de parámetros:
     - Si `desde > hasta` → HTTP 422 (`DatoInvalido`).
     - Si el profesional o sillón no existe → HTTP 404 (`ProfesionalNoEncontrado` / `SillonNoEncontrado`).
   - Formato de respuesta JSON:
     - Incluye metadatos del recurso, lista unificada `items` ordenada por `inicio` con indicador de tipo (`"tipo": "turno" | "bloqueo"`), y listas independientes `turnos` y `bloqueos`.

3. **Tests:**
   - Tests de orden cronológico por `inicio`.
   - Tests de exclusión estricta de turnos con `estado = 'cancelado'` (`RN-TUR-08`).
   - Tests de inclusión de bloqueos correspondientes.
   - Tests de validación de rango `desde > hasta` → 422.
   - Tests de control RBAC: odontólogo consultando a otro profesional → 403; odontólogo consultando un sillón → 403; administración y recepción con acceso completo.

**Fuera de alcance:** vistas de calendario en frontend o exportación a PDF/iCal (fuera del MVP, informe D.3).

## Capabilities

### New Capabilities
- `agenda-profesional`: consulta filtrada y ordenada de turnos y bloqueos de un profesional por rango temporal con restricción RBAC.
- `agenda-sillon`: consulta filtrada y ordenada de turnos y bloqueos de un sillón por rango temporal para administración y recepción.

### Modified Capabilities
- Ninguna.

## Impact

- **Archivos nuevos:**
  - `openspec/changes/c-14-agenda/` (artefactos OpenSpec).
  - `app/api/agenda.py` (router de agenda).
  - `app/db/repositorio_agenda.py` (consultas SQLite de agenda).
  - `tests/api/test_agenda.py` (suite de tests de endpoints y permisos).
- **Archivos modificados:**
  - `app/main.py`: montaje del router `/agenda`.
- **Dependencias:**
  - Requiere `C-04` (`profesionales`), `C-05` (`sillones`), `C-09` (`bloqueos`) y `C-11` (`crear-turno`).
- **Governance:** MEDIO.
