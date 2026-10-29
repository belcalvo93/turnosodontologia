# Proposal — C-11 crear-turno

## Why

El núcleo del MVP es reservar turnos sin superposiciones de profesional, sillón ni paciente (`US-006`, Flujo 2). Hoy la regla de alta existe solo como función pura (`validar_alta`, `C-10`), sin tablas `turno` ni `auditoria_turno` ni endpoints. `C-11` está en el camino crítico (`C-01 → C-03 → C-04 → C-09 → C-11 → C-12 → C-15 → C-17`), es el cuello de botella del roadmap (depende de 4 changes y bloquea 5) y sus dependencias (`C-06`, `C-08`, `C-09`, `C-10`) ya están en `main`.

## What Changes

- Se agregan a `app/db/esquema.sql` las tablas `turno` (con `creado_por` y `creado_en`, `CHECK (inicio < fin)`, `estado` en `reservado` | `cancelado` y los tres índices de KB 04 por profesional, sillón y paciente + `inicio`) y `auditoria_turno` (solo inserción: `UPDATE` y `DELETE` se rechazan en la base).
- Se implementa `POST /turnos` (solo `administracion` y `recepcion`): en **una sola transacción de escritura** carga el contexto, valida con el dominio (`validar_alta`, sin modificarla) e inserta el turno `reservado` junto con su auditoría `crear`. Responde `201`.
- Se implementa `GET /turnos/{id}` (autenticado): `404` si no existe; el odontólogo solo ve turnos de su propio profesional (`RN-ACC-03`), si no `403`.
- Traducción de errores (`RN-GLO-01`): solapamiento, fuera de horario o bloqueo → `409`; recurso inexistente o inactivo, falta de `sillon_id` o `inicio` con zona horaria → `422`; rol sin permiso → `403`; sin token → `401`.
- Se agrega la dependencia `obtener_ahora_local` (hora local del consultorio sin `tzinfo`, a partir del reloj inyectado y `CLINIC_TIMEZONE`) para `creado_en` y `ocurrio_en`. `obtener_ahora` (UTC, JWT) no cambia.
- Se define el **formato canónico** de `antes`/`despues` de la auditoría (snapshot completo del turno) que `C-12` y `C-13` deben reutilizar.
- Se exponen piezas reutilizables para `C-12`, `C-13` y `C-14`: `TurnoResponse`, la conversión fila → `Turno`, `obtener_turno` y el registro de auditoría.
- Se agrega `tzdata` a `requirements.txt`: en Windows `zoneinfo` no trae la base de zonas horarias.

**Fuera de alcance:** cancelar (`C-12`), reprogramar (`C-13`), agenda por rango (`C-14`), lectura de auditoría (`C-15`), rechazo de altas en el pasado (mejora futura, ver design) y auditoría de recursos (`IF-06`: el MVP audita solo turnos).

## Capabilities

### New Capabilities

- `turnos`: alta de turnos con validación completa de agenda en una única transacción, consulta por id y control de acceso por rol (incluido `RN-ACC-03` en la consulta).
- `auditoria-turnos`: registro append-only de cada modificación de un turno (quién, qué y cuándo), con formato canónico del snapshot y atomicidad con la operación auditada. `C-11` cubre la acción `crear`; `C-12`, `C-13` y `C-15` lo extienden.

### Modified Capabilities

Ninguna. `reglas-alta-turno` no cambia (`validar_alta` se reutiliza tal cual) y `errores-api` ya cubre los códigos `409`, `422`, `403`, `401` y `404` que se usan.

## Impact

- **Archivos nuevos:** `app/db/repositorio_turnos.py`, `app/api/turnos.py`, `tests/api/test_turnos.py`, `tests/api/test_repositorio_turnos.py`, `tests/api/test_hora_local.py`, `tests/domain/test_recursos_alta.py`, `tests/domain/test_permisos_turno.py`.
- **Archivos modificados:** `app/db/esquema.sql` (tablas, índices y triggers), `app/db/repositorio_bloqueos.py` (consulta de bloqueos por recursos e intervalo), `app/domain/reglas_turno.py` (nueva `validar_recursos_alta`; `validar_alta` intacta), `app/domain/usuarios.py` (nueva `puede_ver_turno`), `app/api/dependencias.py` (`obtener_ahora_local`), `app/main.py` (monta el router) y `requirements.txt` (`tzdata`). Los tests del esquema viven en `tests/api/test_repositorio_turnos.py`.
- **Sin cambios:** `app/domain/models.py` (`Turno` queda igual), `knowledge-base/`, `CHANGES.md` (hasta archivar), `docs/`, y los designs de `C-12`, `C-13` y `C-14` (sus ajustes se listan en el design de `C-11`).
- **Governance:** CRÍTICO (turno + auditoría). El apply avanza por checkpoints con revisión humana.
- **Dependencias:** `C-06`, `C-08`, `C-09`, `C-10` (en `main`). Habilita `C-12`, `C-13`, `C-14`, `C-15` y `C-16`.
