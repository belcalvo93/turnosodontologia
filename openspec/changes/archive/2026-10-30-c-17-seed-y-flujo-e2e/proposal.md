# Proposal — C-17 seed-y-flujo-e2e

## Why

El MVP está funcional pero **no es demostrable**: la base arranca vacía, no existen usuarios de recepción ni de odontología, ningún test recorre el flujo que el trabajo práctico promete (login → turno → reprogramar → cancelar → auditoría) y no hay un artefacto que demuestre que cada regla de negocio tiene test. De las 31 reglas de KB 05, dos quedaron flojas: `RN-PAC-03` no tiene guardia automática y `RN-REC-03` solo prueba el rechazo, no la conservación del histórico.

Es el último change del roadmap: cerrarlo deja el repositorio listo para la entrega, con datos de demo reproducibles, una prueba de punta a punta y la trazabilidad verificada por la suite.

## What Changes

- **Seed demo completo** en `app/db/seed.py`: 2 profesionales, 2 sillones, 3 prestaciones, 20 horarios (lunes a viernes, 09:00-13:00 y 14:00-18:00, para ambos profesionales), 2 pacientes y 3 usuarios demo (`admin_demo`, `recepcion_demo`, `odontologo_demo` ligado al profesional A). Total: **32 filas**, todas ficticias.
- **Idempotencia real**: `profesional` y `horario_atencion` no tienen `UNIQUE`, así que el seed usa `INSERT … SELECT … WHERE NOT EXISTS` por clave natural. Un segundo arranque deja exactamente las mismas 32 filas y los mismos hashes.
- **Contraseñas solo desde el entorno**: `SEED_ADMIN_PASSWORD` (existente), `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD`. El seed sigue corriendo solo en `development` y solo con `SEED_ADMIN_PASSWORD` definida; cada usuario se crea solo si su propia contraseña está definida.
- **Test E2E del flujo de 6 pasos**: login de recepción → alta de turno → reprogramación → cancelación → login de administración → consulta de auditoría con los 3 registros en orden.
- **Dos tests que cierran los huecos**: `RN-PAC-03` (DNI de los pacientes demo terminados en `"(ficticio)"`) y `RN-REC-03` (un turno sigue consultable después de desactivar su recurso).
- **Trazabilidad verificada**: `docs/trazabilidad-rn-test.md` con las 31 reglas mapeadas a su test, y un test que falla si una regla de KB 05 no está en la tabla o si el test citado no existe.
- **README al día** y `.env.example` con las variables nuevas: estado real de los 17 changes, conteo real de la suite, flujo E2E de ejemplo, dependencia de `CLINIC_TIMEZONE`, y que **no hace falta borrar `turnos.db`** para recibir los datos demo.

**No cambia**: el esquema (`app/db/esquema.sql`), ningún endpoint, ningún código de error, ninguna regla de negocio del dominio. El seed de `admin_demo` conserva su comportamiento y sus tests de unidad.

**Fuera de alcance** (trabajo posterior, PR de saneamiento separado): renombrar los encabezados del spec `agenda` para que pase `openspec validate --specs --strict`, acortar el requirement largo de `horarios-atencion` y deduplicar `AccionAuditoria` entre `app/domain/models.py` y `app/db/repositorio_turnos.py`.

## Capabilities

### New Capabilities

Ninguna: no hay comportamiento de negocio nuevo. El seed de demo es infraestructura de desarrollo de una capability existente y el flujo E2E solo ejercita comportamiento ya especificado en `turnos`, `cancelar-turno`, `reprogramar-turno` y `auditoria-turnos`.

### Modified Capabilities

- `acceso-usuarios`: el seed de desarrollo deja de crear solo `admin_demo` y pasa a sembrar el catálogo y los tres usuarios demo bajo el mismo gate; se agregan requirements para el catálogo, las contraseñas desde el entorno y los datos ficticios (`RN-PAC-03`).
- `base-tecnica`: se agrega el requirement de trazabilidad de reglas de negocio a tests, verificada automáticamente por la suite.

## Impact

**Código afectado**

- `app/db/seed.py`: nuevas funciones y entrada pública `sembrar_demo(...)` con los ids sembrados.
- `app/config.py`: dos variables de contraseña demo más.
- `app/main.py`: el `lifespan` calcula los tres hashes y llama al seed nuevo (solo `development` + `SEED_ADMIN_PASSWORD`).
- `app/db/esquema.sql`: **sin cambios**.
- `app/api/*`: **sin cambios** (los 6 pasos del E2E usan endpoints que ya existen).

**Tests**

- Nuevos: `tests/api/test_seed_demo.py`, `tests/api/test_flujo_e2e.py`, `tests/test_trazabilidad.py`.
- Modificados: `tests/api/test_seed.py` (dos aserciones que hoy esperan un solo usuario) y `tests/api/test_turnos.py` (dos casos de `RN-REC-03`).
- Línea de base: **759 tests en verde**. Ningún test existente debería cambiar de resultado salvo las dos aserciones mencionadas.

**Documentación y configuración**

- Nuevo: `docs/trazabilidad-rn-test.md`.
- Modificados: `README.md` y `.env.example`.
- `knowledge-base/`, `CHANGES.md` y `docs/discovery/`: **no se tocan**.

**Riesgos de compatibilidad**

- Una base de desarrollo existente recibe las 32 filas nuevas al arrancar, sin migración ni borrado.
- Si alguien definió solo `SEED_ADMIN_PASSWORD`, el comportamiento visible sigue siendo el de hoy: `admin_demo` y el catálogo, sin los otros dos usuarios.
