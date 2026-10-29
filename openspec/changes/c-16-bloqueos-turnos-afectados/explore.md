# Explore — C-16 bloqueos-turnos-afectados

Relevamiento previo al propose (fase Explore de OpenSpec/SDD). **No implementa código**: fija el contexto, el estado actual en `main` y en las ramas paralelas (`origin/bruno-c09-bloqueos`), qué falta de `C-11` (`crear-turno`), la hipótesis de trabajo sobre `SE-09` (listar sin cancelar), las decisiones abiertas con opciones y trade-offs, los riesgos y la recomendación técnica.

---

## 1. Contexto, objetivo y alcance en el roadmap

Según `CHANGES.md` (sección `[C-16] bloqueos-turnos-afectados`, Fase 4):

- **Objetivo funcional (`US-005`, `Flujo 5`):** cuando un usuario con rol `administracion` registra un bloqueo horario (`POST /bloqueos`) sobre un profesional (vacaciones, feriado, licencia) o un sillón (mantenimiento), pueden existir turnos ya reservados que se solapen con el intervalo `[inicio, fin)` de ese recurso. `C-16` resuelve cómo informa o actúa el sistema frente a esos turnos preexistentes.
- **Scope declarado en `CHANGES.md` (bajo la propuesta actual del MVP para `SE-09`):**
  - `POST /bloqueos` devuelve, junto con el bloqueo creado, la lista de turnos activos (`estado = 'reservado'`) que quedan dentro del intervalo `[inicio, fin)` y corresponden al recurso bloqueado (`profesional_id` o `sillon_id`).
  - **No cancela ni modifica** esos turnos: permanecen en estado `reservado` para que recepción los reprograme o cancele manualmente.
  - Si el equipo o la cátedra decidiera otra opción en `SE-09` (rechazar el bloqueo con `409` o cancelar automáticamente en cascada), el scope se reemplaza antes de ejecutar `/opsx:propose`.
  - **Tests mínimos previstos:** bloqueo sin turnos superpuestos → lista vacía (`[]`); bloqueo sobre 2 turnos activos y 1 cancelado → lista con los 2 activos; los turnos afectados conservan `estado = "reservado"`.
- **Dependencias (según `CHANGES.md`):** `C-11` (`crear-turno`), que a su vez depende de `C-06` (`pacientes`), `C-08` (`horarios-atencion`), `C-09` (`bloqueos`) y `C-10` (`reglas-alta-turno`). Con `C-02`, `C-04`, `C-05`, `C-06`, `C-08` y `C-10` ya completados y archivados en `main`, **los únicos bloqueos reales de `C-16` hoy son `C-09`** (implementado en `origin/bruno-c09-bloqueos`, falta mergear y archivar) **y `C-11`** (aún no existe la tabla `turno` ni `POST /turnos` en `main`).
- **Governance:** `MEDIO`.
- **Referencias en `knowledge-base/`:**
  - `10_preguntas_abiertas.md` §`SE-09` (prioridad Alta: *"Turnos ya existentes cuando se crea un bloqueo que los cubre: ¿se cancelan, se listan para reprogramar, se rechaza el bloqueo?"*).
  - `07_flujos_principales.md` §`Flujo 5 — Bloquear un horario`.
  - `06_funcionalidades.md` §`US-005 — Bloquear rango horario de profesional o sillón`.
  - `05_reglas_de_negocio.md` §`RN-REC-02`, §`RN-TUR-04`, §`RN-TUR-05`, §`RN-TUR-08`.
  - `04_modelo_de_datos.md` §`Bloqueo`, §`Turno`, §`AuditoriaTurno`.
  - `03_actores_y_roles.md` §`RBAC` (`administracion` tiene `C L B` sobre bloqueos; `recepcion` y `odontologo` tienen `L`).

---

## 2. Qué existe hoy y qué se relevó en ramas

