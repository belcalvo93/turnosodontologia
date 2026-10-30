# Explore — C-16 bloqueos-turnos-afectados

Relevamiento previo al propose (fase Explore de OpenSpec/SDD). **No implementa código**: fija el contexto y el estado actual en `main` (con `C-09` y `C-11` ya fusionados y archivados), la decisión sobre `SE-09` (listar sin cancelar), las decisiones D-A1 a D-A4 adoptadas, los riesgos y la recomendación técnica.

---

## 1. Contexto, objetivo y alcance en el roadmap

Según `CHANGES.md` (sección `[C-16] bloqueos-turnos-afectados`, Fase 4):

- **Objetivo funcional (`US-005`, `Flujo 5`):** cuando un usuario con rol `administracion` registra un bloqueo horario (`POST /bloqueos`) sobre un profesional (vacaciones, feriado, licencia) o un sillón (mantenimiento), pueden existir turnos ya reservados que se solapen con el intervalo `[inicio, fin)` de ese recurso. `C-16` resuelve cómo informa o actúa el sistema frente a esos turnos preexistentes.
- **Scope declarado en `CHANGES.md` (bajo la decisión adoptada para `SE-09` — decidida el 2026-10-29, ver §4 y `design.md` D-A1):**
  - `POST /bloqueos` devuelve, junto con el bloqueo creado, la lista de turnos activos (`estado = 'reservado'`) que quedan dentro del intervalo `[inicio, fin)` y corresponden al recurso bloqueado (`profesional_id` o `sillon_id`).
  - **No cancela ni modifica** esos turnos: permanecen en estado `reservado` para que recepción los reprograme o cancele manualmente.
  - Si el grupo o la cátedra propusiera otra opción en `SE-09` (rechazar el bloqueo con `409` o cancelar automáticamente en cascada), la decisión queda registrada como revisable en `design.md` D-A1 y el scope se reemplazaría con un change nuevo.
  - **Tests mínimos previstos:** bloqueo sin turnos superpuestos → lista vacía (`[]`); bloqueo sobre 2 turnos activos y 1 cancelado → lista con los 2 activos; los turnos afectados conservan `estado = "reservado"`.
- **Dependencias (según `CHANGES.md`):** únicamente `C-11` (`crear-turno`), ya fusionado y archivado en `main` (tabla `turno` y `POST /turnos` disponibles). El resto de la cadena (`C-02`, `C-04`, `C-05`, `C-06`, `C-08`, `C-09`, `C-10`) está completa y archivada; **no quedan bloqueos ni precondiciones pendientes**.
- **Governance:** `MEDIO`.
- **Referencias en `knowledge-base/`:**
  - `10_preguntas_abiertas.md` §`SE-09` (prioridad Alta: *"Turnos ya existentes cuando se crea un bloqueo que los cubre: ¿se cancelan, se listan para reprogramar, se rechaza el bloqueo?"*).
  - `07_flujos_principales.md` §`Flujo 5 — Bloquear un horario`.
  - `06_funcionalidades.md` §`US-005 — Bloquear rango horario de profesional o sillón`.
  - `05_reglas_de_negocio.md` §`RN-REC-02`, §`RN-TUR-04`, §`RN-TUR-05`, §`RN-TUR-08`.
  - `04_modelo_de_datos.md` §`Bloqueo`, §`Turno`, §`AuditoriaTurno`.
  - `03_actores_y_roles.md` §`RBAC` (`administracion` tiene `C L B` sobre bloqueos; `recepcion` y `odontologo` tienen `L`).

---

## 2. Qué existe hoy en `main`

