# Proposal

## Why

`C-11`, `C-12` y `C-13` ya dejan el rastro de auditoría de cada turno (quién, qué y cuándo) en `auditoria_turno`, pero **no hay forma de leerlo**: no existe ningún `SELECT` sobre la tabla ni una ruta que lo exponga. Administración no puede responder la pregunta central de `US-014` y del Flujo 7, y `C-17` no puede verificar el historial de punta a punta. La trazabilidad se guarda, pero hoy es inaccesible.

## What Changes

- Nueva ruta `GET /auditoria?turno_id=` exclusiva del rol `administracion` (`403` para recepción y odontólogo, `401` sin token).
- `turno_id` obligatorio: ausente, `0`, negativo o no entero → `422`; turno inexistente → `404 no_encontrado` (no se confunde un id mal tipeado con un turno sin historial).
- La respuesta devuelve los registros en **orden cronológico** (`ocurrio_en ASC`, desempatado por `id ASC`) con `accion`, `usuario_id`, `username`, `ocurrio_en`, `antes` y `despues`.
- `antes` y `despues` se devuelven como **objetos JSON** parseados; `antes` es `null` únicamente en el registro `crear`.
- Se expone `usuario_id` + `username` mediante `LEFT JOIN`; **nunca** `password_hash`, `rol` ni datos del paciente.
- **Sin rutas de escritura:** no hay `POST`, `PUT`, `PATCH` ni `DELETE` de auditoría; sobre `/auditoria` responden `405` y sobre `/auditoria/{id}` responden `404` (RN-AUD-02).
- Repositorio nuevo `app/db/repositorio_auditoria.py` y router nuevo `app/api/auditoria.py`; `repositorio_turnos.py` y `api/turnos.py` no se tocan.
- **Sin cambios de esquema** (`app/db/esquema.sql` queda intacto) y **sin códigos de error nuevos** (no hay delta de `errores-api`).
- **Fuera de alcance:** paginación, filtros por acción o usuario, listado global sin `turno_id` y políticas de retención o purga (IF-06).

## Capabilities

### New Capabilities

- Ninguna. El historial de turnos ya está cubierto por una capability existente.

### Modified Capabilities

- `auditoria-turnos`: se agrega el requirement de consulta del historial por turno (endpoint, orden cronológico, contrato de `antes`/`despues`, identificación del usuario y ausencia de rutas de escritura). Los cinco requirements existentes del lado escritura no cambian.

## Impact

- **Código nuevo:** `app/api/auditoria.py`, `app/db/repositorio_auditoria.py`, `tests/api/test_repositorio_auditoria.py` y `tests/api/test_auditoria.py`.
- **Código modificado (aditivo):** `app/main.py` (una línea de `include_router`).
- **Sin cambios:** `app/db/esquema.sql`, `app/db/repositorio_turnos.py`, `app/api/turnos.py`, `app/api/errores.py` y `app/domain/`.
- **API:** un endpoint nuevo (`GET /auditoria`); ningún endpoint existente cambia de contrato.
- **Datos:** sin migración; se leen los registros que ya escriben `C-11`, `C-12` y `C-13`.
- **Dependencias:** `C-12` y `C-13` deben estar integrados en la rama de implementación para poder probar los registros `cancelar` y `reprogramar`, aunque el código de C-15 compila sin ellos.
- **Base de tests:** la suite actual de `main` tiene 650 tests verdes; el change debe cerrar sin regresiones.
