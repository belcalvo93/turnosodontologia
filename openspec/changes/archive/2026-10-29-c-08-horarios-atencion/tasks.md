# Tasks — C-08 horarios-atencion

## 1. Dominio puro (`app/domain/`)

- [x] 1.1 Extender `HorarioAtencion` con `id: int | None = None` e implementar `validar_datos_horario(profesional_id, dia_semana, hora_desde, hora_hasta, id=None) -> HorarioAtencion`, `validar_franjas_no_superpuestas(franjas)` y `validar_horario_no_solapa(candidato, existentes)` en `app/domain/models.py`, verificando con tests en `tests/domain/test_horarios.py` (franja invertida inválida, día inválido, dos franjas por día válidas, contiguas válidas y franjas superpuestas inválidas)

## 2. Esquema SQLite y persistencia (`app/db/`)

- [x] 2.1 Agregar `CREATE TABLE IF NOT EXISTS horario_atencion` y el índice `idx_horario_profesional_dia` en `app/db/esquema.sql`
- [x] 2.2 Implementar `app/db/repositorio_horarios.py` (`crear_horario`, `listar_horarios_por_profesional`, `listar_horarios_por_profesional_y_dia`) con consultas SQL parametrizadas, verificando con tests en `tests/api/test_repositorio_horarios.py`

## 3. Router API y control de acceso (`app/api/`)

- [x] 3.1 Implementar el router `app/api/horarios.py` con `GET /profesionales/{id}/horarios` y `POST /profesionales/{id}/horarios`, montarlo en `app/main.py` y verificar con tests en `tests/api/test_horarios.py` (alta 201, franja superpuesta 422, profesional inexistente 422, roles y permisos 401/403/200)

## 4. Verificación integral del change

- [x] 4.1 Ejecutar `pytest tests -v` y verificar que la suite completa pasa en verde
- [x] 4.2 Documentar el reporte en `openspec/changes/archive/2026-10-29-c-08-horarios-atencion/verify.md`, archivar en `openspec/changes/archive/2026-10-29-c-08-horarios-atencion/`, sincronizar `openspec/specs/horarios-atencion/spec.md` y actualizar `CHANGES.md`