| Pieza | Estado actual | Evidencia |
|---|---|---|
| `Profesional` y tabla `profesional` (`C-04`) | **En `main` (archivado)** | `app/domain/models.py`, `app/db/repositorio_profesionales.py`, `app/api/profesionales.py`, `openspec/specs/profesionales/spec.md` |
| `Sillon`, `Prestacion` y tablas `sillon`/`prestacion` (`C-05`) | **En `main` (archivado)** | `app/domain/models.py`, `app/db/repositorio_sillones.py`, `app/api/sillones.py`, `openspec/specs/sillones/spec.md` |
| `Intervalo` y `solapan(a, b)` semiabierto `[inicio, fin)` (`C-10`) + `es_futuro` y `TurnoNoModificable` (`C-02`) | **En `main` (archivados)** | `app/domain/intervalos.py` (`solapan`: `a.inicio < b.fin and b.inicio < a.fin`; `es_futuro` con reloj inyectado), `app/domain/errores.py` (`TurnoNoModificable`), `app/api/errores.py` (mapeo `409`→`turno_no_modificable`) |
| `Turno`, `Bloqueo`, `validar_alta` y `_bloqueo_afecta` (`C-10`) | **En `main` (archivado)** | `app/domain/models.py`, `app/domain/reglas_turno.py`, `openspec/specs/reglas-alta-turno/spec.md` |
| Tabla `bloqueo`, `repositorio_bloqueos.py` y `GET/POST/DELETE /bloqueos` (`C-09`) | **En rama `origin/bruno-c09-bloqueos`** (aún no mergeado a `main`) | `app/db/esquema.sql` (`CREATE TABLE IF NOT EXISTS bloqueo` + índice `idx_bloqueo_alcance_recurso_inicio`), `app/db/repositorio_bloqueos.py`, `app/api/bloqueos.py`, `openspec/changes/c-09-bloqueos/` |
| Tabla `turno`, `auditoria_turno`, `repositorio_turnos.py` y `POST /turnos` (`C-11`) | **No existe todavía en `main`** | Pendiente de `C-11 crear-turno` |
| Cancelación de turnos (`C-12`) | **En progreso en `origin/bruno-c12-cancelar-turno` (solo dominio)** | `app/domain/reglas_turno.py` (`validar_cancelacion`), sin tabla ni endpoint aún porque depende de `C-11` |

### 2.1 Lo que deja `C-09` en `origin/bruno-c09-bloqueos` (leído en solo lectura)

- **Esquema (`app/db/esquema.sql`):**
  ```sql
  CREATE TABLE IF NOT EXISTS bloqueo (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      alcance    TEXT    NOT NULL CHECK (alcance IN ('profesional', 'sillon')),
      recurso_id INTEGER NOT NULL,
      inicio     TEXT    NOT NULL,
      fin        TEXT    NOT NULL,
      motivo     TEXT    NOT NULL DEFAULT '',
      CHECK (inicio < fin)
  );

  CREATE INDEX IF NOT EXISTS idx_bloqueo_alcance_recurso_inicio
      ON bloqueo (alcance, recurso_id, inicio);
  ```
- **Dominio (`app/domain/models.py`):** `Bloqueo` suma `id: int | None = None` y `validar_datos_bloqueo(alcance, recurso_id, inicio, fin, motivo="") -> Bloqueo` (valida `alcance in ("profesional", "sillon")`, fechas naive sin `tzinfo` y `inicio < fin`).
- **Repositorio (`app/db/repositorio_bloqueos.py`):** `crear_bloqueo(conexion, bloqueo) -> Bloqueo` (verifica que el `profesional` o `sillon` exista antes de insertar; si no existe lanza `DatoInvalido` → `422`), `listar_bloqueos(conexion) -> list[Bloqueo]` y `eliminar_bloqueo(conexion, id_bloqueo) -> bool`. Las fechas se persisten con `isoformat(timespec="seconds")`.
- **API (`app/api/bloqueos.py`):**
  - `POST /bloqueos` (`201`, `AdminDep`) devuelve hoy `BloqueoSalida(id, alcance, recurso_id, inicio, fin, motivo)`.
  - En `openspec/changes/c-09-bloqueos/design.md` se declara explícitamente como *Non-Goal*: *"Listar o modificar turnos existentes que caigan dentro del nuevo bloqueo (queda explícitamente para `C-16 bloqueos-turnos-afectados` una vez decidida `SE-09`)"*.

### 2.2 Lo que ya existe en `app/domain/reglas_turno.py` (`C-10`)

