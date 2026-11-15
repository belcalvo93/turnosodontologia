# Proposal — C-19 ajustes-revision-escenarios

## Why

La revisión con la skill `revisor-escenarios-sdd` del change archivado `openspec/changes/archive/2026-10-30-c-17-seed-y-flujo-e2e/`, verificada hallazgo por hallazgo contra el código y los tests reales, dejó seis desajustes entre los specs canónicos y lo que la suite prueba: una regla del verificador de trazabilidad sin test que la fuerce a fallar, un caso del gate por usuario del seed sin escenario ni test, dos escenarios que no coinciden con el comportamiento real (matrículas y rotulado de nombres), un escenario sin fecha anclada al reloj y un requirement de `turnos` con cobertura incompleta para el profesional.

Ninguno es un bug de la aplicación: son huecos de especificación y de tests. Corregirlos ahora evita que el próximo change herede escenarios ambiguos o que una regresión en el verificador o en el seed pase sin que la suite se ponga roja.

## What Changes

Exactamente estos seis puntos, nada más:

1. **(H4) Trazabilidad — RN-TUR-13**: nuevo escenario en `base-tecnica` donde la verificación **falla** si `RN-TUR-13` no cita el mismo test que `RN-TUR-04`, con un mensaje que nombra `RN-TUR-13`. Nuevo test sintético en `tests/test_trazabilidad.py` que fuerza ese fallo (hoy solo hay aserciones del camino feliz).
2. **(H9) Seed — una sola contraseña de rol**: nuevos escenarios en `acceso-usuarios` para definir **solo** `SEED_ODONTOLOGO_PASSWORD` o **solo** `SEED_RECEPCION_PASSWORD` (con `SEED_ADMIN_PASSWORD` definida): se crea únicamente el usuario cuya contraseña está definida. Nuevos tests en `tests/api/test_seed_demo.py`.
3. **(H5) Matrículas**: el requirement "Catálogo demo de desarrollo" dice que **uno** de los profesionales tiene matrícula ficticia; el seed y sus tests muestran que lo son **ambos** (`"0001 (ficticia)"` y `"0002 (ficticia)"`). Se alinea el spec: ambos.
4. **(H7) Turno sobre el catálogo demo**: el escenario "Los recursos sembrados aceptan turnos" se ancla a una fecha futura respecto del reloj inyectado (el lunes del reloj, a las 10:00, cuando el reloj marca las 09:00 locales).
5. **(H8) Rotulado de nombres**: el escenario "Los nombres demo están rotulados" aclara que alcanza con que el conjunto nombre + apellido contenga "ficticio" o "ficticia", sin distinguir mayúsculas.
6. **(H10) Recurso desactivado**: en `turnos`, el escenario del profesional desactivado verifica también `estado` `reservado`, y se agrega un escenario de auditoría para la desactivación del profesional. Nuevo test solo para la auditoría del profesional (el `estado` ya lo verifica el test existente; ver `design.md` D-F).

**No cambia**: ningún archivo de `app/` ni `frontend/`, ningún endpoint, código de error, esquema ni regla de negocio. El comportamiento del sistema es el mismo: el change corrige specs y agrega tests de caracterización.

**Fuera de alcance**: el change archivado `c-17` (no se modifica), `knowledge-base/`, `docs/trazabilidad-rn-test.md` (los tests nuevos no cambian qué test cita cada regla) y cualquier spec canónico distinto de los tres que tocan los deltas.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `base-tecnica`: el requirement "Trazabilidad de reglas de negocio a tests" suma el escenario de fallo por `RN-TUR-13`.
- `acceso-usuarios`: "Catálogo demo de desarrollo" (ambas matrículas ficticias y turno anclado al reloj), "Usuarios demo de recepción y odontología" (escenarios con una sola contraseña de rol) y "Datos ficticios del seed" (rotulado sobre nombre + apellido).
- `turnos`: "Conservación del turno histórico al desactivar un recurso" (estado del turno con profesional desactivado y auditoría al desactivar el profesional).

## Impact

**Código de la aplicación**: ninguno. `app/`, `frontend/` y `app/db/esquema.sql` no se tocan.

**Tests**

- `tests/test_trazabilidad.py`: +1 test sintético (RN-TUR-13 con test distinto de RN-TUR-04).
- `tests/api/test_seed_demo.py`: +4 tests (unidad sobre `sembrar_demo` y arranque, uno por cada contraseña de rol suelta).
- `tests/api/test_turnos.py`: +1 test (auditoría al desactivar el profesional).
- Son tests de caracterización: el comportamiento ya existe, así que el rojo se demuestra con una mutación temporal y revertida (ver `design.md` D-A).

**Specs**: tres deltas (`base-tecnica`, `acceso-usuarios`, `turnos`); los specs canónicos cambian solo al archivar.

**Documentación**: `knowledge-base/`, `CHANGES.md`, `docs/discovery/` y el change archivado `c-17` no se tocan durante el apply. La fila de C-19 en `CHANGES.md` se agrega recién al cierre (autorizado por el equipo).
