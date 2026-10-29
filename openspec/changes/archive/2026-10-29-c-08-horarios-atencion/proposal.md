# Proposal — C-08 horarios-atencion

## Why

Para poder agendar turnos de manera organizada y evitar asignar citas fuera de los días y horarios laborales de cada profesional (RN-PRO-01 y RN-PRO-02), el sistema necesita gestionar las franjas horarias de atención por profesional. `C-08` es una de las dependencias clave de `C-11` (`crear-turno`), el cuello de botella del MVP.

## What Changes

- En `app/domain/models.py`: se agrega `id: int | None = None` a la dataclass `HorarioAtencion` y se implementan las funciones puras `validar_datos_horario`, `validar_franjas_no_superpuestas` y `validar_horario_no_solapa`.
- En `app/db/esquema.sql`: se crea la tabla `horario_atencion` (`id`, `profesional_id`, `dia_semana`, `hora_desde`, `hora_hasta`) y el índice `idx_horario_profesional_dia`.
- En `app/db/repositorio_horarios.py`: se implementan las funciones parametrizadas `crear_horario`, `listar_horarios_por_profesional` y `listar_horarios_por_profesional_y_dia`.
- En `app/api/horarios.py` y `app/main.py`: se implementa y monta el router de horarios con los endpoints:
  - `POST /profesionales/{id}/horarios` (solo administración, `201` o `422` si datos inválidos o profesional inexistente, `403` si otro rol, `401` sin token).
  - `GET /profesionales/{id}/horarios` (administración y recepción leen todos, odontólogo lee solo los propios con `profesional_id == id` (`403` si intenta ver de otro), `404` si profesional inexistente, `401` sin token).
- Tests exhaustivos de dominio en `tests/domain/test_horarios.py` y de persistencia/API en `tests/api/test_horarios.py` y `tests/api/test_repositorio_horarios.py`.

## Capabilities

### New Capabilities

- `horarios-atencion`: gestión y consulta de franjas horarias de atención por profesional y día de la semana con validación de no superposición y permisos por rol.

### Modified Capabilities

Ninguna.

## Impact

- **Archivos nuevos:** `app/api/horarios.py`, `app/db/repositorio_horarios.py`, `tests/domain/test_horarios.py`, `tests/api/test_horarios.py`, `tests/api/test_repositorio_horarios.py`.
- **Archivos modificados:** `app/domain/models.py`, `app/db/esquema.sql`, `app/main.py`.
- **Dependencias:** requiere `C-02` y `C-04`. Desbloquea `C-11` (`crear-turno`).