| Pieza | Estado actual | Evidencia |
|---|---|---|
| `Profesional` y tabla `profesional` (`C-04`) | **En `main` (archivado)** | `app/domain/models.py`, `app/db/repositorio_profesionales.py`, `app/api/profesionales.py`, `openspec/specs/profesionales/spec.md` |
| `Sillon`, `Prestacion` y tablas `sillon`/`prestacion` (`C-05`) | **En `main` (archivado)** | `app/domain/models.py`, `app/db/repositorio_sillones.py`, `app/api/sillones.py`, `openspec/specs/sillones/spec.md` |
| `Intervalo` y `solapan(a, b)` semiabierto `[inicio, fin)` (`C-10`) + `es_futuro` y `TurnoNoModificable` (`C-02`) | **En `main` (archivados)** | `app/domain/intervalos.py` (`solapan`: `a.inicio < b.fin and b.inicio < a.fin`; `es_futuro` con reloj inyectado), `app/domain/errores.py` (`TurnoNoModificable`), `app/api/errores.py` (mapeo `409`→`turno_no_modificable`) |
| `Turno`, `Bloqueo`, `validar_alta` y `_bloqueo_afecta` (`C-10`) | **En `main` (archivado)** | `app/domain/models.py`, `app/domain/reglas_turno.py`, `openspec/specs/reglas-alta-turno/spec.md` |
| Tabla `bloqueo`, `repositorio_bloqueos.py` y `GET/POST/DELETE /bloqueos` (`C-09`) | **En `main` (archivado)** | `app/db/esquema.sql` (`CREATE TABLE IF NOT EXISTS bloqueo` + índice `idx_bloqueo_alcance_recurso_inicio`), `app/db/repositorio_bloqueos.py` (incluida `listar_bloqueos_de_recursos`, agregada por `C-11`), `app/api/bloqueos.py`, `openspec/specs/bloqueos/spec.md` |
| Tabla `turno`, `auditoria_turno`, `repositorio_turnos.py` y `POST/GET /turnos` (`C-11`) | **En `main` (archivado)** | `app/db/esquema.sql` (tablas `turno` y `auditoria_turno` + índices `(profesional_id, inicio)`, `(sillon_id, inicio)`, `(paciente_id, inicio)`), `app/db/repositorio_turnos.py` (`COLUMNAS_TURNO`, `turno_desde_fila`, `crear_turno`, `obtener_turno`, `listar_turnos_activos_del_dia`), `app/api/turnos.py` (`TurnoResponse`, `turno_a_response`), `openspec/specs/turnos/spec.md` |
| Cancelación (`C-12`) | **Pendiente** (no hay endpoint ni `validar_cancelacion` integrado) | `CHANGES.md` §`C-12` |
| Reprogramación (`C-13`) | **En progreso** (dominio con `validar_reprogramacion` y change abierto) | `app/domain/reglas_turno.py`, `openspec/changes/c-13-reprogramar-turno/` |

### 2.1 Lo que dejó `C-09` en `main` (archivado)

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
- **Repositorio (`app/db/repositorio_bloqueos.py`):** `crear_bloqueo(conexion, bloqueo) -> Bloqueo` (verifica que el `profesional` o `sillon` exista antes de insertar; si no existe lanza `DatoInvalido` → `422`), `listar_bloqueos(conexion) -> list[Bloqueo]` y `eliminar_bloqueo(conexion, id_bloqueo) -> bool`. Las fechas se persisten con `isoformat(timespec="seconds")`. Para `C-11` se agregó también `listar_bloqueos_de_recursos(conexion, *, profesional_id, sillon_id, desde, hasta) -> list[Bloqueo]`, que filtra por recurso y ventana con SQL parametrizado (`inicio < ? AND fin > ?`) y ordena por `inicio ASC, id ASC`: es el patrón directo para la consulta de `C-16`.
- **API (`app/api/bloqueos.py`):**
  - `POST /bloqueos` (`201`, `AdminDep`) devuelve hoy `BloqueoSalida(id, alcance, recurso_id, inicio, fin, motivo)` dentro de `transaccion(conexion)`.
  - En `openspec/changes/archive/2026-10-29-c-09-bloqueos/design.md` quedó como *Non-Goal*: *"Listar o modificar turnos existentes que caigan dentro del nuevo bloqueo (queda explícitamente para `C-16 bloqueos-turnos-afectados` una vez decidida `SE-09`)"* — exactamente el punto que este change resuelve.

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

## 3. Lo que dejó `C-11` (`crear-turno`) en `main` (archivado)

`C-11` ya está integrado y archivado, así que este change ya no depende de supuestos. Lo relevante para `C-16`:

1. **Tabla `turno` en `app/db/esquema.sql` (real):**
   - Columnas: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `paciente_id NOT NULL REFERENCES paciente(id)`, `profesional_id NOT NULL REFERENCES profesional(id)`, `sillon_id NOT NULL REFERENCES sillon(id)`, `prestacion_id NOT NULL REFERENCES prestacion(id)`, `inicio TEXT NOT NULL`, `fin TEXT NOT NULL`, `estado TEXT NOT NULL CHECK (estado IN ('reservado', 'cancelado'))`, `creado_por NOT NULL REFERENCES usuario(id)`, `creado_en TEXT NOT NULL`, `CHECK (inicio < fin)`.
   - Formato de `inicio` y `fin`: ISO 8601 local sin zona horaria (`YYYY-MM-DDTHH:MM:SS`, vía `isoformat(timespec="seconds")`, design D4), idéntico al de `bloqueo` en `C-09`.
   - Índices: `(profesional_id, inicio)`, `(sillon_id, inicio)` y `(paciente_id, inicio)`.
