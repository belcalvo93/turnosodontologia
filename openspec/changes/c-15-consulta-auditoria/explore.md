# Explore — C-15 consulta-auditoria

Relevamiento previo al propose. **No implementa nada**: fija el estado actual, la brecha, los riesgos y las decisiones ya cerradas por el equipo.

> Contexto verificado: `C-07` está archivado y mergeado (PR #36); el working tree de `main` está limpio y la suite es de **650 tests en verde**.

## 1. Alcance declarado en el roadmap

`CHANGES.md` (sección `[C-15] consulta-auditoria`, línea 404) define:

- `GET /auditoria?turno_id=` **solo administración**: registros en orden cronológico con usuario, acción, antes/después y fecha y hora.
- Sin rutas `PUT`/`PATCH`/`DELETE` de auditoría (RN-AUD-02).
- Tests: crear + reprogramar + cancelar deja exactamente 3 registros en orden (RN-AUD-01), `PATCH`/`DELETE` → 405/404, recepción → 403.
- Dependencias: `C-12`, `C-13`.
- Governance: **ALTO**.

Posición real en el grafo (líneas 117-119 y 93): C-15 está en la **onda 7**, en paralelo con C-16, y es uno de los cuatro gates que habilitan C-17:

```
C-11 crear-turno        (en main, [x])  ──┐
C-12 cancelar-turno     (rama Bruno)    ──┼──> C-15 consulta-auditoria ──> C-17 cierre MVP
C-13 reprogramar-turno  (rama Joaquín)  ──┘         (onda 7, ALTO)
```

**Dependencias reales ≠ dependencias del roadmap.** C-15 no depende de C-12/C-13 para *leer* la tabla: depende de ellas para que los registros `cancelar` y `reprogramar` **existan y tengan el formato que C-15 va a devolver**. Hoy C-11 es lo único en `main` que escribe auditoría.

## 2. Qué existe hoy

| Pieza | Estado | Evidencia |
|---|---|---|
| Tabla `auditoria_turno` (`turno_id FK`, `accion CHECK IN ('crear','cancelar','reprogramar')`, `usuario_id FK`, `ocurrio_en TEXT`, `antes NULL`, `despues NOT NULL`) | **Existe** | `app/db/esquema.sql:111-119` |
| Triggers append-only `auditoria_turno_sin_update` / `_sin_delete` | **Existen** | `app/db/esquema.sql:121-131` |
| `registrar_auditoria(...)` — solo `INSERT` | **Existe** | `app/db/repositorio_turnos.py:89-106` |
| `snapshot_turno(turno)` — JSON canónico de **8 claves** | **Existe** | `app/db/repositorio_turnos.py:69-86` |
| `crear_turno(...)` — inserta turno + auditoría `crear` con `antes=None`, `despues=snapshot`, `ocurrio_en == creado_en` | **Existe** | `app/db/repositorio_turnos.py:109-147` |
| `cancelar_turno(...)` — `UPDATE estado` + `registrar_auditoria("cancelar", antes=snapshot(antes), despues=snapshot(despues))` | **Existe en rama, no en `main`** | `origin/bruno-c12-cancelar-turno:app/db/repositorio_turnos.py` |
| `reprogramar_turno(...)` — `UPDATE inicio/fin/profesional_id/sillon_id` + `registrar_auditoria("reprogramar", antes=snapshot(anterior), despues=snapshot(nuevo))` | **Existe en rama, no en `main`** | `origin/joaquin-c13-reprogramar-turno:app/db/repositorio_turnos.py` |
| `usuario_actual` (401) y `requiere_rol(...)` (403 `sin_permiso`) | **Existen** | `app/api/auth.py:66-99` |
| Mapeo global de errores HTTP (404/405 incluidos) a `{codigo, mensaje}` | **Existe** | `app/api/errores.py` |
| Patrón de router + Pydantic + `obtener_conexion` | **Existe** | `app/api/turnos.py` |
| **Función de lectura de `auditoria_turno`** | **No existe** | ningún `SELECT` sobre la tabla en `app/` |
| **`app/db/repositorio_auditoria.py`** | **No existe** | — |
| **Router `/auditoria`** | **No existe** | `app/main.py` monta 11 routers, ninguno de auditoría |
| **Modelo Pydantic de respuesta de auditoría** | **No existe** | — |
| **Spec `auditoria` en `openspec/specs/`** | **No existe** | specs actuales: acceso-usuarios, base-tecnica, errores-api, pacientes, prestaciones, profesionales, reglas-alta-turno, sillones, usuarios |
| Fixtures `cliente`, `crear_usuario`, `token_de`, `reloj` | **Existen** | `tests/conftest.py` |
| Baseline de la suite | **650 tests verdes** | `pytest --collect-only -q` |

**Conclusión:** la mitad de escritura ya está hecha y es consistente; la mitad de lectura no existe en absoluto. C-15 es un change **aditivo de solo lectura**: un repositorio, un router, un spec y tests. No crea entidades, no agrega códigos de error y **no toca `app/db/esquema.sql`**.

## 3. Consistencia de formatos: la verificación pedida

Revisé los tres productores de auditoría y **hoy son consistentes**. Los tres usan `snapshot_turno()` con exactamente las mismas 8 claves, en el mismo orden, con `isoformat(timespec="seconds")`:

```json
{"id":1,"paciente_id":1,"profesional_id":1,"sillon_id":1,
 "prestacion_id":1,"inicio":"2026-11-10T09:00:00","fin":"2026-11-10T09:30:00",
 "estado":"reservado"}
```

| Acción | `antes` | `despues` | `ocurrio_en` |
|---|---|---|---|
| `crear` (C-11) | `NULL` | snapshot del turno recién creado (`estado: "reservado"`) | `== creado_en` del turno |
| `cancelar` (C-12) | snapshot con `estado: "reservado"` | snapshot con `estado: "cancelado"` | reloj inyectado del request |
| `reprogramar` (C-13) | snapshot anterior (mismo `id`, mismo `estado`) | snapshot nuevo (mismo `id` y `estado`, `inicio`/`fin`/`profesional_id`/`sillon_id` cambiados) | reloj inyectado del request |

Detalle importante: **`antes` es el único campo anulable**, y solo en `crear`. Cualquier contrato de respuesta tiene que representar `antes: null` para el alta sin romper el tipo.

Dos observaciones que sí importan para C-15:

1. **`ocurrio_en` tiene precisión de segundos.** Crear, reprogramar y cancelar en el mismo request de test pueden caer en el mismo segundo → el orden cronológico **necesita desempate por `id`** (`ORDER BY ocurrio_en ASC, id ASC`). Sin eso, el escenario "3 registros en orden" es flaky.
2. **`snapshot_turno` no copia datos personales**: solo ids y fechas. No incluye DNI, nombre ni `creado_por`/`creado_en`. Eso ya resuelve buena parte de "no exponer datos sensibles", pero **no** resuelve qué se hace con el usuario que operó.

## 4. Qué falta, capa por capa

### 4.1 Esquema

**No se toca `app/db/esquema.sql`.** La tabla `auditoria_turno` y sus triggers ya cubren todo lo que C-15 necesita: no hay columnas nuevas, no hay migración y no hay índices que agregar en este change. La consulta por `turno_id` se resuelve con un `SELECT` ordenado sobre la tabla existente.

El índice sobre `auditoria_turno(turno_id, ocurrio_en, id)` queda registrado como **posible mejora futura** en las preguntas abiertas (§7), no como parte del alcance de C-15.

### 4.2 Dominio

**Nada de lógica de negocio.** Leer auditoría no valida reglas: es una consulta ordenada. Lo único que conviene tipar es la forma del registro (`id`, `turno_id`, `accion`, `usuario_id`, `ocurrio_en`, `antes`, `despues`) y la acción, que ya existe como `AccionAuditoria` en `app/db/repositorio_turnos.py`. Opciones: mover/reutilizar ese alias o declarar un `RegistroAuditoria` en `app/domain/models.py`. No hay RN nueva que codificar.

### 4.3 Repositorio

**Archivo nuevo `app/db/repositorio_auditoria.py`** (SQL parametrizado, regla dura 4):

- `listar_auditoria_por_turno(conexion, turno_id: int) -> list[RegistroAuditoria]` con `ORDER BY ocurrio_en ASC, id ASC`.
- `LEFT JOIN usuario` para exponer `username`; nunca se selecciona `password_hash`, `rol` ni `profesional_id` del usuario, ni datos del paciente.
- `json.loads()` de `antes`/`despues` en la capa de lectura (o en el router) para devolver objetos, no strings.

No hace falta `transaccion()`: es un `SELECT` único sobre una conexión en autocommit. `app/db/repositorio_turnos.py` **no se toca** (así se evita el conflicto con C-12/C-13).

### 4.4 Router

**Archivo nuevo `app/api/auditoria.py`**, montado en `app/main.py`:

| Ruta | Status | Roles |
|---|---|---|
| `GET /auditoria?turno_id=` | 200 / 401 / 403 / 404 / 422 | solo administración |

- `requiere_rol(Rol.ADMINISTRACION)` como dependencia → el **401/403 se resuelve antes** de tocar la base, así que un rol sin permiso no puede inferir si el turno existe. Eso es gratis y hay que conservarlo.
- `turno_id: Annotated[int, Query(ge=1)]` → ausente o `<= 0` da `422` por el mapeo global.
- Sin `POST`/`PUT`/`PATCH`/`DELETE`.

### 4.5 Spec

**Capability nueva `auditoria`** en `openspec/specs/auditoria/spec.md`, con referencia cruzada a `cancelar-turno` y `reprogramar-turno`. **No hay delta de `errores-api`**: no se agrega ningún código nuevo.

## 5. El problema de diseño central: el contrato de la respuesta

Todo lo demás es mecánico; lo que hay que decidir de verdad es **qué devuelve exactamente cada registro**, porque C-15 congela el formato que C-12 y C-13 ya producen y que C-17 va a consumir.

Tres preguntas encadenadas:

1. **`antes`/`despues`: string JSON o objeto JSON?** La tabla los guarda como `TEXT`. Si se devuelven como string, el cliente recibe un JSON-dentro-de-un-string (doble escapado). Si se parsean, el contrato queda limpio pero el servidor tiene que tolerar un `TEXT` corrupto (no debería pasar: solo lo escribe `snapshot_turno`).
2. **`usuario`: ¿id, username o ambos?** El flujo 7 dice "con usuario" y US-014 dice "quién", que para una persona es el `username`, no un entero. Pero el escenario a cubrir es "no expone datos sensibles".
3. **`turno_id` inexistente: ¿404 o lista vacía?** Es la diferencia entre "no sé de qué turno hablás" y "ese turno no tiene auditoría".

Estas tres preguntas ya quedaron resueltas por el equipo (§6); se conservan acá porque son el núcleo del design.

## 6. Decisiones cerradas

| # | Decisión |
|---|---|
| D-01 | **`turno_id` es obligatorio.** Ausente, `0`, negativo o no entero → `422 dato_invalido` (vía `Query(ge=1)` y el mapeo global). No hay listado global de auditoría. |
| D-02 | **`turno_id` inexistente → `404 no_encontrado`.** Se verifica con `obtener_turno()` antes de listar: un id mal tipeado no se confunde con un turno sin historial. |
| D-03 | **`antes` y `despues` se devuelven como objetos JSON** (parseados), no como strings. `antes: null` **solo** en el registro `crear`; `despues` siempre es objeto. |
| D-04 | **Orden `ocurrio_en ASC, id ASC`.** El desempate por `id` es obligatorio porque `ocurrio_en` tiene precisión de segundos y los tests pueden generar varios registros en el mismo segundo. |
| D-05 | **Se expone `usuario_id` + `username`** mediante `LEFT JOIN usuario`. **Nunca** `password_hash`, `rol` ni `profesional_id` del usuario, y **nunca** datos del paciente (nombre, DNI, etc.). |
| D-06 | **Sin códigos de error nuevos.** Se reutilizan `NoAutenticado` (401), `SinPermiso` (403), `NoEncontrado` (404) y el `422` de Pydantic. Sin delta de `errores-api`. |
| D-07 | **No hay rutas de escritura.** Sobre `/auditoria`, `POST/PUT/PATCH/DELETE` responden **405**; sobre `/auditoria/{id}` responden **404** por ruta inexistente. Ambos ya salen con el JSON de RN-GLO-01. |
| D-08 | **Sin cambios de esquema.** No se toca `app/db/esquema.sql`: ni columnas, ni triggers, ni índices. |
| D-09 | **Sin paginación** en el MVP: un turno tiene un puñado de registros y la respuesta es la lista completa ordenada. |
| D-10 | **Sin `transaccion()`.** Es un `SELECT` único sobre una conexión en autocommit. |
| D-11 | **`ocurrio_en` se serializa** como string `YYYY-MM-DDTHH:MM:SS` (hora local naive), igual que `TurnoResponse`. No se inventa zona horaria. |
| D-12 | **Todo en archivos nuevos.** De los existentes solo se toca `app/main.py` (una línea de `include_router`). `repositorio_turnos.py` y `api/turnos.py` no se modifican, para minimizar el conflicto con C-12/C-13. |

## 7. Preguntas abiertas para el equipo

- **IF-06 (prioridad Alta en la KB):** alcance, retención y quién lee. El MVP ya decidió "solo turnos" y "solo administración"; queda explícito que **no hay purga ni retención definida**. ¿La cátedra espera alguna política?
- **Índice sobre `auditoria_turno(turno_id, ocurrio_en, id)`:** fuera de scope de C-15 por decisión del equipo. Queda como **posible mejora futura** si el volumen de auditoría crece; agregarlo más adelante es aditivo porque `inicializar_esquema()` reaplica el script idempotente en cada arranque.
- **`username` histórico:** C-07 hace el `username` inmutable, así que el `LEFT JOIN` devuelve siempre el mismo nombre que operó. Si en el futuro se permitiera renombrar usuarios, habría que decidir si la auditoría guarda el nombre del momento o resuelve el actual. Hoy no aplica.
- **Usuario desactivado:** un usuario dado de baja lógica sigue apareciendo en la auditoría (el `LEFT JOIN` no lo filtra). Es lo correcto para trazabilidad; se documenta para que no se "optimice" filtrando por `activo`.
- **SE-13** ya está resuelta por C-11/C-12/C-13 (misma transacción); C-15 no la reabre.

## 8. Riesgos del change

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **C-12 y C-13 no están en `main`** | C-15 no puede probar los 3 registros contra el código real | Implementar sobre una rama que ya tenga C-12+C-13 mergeados, o esperar el merge antes de `/opsx:apply`. El código de C-15 en sí no depende de ellas para compilar. |
| **Conflicto de merge en `app/main.py`** | Integración | C-15 agrega una sola línea de `include_router`; C-12/C-13 no tocan `main.py`. Conflicto trivial. |
| Conflicto en `app/db/repositorio_turnos.py` / `app/api/turnos.py` | Integración | C-15 **no los modifica**: lectura va en `repositorio_auditoria.py` y `api/auditoria.py`. |
| **Divergencia de formato** entre C-12/C-13 y el snapshot de C-11 | El contrato de respuesta se rompe | Verificado hoy: los tres usan las 8 claves. Blindar con un test que lea la base real después de crear+reprogramar+cancelar y compare las claves. |
| Empate de `ocurrio_en` en el mismo segundo | Test flaky / orden incorrecto | `ORDER BY ocurrio_en ASC, id ASC`. |
| Exponer `password_hash` por un `JOIN` descuidado | Seguridad (RN-ACC-04) | Modelo Pydantic explícito + test `"password_hash" not in respuesta`. |
| `antes`/`despues` con JSON corrupto | 500 | Solo los escribe `snapshot_turno`; si se quiere, `json.loads` con fallo controlado. Riesgo bajo. |
| Expectativa 405 vs 404 mal fijada | Test rojo | Probar **las dos**: `PATCH/DELETE /auditoria` → 405; `PATCH/DELETE /auditoria/1` → 404. |
| Turno con un solo registro (`crear`) devolviendo lista vacía por un filtro mal puesto | Funcional | Escenario explícito: turno recién creado → exactamente 1 registro, `antes: null`. |
| Regresión de los 650 tests | Estabilidad | Suite completa al cerrar; C-15 no toca código existente salvo `main.py`. |
| Governance ALTO sin design propio | Proceso OPSX | `/opsx:propose` debe generar design con las decisiones D-01…D-12 y al menos 3 escenarios por requirement. |

## 9. Escenarios candidatos para el delta de spec

- **Historial completo (RN-AUD-01):**
  - Dado un turno creado, luego reprogramado y luego cancelado por el mismo admin,
  - cuando consulta `GET /auditoria?turno_id={id}`,
  - entonces responde `200` con exactamente 3 registros en orden `crear` → `reprogramar` → `cancelar`, cada uno con `usuario_id`, `username`, `ocurrio_en`, `antes` y `despues`, y `antes: null` solo en el primero.
- **Turno sin más registros que el alta:**
  - dado un turno recién creado, cuando se consulta su auditoría, entonces hay exactamente 1 registro `crear` con `antes: null` y `despues.estado == "reservado"`.
- **Cancelación reflejada:** el registro `cancelar` tiene `antes.estado == "reservado"` y `despues.estado == "cancelado"`.
- **Reprogramación reflejada:** el registro `reprogramar` conserva el mismo `id` de turno en `antes` y `despues`, y el `inicio` de `antes` es distinto del de `despues`.
- **`turno_id` inexistente:** `GET /auditoria?turno_id=999999` → `404 no_encontrado`.
- **`turno_id` inválido:** ausente, `0` o negativo → `422`.
- **Solo lectura (RN-AUD-02):** `PATCH /auditoria` y `DELETE /auditoria` → `405`; `PATCH /auditoria/1` y `DELETE /auditoria/1` → `404`; en ningún caso cambia la cantidad de registros.
- **RBAC:** recepción → `403 sin_permiso`; odontólogo → `403 sin_permiso`; sin token → `401 no_autenticado` (y el 401/403 ocurre antes de revelar si el turno existe).
- **Sin datos sensibles:** la respuesta no contiene `password_hash`, `password`, `rol` del usuario, `dni`, `nombre` ni `apellido`; `antes`/`despues` solo traen las 8 claves del snapshot.
- **Integración C-12/C-13 (RN-AUD-03):** un intento de reprogramación rechazado con `409` no agrega registros; la consulta sigue devolviendo la misma cantidad.

## 10. Próximo paso

C-15 es **el change más chico de la fase**: un repositorio de lectura nuevo, un router nuevo, un spec nuevo, cero códigos de error nuevos, cero entidades nuevas y **cero cambios de esquema**. El único trabajo real es **fijar el contrato de respuesta** (D-01 a D-07) y **blindar con tests la consistencia de formatos** que hoy sostienen C-11, C-12 y C-13.

Sigue `/opsx:propose` para escribir proposal + specs + design + tasks, respetando las decisiones D-01…D-12.