En `app/domain/reglas_turno.py` ya existe la función privada:
```python
def _bloqueo_afecta(bloqueo: Bloqueo, turno: Turno) -> bool:
    if bloqueo.alcance == "profesional":
        return bloqueo.recurso_id == turno.profesional_id
    return bloqueo.recurso_id == turno.sillon_id
```
Combinada con `solapan(turno, bloqueo)` (`app/domain/intervalos.py`) y `turno.estado == "reservado"` (`RN-TUR-08`), la regla de dominio para saber si un bloqueo afecta a un turno **ya está modelada** y solo necesita exponerse como función pública pura en `app/domain/reglas_turno.py` (por ejemplo, `turnos_afectados_por_bloqueo(bloqueo: Bloqueo, turnos: Sequence[Turno]) -> list[Turno]`).

---

## 3. Supuestos sobre `C-11` (`crear-turno`) y bloqueo de implementación

Como `C-11` todavía no está en `main`, este explore explicita qué asume sobre el modelo y la persistencia que `C-11` introducirá (según `knowledge-base/04_modelo_de_datos.md` y `CHANGES.md`):

1. **Tabla `turno` en `app/db/esquema.sql`:**
   - Columnas esperadas: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `paciente_id INTEGER NOT NULL`, `profesional_id INTEGER NOT NULL`, `sillon_id INTEGER NOT NULL`, `prestacion_id INTEGER NOT NULL`, `inicio TEXT NOT NULL`, `fin TEXT NOT NULL`, `estado TEXT NOT NULL CHECK (estado IN ('reservado', 'cancelado'))`, `creado_por INTEGER NOT NULL`, `creado_en TEXT NOT NULL`.
   - Formato de `inicio` y `fin`: texto ISO 8601 local sin zona horaria (`YYYY-MM-DDTHH:MM:SS`, vía `isoformat(timespec="seconds")`), idéntico al de `bloqueo` en `C-09`.
   - Índices esperados (`KB 04`): `(profesional_id, inicio)` y `(sillon_id, inicio)`.
2. **Modelo de dominio (`app/domain/models.py`):**
   - La dataclass `Turno(paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado="reservado", id=None)` ya existe en `main`. `C-11` poblará `id` al insertar/leer de SQLite.
3. **Repositorio (`app/db/repositorio_turnos.py`):**
   - Existirá una función para insertar y consultar turnos. `C-16` podrá agregar una consulta parametrizada en `repositorio_turnos.py` (o `repositorio_bloqueos.py`) que recupere los turnos del recurso afectado, o bien traer los turnos activos del recurso y filtrarlos en dominio con `turnos_afectados_por_bloqueo(bloqueo, turnos)`.

> **Bloqueo de implementación:** `C-16` **no puede entrar en `/opsx:apply`** hasta que `C-09` (`bloqueos`) y `C-11` (`crear-turno`) estén integrados en la rama base, porque modifica `POST /bloqueos` y consulta la tabla `turno`.

---

## 4. Hipótesis de trabajo sobre `SE-09` (pendiente de confirmación del grupo)

> **Estado de `SE-09`:** **Propuesta pendiente de confirmación del grupo / cátedra.**
> Para este explore se trabaja bajo la hipótesis propuesta en `knowledge-base/10_preguntas_abiertas.md` §`SE-09`, `06_funcionalidades.md` §`US-005`, `07_flujos_principales.md` §`Flujo 5` y `CHANGES.md` §`C-16`: **el MVP solo LISTA los turnos afectados al crear un bloqueo, sin cancelarlos ni modificarlos.**

### 4.1 Cómo funciona bajo la hipótesis actual (Listar sin cancelar)

1. Administración envía `POST /bloqueos` con `{alcance, recurso_id, inicio, fin, motivo}`.
2. Se valida el bloqueo en dominio (`validar_datos_bloqueo`) y la existencia del recurso en DB.
3. Dentro de la misma `transaccion(conexion)`, se inserta el bloqueo y se consultan los turnos con `estado = 'reservado'` del recurso (`profesional_id = ?` o `sillon_id = ?`) cuyo intervalo `[turno.inicio, turno.fin)` se solape con `[bloqueo.inicio, bloqueo.fin)`.
4. `POST /bloqueos` responde `201` incluyendo los datos del bloqueo creado y la lista `turnos_afectados` ordenada por `inicio ASC, id ASC`.
5. Los turnos afectados **siguen en `estado = 'reservado'`** y **no se escribe en `auditoria_turno`** (porque ningún turno fue creado, reprogramado ni cancelado, y `IF-06` establece que los bloqueos en sí mismos no se auditan).
6. Recepción utiliza esa lista para contactar a los pacientes y reprogramar (`C-13`) o cancelar (`C-12`) cada turno manualmente.