2. **Repositorio (`app/db/repositorio_turnos.py`):**
   - `COLUMNAS_TURNO` (constante con las 8 columnas en el orden de lectura) y `turno_desde_fila(fila) -> Turno` ya son públicas para que las reutilicen `C-12`, `C-13` y `C-14`; `C-16` las usa igual.
   - `listar_turnos_activos_del_dia(...)` muestra el patrón de consulta usada por `C-11`: `WHERE estado = 'reservado' AND (… = ? …) AND inicio < ? AND fin > ?` con `ORDER BY inicio ASC, id ASC`.
   - `C-16` agrega su consulta en `repositorio_turnos.py` (o `repositorio_bloqueos.py`), dejando en el dominio el filtro final con `turnos_afectados_por_bloqueo(bloqueo, turnos)`.
3. **Serialización (`app/api/turnos.py`):** `TurnoResponse(id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado)` y `turno_a_response(turno) -> TurnoResponse` permiten serializar los turnos afectados sin duplicar un schema en `bloqueos.py`.

> **Estado de la implementación:** ya no hay bloqueo previo: se puede entrar en `/opsx:apply` una vez aprobado el propose.

---

## 4. Decisión sobre `SE-09` (decidida el 2026-10-29)

> **Estado de `SE-09`:** **Decidida el 2026-10-29 por Belén Calvo, responsable de `C-16`**, ante la falta de respuesta del grupo y siguiendo la propuesta MVP de `CHANGES.md` y `US-005` (ver `design.md` D-A1). Es revisable si el grupo propone otra cosa antes del `/opsx:apply`.
> **Decisión:** **el MVP solo LISTA los turnos afectados al crear un bloqueo, sin cancelarlos ni modificarlos ni escribir en `auditoria_turno`.** La cancelación queda fuera de alcance (es `C-12`).

### 4.1 Cómo funciona bajo la decisión tomada (Listar sin cancelar)

1. Administración envía `POST /bloqueos` con `{alcance, recurso_id, inicio, fin, motivo}`.
2. Se valida el bloqueo en dominio (`validar_datos_bloqueo`) y la existencia del recurso en DB.
3. Dentro de la misma `transaccion(conexion)`, se inserta el bloqueo y se consultan los turnos con `estado = 'reservado'` del recurso (`profesional_id = ?` o `sillon_id = ?`) cuyo intervalo `[turno.inicio, turno.fin)` se solape con `[bloqueo.inicio, bloqueo.fin)`.
4. `POST /bloqueos` responde `201` incluyendo los datos del bloqueo creado y la lista `turnos_afectados` ordenada por `inicio ASC, id ASC`.
5. Los turnos afectados **siguen en `estado = 'reservado'`** y **no se escribe en `auditoria_turno`** (porque ningún turno fue creado, reprogramado ni cancelado, y `IF-06` establece que los bloqueos en sí mismos no se auditan).
6. Recepción utiliza esa lista para contactar a los pacientes y reprogramar (`C-13`) o cancelar (`C-12`) cada turno manualmente.

### 4.2 Relación descartada: cancelar automáticamente (con `C-12`)

Si antes del `/opsx:propose` el equipo decidiera que crear un bloqueo debe **cancelar automáticamente** los turnos afectados:

- **Dependencia adicional en el roadmap:** `C-16` pasaría a depender no solo de `C-11`, sino también de **`C-12` (`cancelar-turno`)**, dejando de poder ejecutarse en paralelo con `C-12`.
- **Transacción atómica con `auditoria_turno` (Regla dura 5 y `RN-AUD-01`/`RN-AUD-03`):** en la misma `transaccion(conexion)` en que se inserta el bloqueo, cada turno afectado debería pasar a `estado = 'cancelado'` y generar su fila `INSERT INTO auditoria_turno` (`accion = 'cancelar'`, `usuario_id` del administrador que creó el bloqueo, `ocurrio_en` del reloj inyectado, `antes` con `"reservado"` y `despues` con `"cancelado"`).
- **Interacción con `RN-TUR-09` (reloj inyectado):** `C-12` exige que solo se cancelen turnos futuros (`turno.inicio > ahora`). Habría que definir qué ocurre si un bloqueo cubre un turno pasado o en curso: o bien se prohíben bloqueos en el pasado, o bien solo se cancelan los turnos con `inicio > ahora`.
- **Governance:** al modificar estado de turnos y escribir en `auditoria_turno`, el nivel de governance de `C-16` subiría de `MEDIO` a **`ALTO`** (igual que `C-11`, `C-12` y `C-13`).

