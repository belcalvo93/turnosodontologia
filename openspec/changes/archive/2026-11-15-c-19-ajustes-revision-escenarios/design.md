# Design — C-19 ajustes-revision-escenarios

> Governance BAJO/MEDIO: specs y tests, sin código de la aplicación. Este design fija cómo se hacen los tests de caracterización y deja registrado qué se verificó en el código antes de proponer cada punto. El "por qué" está en `proposal.md`; el contrato, en los deltas de `specs/`.

## Context

Ver `proposal.md` §Why. Estado relevado en el repositorio (rama `c-19-ajustes-revision-escenarios`):

- **Verificador de trazabilidad**: `tests/trazabilidad.py:124-128` ya agrega el hallazgo `"RN-TUR-13 debe citar exactamente el mismo test que RN-TUR-04."` cuando ambas filas existen y citan tests distintos. `tests/test_trazabilidad.py` tiene 5 tests; la igualdad RN-TUR-13/RN-TUR-04 solo aparece en caminos felices (`:25` sobre el repositorio real y `:106-107` en la tabla sintética completa). Ningún test fuerza ese hallazgo.
- **Gate por usuario del seed**: `app/db/seed.py:243-281` (`_sembrar_usuarios`) crea `recepcion_demo` y `odontologo_demo` solo si su hash llega distinto de `None`, y `app/main.py:55-60` pasa `_hash_o_none(...)` por variable. El comportamiento por usuario ya existe. En `tests/api/test_seed_demo.py` solo se prueban las combinaciones (todas definidas) y (ninguna de rol): `test_sembrar_demo_no_crea_usuarios_sin_su_contrasena` (`:157-173`, unidad con `(None, None)`) y `test_arranque_solo_con_seed_admin_password_...` (`:316-349`, arranque).
- **Matrículas**: el seed escribe `"0001 (ficticia)"` y `"0002 (ficticia)"`; `tests/api/test_seed_demo.py:47-64` lo verifica para ambos y `verify.md` de c-17 (`:62`) lo documenta. El spec canónico (`openspec/specs/acceso-usuarios/spec.md:212` y `:220`) dice "uno".
- **Turno sobre el catálogo demo**: el escenario canónico (`acceso-usuarios/spec.md:223-227`) dice "un día hábil con horario sembrado, a las 10:00" sin fecha. El test que lo cubre es el paso 2 de `tests/api/test_flujo_e2e.py` (`:104-127`), que usa `RelojFijo` en `2026-01-05 12:00 UTC` = lunes 09:00 en Buenos Aires, reserva ese lunes a las 10:00 y fija `CLINIC_TIMEZONE` (decisión D-E de c-17). RN-TUR-09 (`knowledge-base/05_reglas_de_negocio.md:55`) exige turnos futuros para cancelar o reprogramar, que son los pasos siguientes del flujo.
- **Rotulado de nombres**: el escenario canónico (`acceso-usuarios/spec.md:298-302`) dice "cada nombre o apellido contiene…", lo que admite la lectura "cada campo por separado". El test (`tests/api/test_seed_demo.py:208-216`) concatena `f"{nombre} {apellido}".lower()`, y los datos reales lo necesitan: `nombre` "Paciente" / "Odontólogo" no contiene la palabra, solo el apellido.
- **Recurso desactivado** (`turnos/spec.md:228-251`): ver D-F.

## Goals / Non-Goals

**Goals**

- Que cada escenario modificado o nuevo tenga un test que lo ejercite y que ese test sea capaz de ponerse rojo.
- Que los specs canónicos describan el comportamiento real, sin cambiarlo.

**Non-Goals**

- Cambiar código de `app/` o `frontend/` (si un test nuevo fallara por un bug real, se para y se reporta: ver Risks).
- Tocar `docs/trazabilidad-rn-test.md`: ninguna regla cambia de test citado.
- Modificar el change archivado c-17 o `knowledge-base/`.

## Decisions

### D-A · Tests de caracterización con rojo demostrado por mutación temporal

Los seis puntos describen comportamiento que **ya existe**, así que los tests nuevos van a pasar en cuanto se escriban. Para cumplir Strict TDD (ver un test fallar antes de darlo por bueno) cada test nuevo se valida así:

1. Escribir el test y correrlo: pasa (se documenta "caracterización").
2. Introducir una **mutación temporal** mínima en el código bajo prueba que rompa exactamente el comportamiento descrito (lista concreta en `tasks.md`), correr el test y verificar que **falla por la aserción esperada**.
3. Revertir la mutación (`git checkout -- <archivo>`) y verificar que el test vuelve a pasar y que `git diff --stat` no muestra el archivo mutado.

**Alternativa descartada:** dar por buenos los tests porque pasan. Un test que nunca se vio en rojo puede ser una tautología; justamente el hallazgo H4 es que el chequeo de RN-TUR-13 no tenía un test que lo forzara a fallar.

