# Design — C-17 seed-y-flujo-e2e

> Governance BAJO: este design es corto a propósito. Fija las decisiones técnicas que el apply necesita para no improvisar; el "por qué" del change está en `proposal.md` y el contrato de comportamiento en los deltas de `specs/`.

## Context

Ver `proposal.md` §Why. Restricciones que condicionan el approach:

- `sembrar_admin_demo(conexion, password_hash)` recibe el hash ya calculado porque `app/db` **no puede importar `app/api/seguridad`** (regla dura 1). Los hashes se calculan en el `lifespan`.
- `app/db/esquema.sql` **no se toca**: no hay migraciones ni se puede agregar un `UNIQUE` a una tabla existente sin rehacerla.
- `profesional` no tiene restricción única sobre `(nombre, apellido, matricula)` y `horario_atencion` no tiene ninguna: `ON CONFLICT` no sirve en esas dos tablas.
- `Config` es un dataclass frozen con un solo campo de seed (`seed_admin_password`), construido por `cargar_config(entorno)` inyectable.
- La suite tiene 759 tests en verde y `tests/api/test_seed.py` afirma hoy que en development se crea **exactamente un** usuario.
- El reloj se inyecta (`RelojFijo`); `INSTANTE_INICIAL = 2026-01-05 12:00 UTC` es lunes 09:00 en `America/Argentina/Buenos_Aires`.
- SQLite es de un solo escritor: `transaccion()` usa `BEGIN IMMEDIATE`.

## Goals / Non-Goals

**Goals**

- Un seed determinista de 32 filas, idempotente, sin duplicar profesionales ni horarios.
- Que el flujo de 6 pasos del roadmap corra contra la app real, no contra mocks.
- Que la trazabilidad RN → test no pueda desactualizarse sin que la suite se ponga roja.

**Non-Goals**

- Turnos de ejemplo en el seed (envejecen contra el reloj).
- Endpoints, códigos de error o cambios de esquema.
- `GET /agenda` y `POST /bloqueos` dentro del E2E.
- El saneamiento documental de `agenda`, `horarios-atencion` y `AccionAuditoria` (PR aparte).

## Decisions

### D-A · Un módulo de seed con una entrada pública y funciones por grupo

`sembrar_demo(conexion, *, password_hash_admin, password_hash_recepcion, password_hash_odontologo) -> DatosDemo` orquesta `_sembrar_profesionales`, `_sembrar_horarios`, `_sembrar_sillones`, `_sembrar_prestaciones`, `_sembrar_pacientes` y `_sembrar_usuarios`, y devuelve un `DatosDemo` frozen con los ids (`profesional_a`, `profesional_b`, `sillon_1`, `sillon_2`, `consulta`, `limpieza`, `tratamiento`, `paciente_1`, `paciente_2`, ids de usuarios).

**Alternativa descartada:** reescribir `sembrar_admin_demo` para que cubra todo. Rompe sus 6 tests de unidad y el escenario "con solo `SEED_ADMIN_PASSWORD` existe un único usuario". Se conserva tal cual y `sembrar_demo` la reutiliza.

Los `password_hash` que llegan en `None` significan "ese usuario no se siembra": así el gate por usuario vive en una sola firma y no en ramas dispersas.

### D-B · Idempotencia por clave natural, en SQL

- `sillon`, `prestacion`, `paciente`, `usuario`: ya tienen `UNIQUE` → `ON CONFLICT(<columna>) DO NOTHING`.
- `profesional` y `horario_atencion`: `INSERT INTO … SELECT … WHERE NOT EXISTS (SELECT 1 FROM … WHERE <clave natural>)`.
- Todo dentro de un único `transaccion()`; si algo falla, no queda medio catálogo.

**Alternativas descartadas:** (a) `SELECT` en Python y decidir ahí — duplica la lógica de la clave natural en dos capas y agrega round-trips; (b) agregar `UNIQUE` al esquema — prohibido por el alcance del change y rompería bases existentes.

Consecuencia aceptada: si alguien renombra a mano un profesional demo, el seed crea otro. El seed no "adopta" filas modificadas manualmente.

### D-C · Gate del seed en el `lifespan`

```python
if config.app_env == "development" and config.seed_admin_password:
    sembrar_demo(
        conexion,
        password_hash_admin=hashear(config.seed_admin_password),
        password_hash_recepcion=_hash_o_none(config.seed_recepcion_password),
        password_hash_odontologo=_hash_o_none(config.seed_odontologo_password),
    )
```

Mismo gate que hoy: fuera de `development` o sin `SEED_ADMIN_PASSWORD`, no se siembra **nada** (ni catálogo). Los hashes se calculan solo para las variables definidas, así que un arranque con una sola contraseña no paga tres Argon2.