### 4.3 Relación descartada: rechazar el bloqueo (`409`)

- Si existen turnos en `estado = 'reservado'` que se solapan con el bloqueo, el dominio lanzaría un error (p. ej. `ConflictoAgenda` o `BloqueoConTurnosActivos` mapeado a `409` en `app/api/errores.py`) y no insertaría el bloqueo, obligando a recepción/administración a reprogramar o cancelar los turnos *antes* de cargar el bloqueo.

---

## 5. Qué falta implementar para `C-16` (bajo la decisión de listar sin cancelar)

1. **Capa de Dominio (`app/domain/reglas_turno.py` — Regla dura 1, 2, 3, 8, 11, 12):**
   - Agregar la función pura `turnos_afectados_por_bloqueo(bloqueo: Bloqueo, turnos: Sequence[Turno]) -> list[Turno]`:
     - Filtra los turnos donde `turno.estado == "reservado"`, `_bloqueo_afecta(bloqueo, turno)` es `True` y `solapan(turno, bloqueo)` es `True` (intervalos semiabiertos `[inicio, fin)`).
     - Devuelve la lista ordenada por `(turno.inicio, turno.id or 0)`.
     - No importa FastAPI ni SQLite, ni llama a `datetime.now()` (`C-16` no depende del reloj).
2. **Capa de Persistencia (`app/db/` — Regla dura 4):**
   - Consulta SQL parametrizada con `?` que recupere los turnos `reservado` del recurso afectado `(profesional_id = ?` o `sillon_id = ?`) acotada por rango (`AND inicio < ? AND fin > ?`, patrón idéntico a `listar_bloqueos_de_recursos` y `listar_turnos_activos_del_dia`), reutilizando `COLUMNAS_TURNO` y `turno_desde_fila`. El filtro final lo resuelve el dominio con `turnos_afectados_por_bloqueo`.
3. **Capa de API (`app/api/bloqueos.py` — Regla dura 7 y 8):**
   - Extender la respuesta de `POST /bloqueos` con un schema `BloqueoCreadoSalida(BloqueoSalida)` que suma `turnos_afectados: list[TurnoResponse]`, reutilizando `TurnoResponse` y `turno_a_response` de `app/api/turnos.py`. `GET /bloqueos` queda sin el campo.
4. **Tests (`tests/domain/` y `tests/api/` — Regla dura 10 y 11, Strict TDD):**
   - Unitarios de dominio en `tests/domain/test_reglas_turno.py` (o `test_bloqueos_turnos_afectados.py`): solapamiento parcial, contención total, turnos contiguos en el borde `[inicio, fin)` **no** afectados (`RN-TUR-04`/`RN-TUR-05`), turnos `cancelado` excluidos (`RN-TUR-08`), turnos de otro profesional o sillón excluidos.
   - Integración/API en `tests/api/test_bloqueos.py`: bloqueo sin turnos → `turnos_afectados: []`; bloqueo con 2 turnos `reservado` y 1 `cancelado` → devuelve solo los 2 `reservado`; verificación posterior por `GET /turnos/{id}` de que ambos siguen en `estado = "reservado"`; datos ficticios con sufijo `"(ficticio)"`.
   - La única aserción de igualdad exacta de `tests/api/test_bloqueos.py` de `C-09` sobre la respuesta de `POST /bloqueos` se actualiza para incluir `"turnos_afectados": []` (aprobado por el usuario; el resto de los tests de `C-09` y `GET /bloqueos` no se tocan).

---

## 6. Decisiones (adoptadas para el propose)