### 4.2 Qué cambiaría si el grupo decidiera CANCELAR automáticamente (relación con `C-12`)

Si antes del `/opsx:propose` el equipo decidiera que crear un bloqueo debe **cancelar automáticamente** los turnos afectados:

- **Dependencia adicional en el roadmap:** `C-16` pasaría a depender no solo de `C-11`, sino también de **`C-12` (`cancelar-turno`)**, dejando de poder ejecutarse en paralelo con `C-12`.
- **Transacción atómica con `auditoria_turno` (Regla dura 5 y `RN-AUD-01`/`RN-AUD-03`):** en la misma `transaccion(conexion)` en que se inserta el bloqueo, cada turno afectado debería pasar a `estado = 'cancelado'` y generar su fila `INSERT INTO auditoria_turno` (`accion = 'cancelar'`, `usuario_id` del administrador que creó el bloqueo, `ocurrio_en` del reloj inyectado, `antes` con `"reservado"` y `despues` con `"cancelado"`).
- **Interacción con `RN-TUR-09` (reloj inyectado):** `C-12` exige que solo se cancelen turnos futuros (`turno.inicio > ahora`). Habría que definir qué ocurre si un bloqueo cubre un turno pasado o en curso: o bien se prohíben bloqueos en el pasado, o bien solo se cancelan los turnos con `inicio > ahora`.
- **Governance:** al modificar estado de turnos y escribir en `auditoria_turno`, el nivel de governance de `C-16` subiría de `MEDIO` a **`ALTO`** (igual que `C-11`, `C-12` y `C-13`).

### 4.3 Qué cambiaría si el grupo decidiera RECHAZAR el bloqueo (`409`)

- Si existen turnos en `estado = 'reservado'` que se solapan con el bloqueo, el dominio lanzaría un error (p. ej. `ConflictoAgenda` o `BloqueoConTurnosActivos` mapeado a `409` en `app/api/errores.py`) y no insertaría el bloqueo, obligando a recepción/administración a reprogramar o cancelar los turnos *antes* de cargar el bloqueo.

---

## 5. Qué falta implementar para `C-16` (bajo la hipótesis de listar sin cancelar)

1. **Capa de Dominio (`app/domain/reglas_turno.py` — Regla dura 1, 2, 3, 8, 11, 12):**
   - Agregar la función pura `turnos_afectados_por_bloqueo(bloqueo: Bloqueo, turnos: Sequence[Turno]) -> list[Turno]`:
     - Filtra los turnos donde `turno.estado == "reservado"`, `_bloqueo_afecta(bloqueo, turno)` es `True` y `solapan(turno, bloqueo)` es `True` (intervalos semiabiertos `[inicio, fin)`).
     - Devuelve la lista ordenada por `(turno.inicio, turno.id or 0)`.
     - No importa FastAPI ni SQLite, ni llama a `datetime.now()`.
2. **Capa de Persistencia (`app/db/` — Regla dura 4):**
   - Consulta SQL parametrizada con `?` para obtener los turnos del recurso (`WHERE profesional_id = ? AND estado = 'reservado'` o `WHERE sillon_id = ? AND estado = 'reservado'`, pudiendo acotar además en SQL con `AND inicio < ? AND fin > ?` y revalidar en dominio con `turnos_afectados_por_bloqueo`).
3. **Capa de API (`app/api/bloqueos.py` — Regla dura 7 y 8):**
   - Extender la respuesta de `POST /bloqueos` (y/o su schema Pydantic `BloqueoSalida`) para incluir `turnos_afectados: list[TurnoAfectadoSalida]` (con `id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin`, `estado`).
4. **Tests (`tests/domain/` y `tests/api/` — Regla dura 10 y 11, Strict TDD):**
   - Unitarios de dominio en `tests/domain/test_reglas_turno.py` (o `test_bloqueos_turnos_afectados.py`): solapamiento parcial, contención total, turnos contiguos en el borde `[inicio, fin)` **no** afectados (`RN-TUR-04`/`RN-TUR-05`), turnos `cancelado` excluidos (`RN-TUR-08`), turnos de otro profesional o sillón excluidos.
   - Integración/API en `tests/api/test_bloqueos.py`: bloqueo sin turnos → `turnos_afectados: []`; bloqueo con 2 turnos `reservado` y 1 `cancelado` → devuelve solo los 2 `reservado`; verificación posterior por `GET /turnos/{id}` (o repositorio) de que ambos siguen en `estado = "reservado"`; datos ficticios con sufijo `"(ficticio)"`.