La mutación nunca se commitea y la verificación final (`git diff --stat`) confirma que `app/` y `tests/trazabilidad.py` quedan intactos.

### D-B · RN-TUR-13: tabla sintética con dos tests existentes y distintos (H4)

El test nuevo arma una KB sintética con `RN-TUR-04` y `RN-TUR-13`, una tabla donde cada una cita un nodo distinto, y pasa **ambos nodos** en `existentes`. Así el único hallazgo posible es el de RN-TUR-13 y el test puede afirmar `len(problemas) == 1` y `"RN-TUR-13" in problemas[0]`.

**Alternativa descartada:** citar un test inexistente para RN-TUR-13. Mezclaría dos hallazgos y el test no distinguiría cuál chequeo disparó.

### D-C · Seed con una sola contraseña de rol: unidad y arranque (H9)

Por cada combinación (solo odontología, solo recepción) se agregan dos tests en `tests/api/test_seed_demo.py`:

- **Unidad** sobre `sembrar_demo` con el hash del otro rol en `None`: verifica los usernames creados, los campos del usuario creado (rol, `profesional_id`, `activo`, hash) y que el id del ausente en `DatosDemo` sea `None`.
- **Arranque** con `create_app` y la fixture/helpers existentes (`_config_arranque_demo`, `_conteos_por_tabla`): verifica usernames, catálogo sembrado y `POST /auth/login` `200` con el usuario creado, que es lo que pide el escenario.

Se pueden parametrizar por rol si queda más legible; la decisión de estilo queda al apply, siempre que cada escenario tenga al menos un test de arranque nombrado por él.

### D-D · Puntos solo de spec: H5, H7 y H8

- **H5** y **H8**: los tests existentes ya verifican lo que el spec corregido dice (`test_seed_demo.py:61-64` y `:208-216`). No se agregan tests; la tarea es verificar que esos tests siguen siendo los que citan los escenarios.
- **H7**: el paso 2 de `test_flujo_e2e.py` ya reserva el lunes del reloj a las 10:00 con el reloj en las 09:00 locales y `CLINIC_TIMEZONE` fija. El escenario corregido cita RN-TUR-09 para explicar por qué la fecha tiene que ser futura. No se agrega test.

### D-E · Matrícula: se corrige el spec, no el seed (H5)

El comportamiento real (ambas ficticias) es el más seguro respecto de RN-PAC-03 y ya está en tests y en `verify.md` de c-17. Cambiar el seed para que solo uno sea ficticio iría contra la regla.

### D-F · RN-REC-03 con profesional: hallazgo verificado (H10)

Revisado en `tests/api/test_turnos.py`:

- `test_profesional_desactivado_despues_de_la_reserva_conserva_el_turno_y_rechaza_nuevos_422` (`:677-705`) **ya verifica** `consulta.json()["estado"] == "reservado"` (`:695`), además de `consulta.json() == creado` (`:693`). El escenario "Profesional desactivado después de la reserva" se corrige **solo en el spec**; no hace falta test nuevo.
- `test_desactivar_el_sillon_no_borra_ni_modifica_la_auditoria_del_turno` (`:708-730`) desactiva **solo el sillón**. **Ningún test** cubre la auditoría al desactivar el profesional. Se agrega el escenario "La desactivación del profesional no borra auditoría" y un test nuevo con el mismo patrón (`_auditorias(ctx)` antes y después, y `GET /auditoria?turno_id=…` con un único registro `crear`).

Se agrega un escenario nuevo en lugar de ampliar "La desactivación no borra auditoría" para que cada escenario tenga un único test que lo cubra y el existente no cambie de significado.

### D-G · Deltas MODIFIED con el bloque completo

Los cinco requirements tocados se copian enteros en `## MODIFIED Requirements`, con todos sus escenarios, sin renombrar el header (mismo criterio que c-17). Los escenarios nuevos se agregan al final de cada bloque.

## Risks / Trade-offs

- **[Un test de caracterización falla sin mutación]** → sería un bug real del sistema y queda fuera del alcance (no se toca `app/`). Se para el apply y se reporta al equipo con el test y la salida.
- **[Olvidar revertir una mutación]** → cada tarea termina con `git diff --stat` del archivo mutado vacío, y la verificación final lo repite para `app/` y `tests/trazabilidad.py`.
- **[Los tests de arranque suman tiempo (Argon2 por usuario)]** → son dos arranques más, del mismo orden que los existentes; aceptable.
- **[El delta de `acceso-usuarios` reescribe tres requirements]** → se copia el bloque literal del canónico y se cambian solo las líneas citadas; `openspec validate --strict` del change lo controla.

## Migration Plan

No aplica: sin cambios de código, esquema ni datos. Los specs canónicos se actualizan al archivar con `/opsx:archive`. Rollback: descartar el change.