### D-A1 — Resolución de `SE-09` (comportamiento ante turnos preexistentes)
> **DECIDIDO el 2026-10-29 por Belén Calvo, responsable de `C-16`**, ante la falta de respuesta del grupo y siguiendo la propuesta MVP de `CHANGES.md` y `US-005`. Se adopta la **Opción A**. Es revisable si el grupo propone otra cosa antes del `/opsx:apply`.
- **Opción A (Adoptada — Propuesta MVP en KB y `CHANGES.md`):** Crear el bloqueo y devolver la lista de turnos activos afectados sin modificarlos (`estado = "reservado"`).
  - *Pros:* simple, no destruye turnos sin aviso al paciente, no requiere tocar `auditoria_turno` ni depende de `C-12`.
  - *Contras:* deja temporalmente en la base turnos `reservado` que solapan con un bloqueo hasta que recepción los reprograme o cancele manualmente.
- **Opción B (Descartada):** Cancelar automáticamente en cascada todos los turnos futuros afectados y registrar auditoría.
  - *Pros:* la agenda queda libre de inmediato.
  - *Contras:* acopla `C-16` con `C-12`, exige definir qué pasa con turnos pasados/en curso (`RN-TUR-09`) y cancela sin haber hablado antes con el paciente.
- **Opción C (Descartada):** Rechazar `POST /bloqueos` con `409` si existen turnos activos en el rango.
  - *Pros:* invariante estricta en base de datos (nunca coexisten un bloqueo y un turno `reservado` superpuestos).
  - *Contras:* mala experiencia ante una urgencia (ej. rotura de un sillón o licencia médica imprevista): administración no puede bloquear rápido para frenar *nuevos* turnos hasta vaciar manualmente todos los existentes.

### D-A2 — Forma del contrato JSON de `POST /bloqueos` y compatibilidad con `C-09` (**Confirmada por Bruno**)
En `main`, `POST /bloqueos` devuelve hoy en el nivel raíz:
`{"id": 1, "alcance": "profesional", "recurso_id": 1, "inicio": "...", "fin": "...", "motivo": "..."}`.
- **Opción A (Adoptada):** Agregar el campo `turnos_afectados: list[TurnoSalida] = []` al mismo nivel del objeto de `POST /bloqueos` (mientras que `GET /bloqueos` sigue devolviendo la lista de bloqueos sin `turnos_afectados`, usando un schema separado `BloqueoCreadoSalida(BloqueoSalida)` en `POST /bloqueos`).
  - *Pros:* es 100 % aditivo respecto de los campos actuales de `POST /bloqueos`; no anida el bloqueo bajo otra clave; no penaliza `GET /bloqueos` con consultas N+1.
  - *Contras:* la única aserción de igualdad completa de `tests/api/test_bloqueos.py` de `C-09` sobre `POST /bloqueos` deberá incluir `"turnos_afectados": []` (única edición aprobada en tests de `C-09`; `GET /bloqueos` queda intacto).
- **Opción B (Descartada):** Envolver la respuesta de `POST /bloqueos` en `{"bloqueo": {...}, "turnos_afectados": [...]}`.
  - *Pros:* separa semánticamente la entidad creada del reporte de impacto.
  - *Contras:* rompe todas las aserciones de `POST /bloqueos` de `C-09` (`respuesta.json()["id"]`).

### D-A3 — ¿Se incluyen turnos afectados pasados o solo futuros? (**Adoptada: sin reloj**)
`C-09` no exige que un bloqueo sea futuro (no inyecta reloj en `POST /bloqueos`).
- **Opción A (Adoptada):** Incluir **todos** los turnos con `estado = 'reservado'` que se solapen con `[bloqueo.inicio, bloqueo.fin)` para ese recurso, sin filtrar por `ahora`.
  - *Pros:* `POST /bloqueos` no necesita reloj para decidir qué reportar; la consulta depende únicamente del intervalo `[inicio, fin)` del bloqueo y respeta intervalos semiabiertos (`RN-TUR-04`).
  - *Contras:* si alguien carga un bloqueo retroactivo, también listará turnos `reservado` de ese período.
- **Opción B (Descartada):** Filtrar solo turnos con `es_futuro(turno, ahora)` (`app/domain/intervalos.py`, `C-02`) usando un reloj inyectado (`RN-TUR-09`, Regla dura 2).
  - *Pros:* solo muestra turnos que recepción todavía puede reprogramar/cancelar (`RN-TUR-09`).
  - *Contras:* oculta turnos en curso o recién iniciados dentro del rango bloqueado.