---

## 6. Decisiones abiertas (con opciones y trade-offs)

### D-A1 — Resolución definitiva de `SE-09` (comportamiento ante turnos preexistentes)
- **Opción A (Recomendada — Propuesta MVP en KB y `CHANGES.md`):** Crear el bloqueo y devolver la lista de turnos activos afectados sin modificarlos (`estado = "reservado"`).
  - *Pros:* simple, no destruye turnos sin aviso al paciente, no requiere tocar `auditoria_turno` ni depende de `C-12`.
  - *Contras:* deja temporalmente en la base turnos `reservado` que solapan con un bloqueo hasta que recepción los reprograme o cancele manualmente.
- **Opción B:** Cancelar automáticamente en cascada todos los turnos futuros afectados y registrar auditoría.
  - *Pros:* la agenda queda libre de inmediato.
  - *Contras:* acopla `C-16` con `C-12`, exige definir qué pasa con turnos pasados/en curso (`RN-TUR-09`) y cancela sin haber hablado antes con el paciente.
- **Opción C:** Rechazar `POST /bloqueos` con `409` si existen turnos activos en el rango.
  - *Pros:* invariante estricta en base de datos (nunca coexisten un bloqueo y un turno `reservado` superpuestos).
  - *Contras:* mala experiencia ante una urgencia (ej. rotura de un sillón o licencia médica imprevista): administración no puede bloquear rápido para frenar *nuevos* turnos hasta vaciar manualmente todos los existentes.

### D-A2 — Forma del contrato JSON de `POST /bloqueos` y compatibilidad con `C-09`
En `origin/bruno-c09-bloqueos`, `POST /bloqueos` devuelve en el nivel raíz:
`{"id": 1, "alcance": "profesional", "recurso_id": 1, "inicio": "...", "fin": "...", "motivo": "..."}`.
- **Opción A (Recomendada — Aditiva sin romper tests de `C-09`):** Agregar el campo `turnos_afectados: list[TurnoSalida] = []` al objeto `BloqueoSalida` de `POST /bloqueos` (mientras que `GET /bloqueos` sigue devolviendo la lista de bloqueos sin `turnos_afectados`, usando un schema separado `BloqueoCreadoSalida(BloqueoSalida)` en `POST /bloqueos`).
  - *Pros:* es 100 % aditivo respecto de los campos que ya devuelve `POST /bloqueos` en `C-09`; no anida el bloqueo bajo otra clave; no penaliza `GET /bloqueos` con consultas N+1.
  - *Contras:* en `tests/api/test_bloqueos.py` de `C-09`, cualquier aserción que compare el diccionario completo (`assert respuesta.json() == {...}`) deberá incluir `"turnos_afectados": []`.
- **Opción B:** Envolver la respuesta de `POST /bloqueos` en `{"bloqueo": {...}, "turnos_afectados": [...]}`.
  - *Pros:* separa semánticamente la entidad creada del reporte de impacto.
  - *Contras:* rompe todas las aserciones de `POST /bloqueos` de `C-09` (`respuesta.json()["id"]`).

### D-A3 — ¿Se incluyen turnos afectados pasados o solo futuros?
`C-09` no exige que un bloqueo sea futuro (no inyecta reloj en `POST /bloqueos`).
- **Opción A (Recomendada):** Incluir **todos** los turnos con `estado = 'reservado'` que se solapen con `[bloqueo.inicio, bloqueo.fin)` para ese recurso, sin filtrar por `ahora`.
  - *Pros:* `POST /bloqueos` no necesita reloj para decidir qué reportar; la consulta depende únicamente del intervalo `[inicio, fin)` del bloqueo y respeta intervalos semiabiertos (`RN-TUR-04`).
  - *Contras:* si alguien carga un bloqueo retroactivo, también listará turnos `reservado` de ese período.
- **Opción B:** Filtrar solo turnos con `es_futuro(turno, ahora)` (`app/domain/intervalos.py`, `C-02`) usando un reloj inyectado (`RN-TUR-09`, Regla dura 2).
  - *Pros:* solo muestra turnos que recepción todavía puede reprogramar/cancelar (`RN-TUR-09`).
  - *Contras:* oculta turnos en curso o recién iniciados dentro del rango bloqueado.