### D-D · Tres campos de contraseña en `Config`

`seed_admin_password`, `seed_recepcion_password`, `seed_odontologo_password`, todos con el patrón `valores.get("…") or None`. Sin defaults en el código (regla dura 9).

### D-E · El E2E arranca la app de verdad

`TestClient(create_app(config, reloj=reloj))` con `APP_ENV=development`, las tres contraseñas y una base temporal; el `with` dispara el `lifespan` y por lo tanto el seed. Los ids se leen de la base con `abrir_conexion(config.database_path)`, no de los endpoints de catálogo: el E2E prueba el flujo de turnos, no el CRUD de recursos.

Fecha del turno: el lunes del reloj a las 10:00 (cae en la franja sembrada 09:00-13:00 y es futuro respecto de las 09:00 locales). El test fija `CLINIC_TIMEZONE` en su `Config` para no depender del entorno del runner.

**Alternativa descartada:** llamar `sembrar_demo` a mano y usar `APP_ENV=test`. Es más rápido pero no prueba el arranque, que es justamente lo que el change promete.

### D-F · La trazabilidad es un verificador puro usado por la suite

`tests/trazabilidad.py` expone funciones sin dependencias del proyecto:

- `codigos_de_reglas(texto_kb) -> list[str]`: extrae los `RN-xxx-NN` de la KB 05.
- `filas_de_tabla(texto_tabla) -> dict[str, str]`: mapea código → nodo de test citado.
- `tests_existentes(raiz) -> set[str]`: recorre `tests/**/test_*.py` con `ast` y arma el conjunto de nodos `ruta::funcion`.
- `hallazgos(reglas, filas, existentes) -> list[str]`: devuelve los problemas legibles.

`tests/test_trazabilidad.py` lo aplica al repositorio real (debe dar vacío) y a tres casos sintéticos (regla sin fila, test inexistente, tabla completa) para probar los mensajes.

**Alternativas descartadas:** un script en `app/` (no es código de producción); un `fixture` de `conftest` (no se puede probar aislado ni fallar con un mensaje propio).

### D-G · Formato de la tabla de trazabilidad

`| RN | Regla | Test | Estado |`, con el test como nodo exacto (`tests/api/test_turnos.py::test_…`). El verificador exige nodo exacto: un nombre de archivo suelto no alcanza.

### D-H · README por secciones, no reescritura total

Se conservan instalación, variables, formato de error y estructura (la tabla de errores ya está completa). Se corrigen: el estado (17 changes + conteo real), la frase "todavía no hay rutas protegidas", la sección de usuario demo (3 usuarios), el conteo de `pytest`, y se agregan el flujo E2E de 6 pasos, la dependencia de `CLINIC_TIMEZONE`, la nota de `turnos.db` y el link a `docs/trazabilidad-rn-test.md`.

### D-I · `tests/api/test_seed.py` no se reescribe

Sus 6 tests de unidad de `sembrar_admin_demo` quedan intactos. Solo se ajustan las dos aserciones del `lifespan` que hoy esperan un único usuario (contar filtrando por `username` en vez de desempacar la lista). Los tests nuevos del seed demo van a `tests/api/test_seed_demo.py`.

## Risks / Trade-offs

- **[Tres Argon2 por arranque en development]** → el costo dominante es el hash, no los 32 inserts. Si molesta en la DX, se mide y se decide después; no se cachea nada.
- **[`WHERE NOT EXISTS` no adopta filas editadas a mano]** → documentado en D-B; es el comportamiento correcto para un seed.
- **[El E2E depende de la zona horaria]** → el test fija `CLINIC_TIMEZONE` en su `Config`; nunca hereda el entorno.
- **[El E2E es más lento que un test de API normal]** → un solo arranque con seed por test; los bordes (hueco liberado, 409) van en el mismo archivo y reutilizan la fixture.
- **[La tabla de trazabilidad puede quedar desactualizada]** → el verificador de D-F corre en la suite y falla con el código faltante.
- **[Modificar el requirement existente de `acceso-usuarios`]** → se copia el bloque completo con sus 4 escenarios y se agregan los nuevos; no se renombra el header (evita el riesgo de un `RENAMED` + `MODIFIED` sobre la misma regla).

## Migration Plan

Aditivo, sin migración: `inicializar_esquema()` ya es idempotente y el seed se suma a lo que exista. Una base de development anterior recibe las 32 filas en el siguiente arranque. Rollback: quitar la llamada del `lifespan` y las variables; las filas demo quedan inertes en development.

## Open Questions

Ninguna bloqueante.