### D-A4 — ¿Dónde se ejecuta el filtro de solapamiento (SQL vs. Dominio)? (**Adoptada: híbrida**)
- **Opción A (Adoptada — Híbrida alineada con Regla dura 8 y `C-10`):** El repositorio recupera de SQLite los turnos `reservado` del recurso que se solapan con el rango (`WHERE ... AND estado = 'reservado' AND inicio < ? AND fin > ?` con marcadores `?`) y el dominio aplica `turnos_afectados_por_bloqueo(bloqueo, turnos)` usando `solapan()` e `_bloqueo_afecta()`.
  - *Pros:* aprovecha los índices `(profesional_id, inicio)` / `(sillon_id, inicio)` en SQLite y a la vez garantiza por contrato que la regla de negocio viva y se testee en `app/domain/` sin base de datos ni HTTP (Reglas duras 1, 3, 8 y 11).
- **Opción B (Descartada):** Filtrar exclusivamente en SQL sin función en `app/domain/`.
  - *Contras:* viola la Regla dura 8 (*"la lógica vive en `app/domain/`"*) y la Regla dura 11 (*"los tests de dominio corren sin base de datos ni HTTP"*).

---

## 7. Riesgos identificados

| Riesgo | Impacto | Mitigación propuesta |
|---|---|---|
| `SE-09` quedó decidida por la responsable (2026-10-29) y sigue marcada como abierta en `10_preguntas_abiertas.md` | Cambiar de criterio después de implementar obliga a rehacer `C-16` | Registrar la decisión en `design.md` con fecha y responsable (hecho); dejar anotado que es revisable si el grupo propone otra cosa antes del `/opsx:apply` |
| ~~`C-09` y `C-11` aún no están mergeados en `main`~~ | ~~No existían en `main`~~ | **Resuelto:** `C-09` y `C-11` están fusionados y archivados en `main`; el diseño ya usa el código real (`repositorio_bloqueos.py`, `repositorio_turnos.py`, `app/api/turnos.py`) |
| Turnos contiguos al bloqueo (`turno.fin == bloqueo.inicio` o `turno.inicio == bloqueo.fin`) | Falsos positivos si se usa `<=` / `>=` en vez de `<` / `>` | Reutilizar `solapan(turno, bloqueo)` de `app/domain/intervalos.py` (intervalos semiabiertos `[inicio, fin)`, Regla dura 3 y `RN-TUR-05`) |
| Coexistencia de turnos `reservado` con un bloqueo recién creado | En `C-13` (`reprogramar-turno`) o `C-14` (`agenda`) conviven en el mismo rango un bloqueo y el turno preexistente | Es el comportamiento esperado bajo `SE-09` (listar sin cancelar); en `C-14` la agenda mostrará ambos para que recepción vea el conflicto y lo reprograme |
| Aserción de igualdad exacta en `tests/api/test_bloqueos.py` de `C-09` | Si `POST /bloqueos` agrega `"turnos_afectados": []`, la aserción que compara el JSON completo rompe | Ya aprobado: en `C-16` se actualiza esa única aserción para incluir `"turnos_afectados": []`; `GET /bloqueos` y el resto de los tests de `C-09` no se tocan |

---

## 8. Recomendación

1. ~~**Confirmar `SE-09` con la opción A (listar sin cancelar)**~~ → **Confirmada el 2026-10-29 (Opción A, decidida por Belén Calvo):** mantiene el alcance acotado del MVP tal como proponen `US-005`, `Flujo 5` y `CHANGES.md`, evita acoplar `C-16` con `C-12` (`cancelar-turno`) y respeta que no se cancelen turnos sin previo contacto de recepción con el paciente.
2. **Mantener la lógica en `app/domain/reglas_turno.py`:** exponer `turnos_afectados_por_bloqueo(bloqueo, turnos)` reutilizando `_bloqueo_afecta` y `solapan` (intervalos semiabiertos `[inicio, fin)`), testeada en dominio puro sin DB ni HTTP.
3. **Extender `POST /bloqueos` de forma aditiva (`BloqueoCreadoSalida`):** devolver todos los campos actuales de `BloqueoSalida` más `turnos_afectados: list[TurnoResponse]` (reutilizando `turno_a_response` de `app/api/turnos.py`), manteniendo `GET /bloqueos` sin cambios.
4. **Secuencia operativa:** con `SE-09` decidida y `C-09`/`C-11` en `main`, el change está desbloqueado; puede avanzar `/opsx:propose c-16-bloqueos-turnos-afectados` y luego `/opsx:apply` sin precondiciones pendientes.