### D-A4 — ¿Dónde se ejecuta el filtro de solapamiento (SQL vs. Dominio)?
- **Opción A (Recomendada — Híbrida alineada con Regla dura 8 y `C-10`):** El repositorio recupera de SQLite los turnos `reservado` del recurso que se solapan con el rango (`WHERE ... AND estado = 'reservado' AND inicio < ? AND fin > ?` con marcadores `?`) y el dominio aplica `turnos_afectados_por_bloqueo(bloqueo, turnos)` usando `solapan()` e `_bloqueo_afecta()`.
  - *Pros:* aprovecha los índices `(profesional_id, inicio)` / `(sillon_id, inicio)` en SQLite y a la vez garantiza por contrato que la regla de negocio viva y se testee en `app/domain/` sin base de datos ni HTTP (Reglas duras 1, 3, 8 y 11).
- **Opción B:** Filtrar exclusivamente en SQL sin función en `app/domain/`.
  - *Contras:* viola la Regla dura 8 (*"la lógica vive en `app/domain/`"*) y la Regla dura 11 (*"los tests de dominio corren sin base de datos ni HTTP"*).

---

## 7. Riesgos identificados

| Riesgo | Impacto | Mitigación propuesta |
|---|---|---|
| `SE-09` sigue marcada como abierta en `10_preguntas_abiertas.md` | Cambiar de criterio después de implementar obliga a rehacer `C-16` | Confirmar con el equipo la hipótesis de "listar sin cancelar" antes de correr `/opsx:propose c-16-bloqueos-turnos-afectados` |
| `C-09` y `C-11` aún no están mergeados en `main` | No existen en `main` ni `app/api/bloqueos.py` ni la tabla `turno` | Esperar el merge de `C-09` y `C-11` antes de `/opsx:apply`; diseñar `C-16` sobre el contrato real de `origin/bruno-c09-bloqueos` |
| Turnos contiguos al bloqueo (`turno.fin == bloqueo.inicio` o `turno.inicio == bloqueo.fin`) | Falsos positivos si se usa `<=` / `>=` en vez de `<` / `>` | Reutilizar `solapan(turno, bloqueo)` de `app/domain/intervalos.py` (intervalos semiabiertos `[inicio, fin)`, Regla dura 3 y `RN-TUR-05`) |
| Coexistencia de turnos `reservado` con un bloqueo recién creado | En `C-13` (`reprogramar-turno`) o `C-14` (`agenda`) conviven en el mismo rango un bloqueo y el turno preexistente | Es el comportamiento esperado bajo `SE-09` (listar sin cancelar); en `C-14` la agenda mostrará ambos para que recepción vea el conflicto y lo reprograme |
| Aserciones de igualdad exacta en `tests/api/test_bloqueos.py` de `C-09` | Si `POST /bloqueos` agrega `"turnos_afectados": []`, los tests de `C-09` que comparan el JSON completo pueden requerir actualizarse | Usar `BloqueoCreadoSalida` solo en `POST /bloqueos` (dejando `GET /bloqueos` intacto) y actualizar en `C-16` los tests de `POST /bloqueos` para contemplar `"turnos_afectados": []` |

---

## 8. Recomendación

1. **Confirmar `SE-09` con la opción A (listar sin cancelar):** mantiene el alcance acotado del MVP tal como proponen `US-005`, `Flujo 5` y `CHANGES.md`, evita acoplar `C-16` con `C-12` (`cancelar-turno`) y respeta que no se cancelen turnos sin previo contacto de recepción con el paciente.
2. **Mantener la lógica en `app/domain/reglas_turno.py`:** exponer `turnos_afectados_por_bloqueo(bloqueo, turnos)` reutilizando `_bloqueo_afecta` y `solapan` (intervalos semiabiertos `[inicio, fin)`), testeada en dominio puro sin DB ni HTTP.
3. **Extender `POST /bloqueos` de forma aditiva (`BloqueoCreadoSalida`):** devolver todos los campos actuales de `BloqueoSalida` más `turnos_afectados: list[TurnoSalida]`, manteniendo `GET /bloqueos` sin cambios.
4. **Secuencia operativa:** una vez confirmado `SE-09` por el grupo, se puede avanzar con `/opsx:propose c-16-bloqueos-turnos-afectados`; la ejecución de `/opsx:apply c-16-bloqueos-turnos-afectados` debe aguardar a que `C-09` y `C-11` estén integrados en la rama.
