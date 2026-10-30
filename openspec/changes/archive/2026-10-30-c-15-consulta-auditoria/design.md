# Design — C-15 consulta-auditoria

## Context

Ver `proposal.md` §Why. Estado y restricciones que condicionan el enfoque:

- `C-11` creó `auditoria_turno` y `registrar_auditoria()` (solo `INSERT`), con triggers que rechazan `UPDATE` y `DELETE`. Las filas guardan `antes`/`despues` como `TEXT` JSON y `ocurrio_en` como `TEXT` ISO sin offset.
- `C-11`, `C-12` y `C-13` comparten `snapshot_turno()`: exactamente 8 claves (`id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin`, `estado`) y `antes = NULL` solo en `crear`.
- La capability `auditoria-turnos` ya existe en `openspec/specs/` con 5 requirements del lado escritura, incluido "Auditoría de solo agregado", que ya exige que la API no exponga rutas de edición ni borrado.
- `GET /turnos/{id}` (`app/api/turnos.py`) fija el patrón de consulta: `Path/Query` con `ge=1`, `obtener_conexion` por request, `404` con `NoEncontrado` y RBAC por dependencia.
- Reglas duras aplicables (`AGENTS.md`): 1 (dominio puro), 4 (SQL parametrizado), 7 (errores en español con código), 8 (reglas en `app/domain/`), 11 (cada RN con test), 12 (`snake_case` y type hints).
- Línea base: 650 tests verdes en `main`. Sin cambios de esquema ni migraciones.

## Goals / Non-Goals

**Goals:**

- Exponer el historial de auditoría de un turno a administración con un contrato estable y sin datos sensibles.
- Leer la tabla existente sin tocar la capa de escritura (`repositorio_turnos.py`, `api/turnos.py`).
- Orden cronológico determinista incluso con varios registros en el mismo segundo.
- Diferenciar "turno inexistente" (`404`) de "turno sin historial" (imposible: todo turno tiene al menos el alta).
- Tests de repositorio y de API, incluidos los 405/404 de las rutas de escritura.

**Non-Goals:**

- Paginación, filtros por acción/usuario/fecha o listado global sin `turno_id`.
- Retención, purga o exportación de auditoría (IF-06).
- Cambiar el formato de escritura, los triggers o el esquema.
- Rutas de escritura de auditoría.
- Exponer el `username` histórico: C-07 hace el `username` inmutable, así que el actual es el que operó.

## Decisions

- **D1 — Se modifica `auditoria-turnos`, no se crea una capability nueva.**
  *Por qué:* la capability ya posee el historial completo del turno (escritura, snapshot, atomicidad y solo-agregado). Una capability `auditoria` paralela duplicaría el dominio y obligaría a mover requirements existentes.
  *Alternativa descartada:* crear `consulta-auditoria` como spec propio — fragmenta una única responsabilidad en dos specs que siempre cambian juntas.

- **D2 — Sin cambios de esquema.**
  *Por qué:* la tabla, los FK y los triggers ya cubren la lectura. `esquema.sql` se reaplica en cada arranque con `CREATE ... IF NOT EXISTS`, pero C-15 no agrega nada; el índice sobre `turno_id` queda como mejora futura (ver Open Questions).

- **D3 — Entidad de lectura `RegistroAuditoria` en `app/domain/models.py`.**
  ```python
  @dataclass(frozen=True)
  class RegistroAuditoria:
      id: int
      turno_id: int
      accion: AccionAuditoria
      usuario_id: int
      username: str | None
      ocurrio_en: datetime
      antes: dict[str, object] | None
      despues: dict[str, object]
  ```
  *Por qué:* es un tipo del dominio (el "qué" de la auditoría) y permite que `app/db` lo devuelva sin filtrar `TEXT` a la API (regla dura 1: `db → domain` solo tipos).
  *Alternativa descartada:* devolver `sqlite3.Row` o tuplas — acopla el router al esquema y pierde type hints.

- **D4 — Repositorio dedicado `app/db/repositorio_auditoria.py`.**
  - `listar_auditoria_por_turno(conexion, turno_id) -> list[RegistroAuditoria]` con una única sentencia parametrizada:
    ```sql
    SELECT a.id, a.turno_id, a.accion, a.usuario_id, u.username,
           a.ocurrio_en, a.antes, a.despues
    FROM auditoria_turno AS a
    LEFT JOIN usuario AS u ON u.id = a.usuario_id
    WHERE a.turno_id = ?
    ORDER BY a.ocurrio_en ASC, a.id ASC
    ```
  - `json.loads()` de `antes`/`despues` y `datetime.fromisoformat()` de `ocurrio_en` en esta capa.
  *Por qué:* `repositorio_turnos.py` y `api/turnos.py` quedan intactos y el merge con C-12/C-13 no toca la lectura. El `LEFT JOIN` es defensivo: el FK garantiza el usuario, pero así un dato huérfano no rompe la consulta.
  *Alternativa descartada:* agregar la función a `repositorio_turnos.py` — mezcla lectura de auditoría con escritura de turnos y genera conflicto con las ramas de C-12/C-13.

- **D5 — Desempate por `id` en el orden.**
  *Por qué:* `ocurrio_en` tiene precisión de segundos; crear, reprogramar y cancelar en un test pueden compartir segundo y el orden debe seguir siendo el de inserción. Sin el desempate, el escenario "3 registros en orden" es flaky y el contrato no es determinista.
  *Alternativa descartada:* ordenar solo por `ocurrio_en` — no garantiza estabilidad entre filas empatadas.

- **D6 — Router `app/api/auditoria.py` montado en `main.py`.**
  ```python
  @router.get("")
  def get_auditoria(
      turno_id: Annotated[int, Query(ge=1)],
      conexion: ConexionDep,
      usuario: Annotated[Usuario, Depends(requiere_rol(Rol.ADMINISTRACION))],
  ) -> AuditoriaResponse: ...
  ```
  - `Query(ge=1)` deja el `422` de ausencia/valor inválido en la frontera (regla dura 8).
  - `requiere_rol` se resuelve como dependencia: el `401/403` ocurre **antes** de que el handler consulte la base, así que un rol sin permiso no puede distinguir un turno existente de uno inexistente.
  - `404` con `NoEncontrado` (código `no_encontrado`) cuando `obtener_turno()` devuelve `None`.
  *Por qué:* replica exactamente el patrón de `GET /turnos/{id}` y `GET /agenda/*`; no hay lógica nueva que inventar.
  *Alternativa descartada:* verificar el turno en el repositorio de auditoría con un `EXISTS` — duplica la consulta y mezcla responsabilidades.

- **D7 — Contrato Pydantic de salida.**
  ```python
  class RegistroAuditoriaSalida(BaseModel):
      id: int
      turno_id: int
      accion: Literal["crear", "cancelar", "reprogramar"]
      usuario_id: int
      username: str | None
      ocurrio_en: str
      antes: dict[str, object] | None
      despues: dict[str, object]

  class AuditoriaResponse(BaseModel):
      turno_id: int
      registros: list[RegistroAuditoriaSalida]
  ```
  - `ocurrio_en` se serializa con `isoformat(timespec="seconds")`, igual que `TurnoResponse`.
  - `antes`/`despues` viajan como objetos: el cliente no recibe JSON escapado dentro de un string.
  - `username` es `str | None` para reflejar el `LEFT JOIN`.
  *Por qué:* el modelo explícito es la garantía de que ningún campo de `usuario` (hash, rol) ni del paciente se filtra por accidente; es el mismo mecanismo que protegió `password_hash` en C-07.
  *Alternativa descartada:* devolver `list[dict]` — sin contrato ni test de campos, y Pydantic no puede rechazar campos extra.

- **D8 — Envoltorio `{turno_id, registros}` en lugar de una lista pelada (confirmado por el equipo).**
  *Por qué:* deja espacio para metadatos futuros (p. ej. `total`) sin romper el contrato, y hace explícito a qué turno pertenece la respuesta. Es coherente con `AgendaResponse`, que también envuelve sus `items`.

- **D9 — Sin `transaccion()` ni escrituras.**
  *Por qué:* es un `SELECT` único sobre una conexión en autocommit; abrir `BEGIN IMMEDIATE` solo agregaría locks innecesarios. La tabla es append-only por trigger, así que la lectura no compite con escrituras de la misma fila.

- **D10 — Las rutas de escritura se cubren con tests, no con requirements nuevos.**
  *Por qué:* el requirement "Auditoría de solo agregado" ya exige que la API no exponga edición ni borrado, y su escenario ya acepta `404` o `405`. C-15 solo agrega tests que lo verifican sobre `/auditoria` (405) y `/auditoria/{id}` (404). Repetir el requirement sería duplicar el contrato.
  *Alternativa descartada:* un requirement nuevo "sin rutas de escritura" — redundante y propenso a divergir del existente.

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| C-12 y C-13 no están en `main` | Esperar a que estén mergeados en `main`; traerlos con `git merge origin/main` (sin rebase y sin mergear ramas ajenas que no estén en `main`) y verificar que el escenario de 3 registros corre contra el código real. |
| Divergencia futura del snapshot entre acciones | Test de contrato que compara las 8 claves de `antes`/`despues` en los tres registros; el requirement "Formato canónico del snapshot" ya lo exige. |
| `ocurrio_en` empatado en el mismo segundo | `ORDER BY ocurrio_en ASC, id ASC` y test con reloj fijo que fuerza el empate. |
| Fuga de `password_hash` por un `JOIN` futuro | Modelo Pydantic cerrado + test que recorre las claves de la respuesta y rechaza `password_hash`, `password`, `rol`, `dni`, `nombre`, `apellido`. |
| `json.loads` sobre un `TEXT` corrupto | Solo `snapshot_turno` escribe esas columnas; no se agrega recuperación defensiva para no ocultar un bug de escritura. Si apareciera, el `500` es la señal correcta. |
| Ordenar por texto ISO | El formato `YYYY-MM-DDTHH:MM:SS` es lexicográficamente equivalente al orden cronológico; no hace falta parsear para ordenar. |
| Consulta sin índice con muchos registros | Aceptado para el MVP; el volumen por turno es acotado. Índice futuro documentado en Open Questions. |
| Respuesta grande sin paginación | Aceptado: un turno tiene un puñado de registros y el endpoint exige `turno_id`. |

## Migration Plan

- No hay migración de datos ni de esquema.
- Despliegue: agregar los dos archivos nuevos y montar el router en `app/main.py`; el endpoint queda disponible sin tocar filas existentes.
- Rollback: quitar el `include_router` y borrar los archivos nuevos; la tabla y los registros de auditoría no se alteran.
- Orden de integración: esperar a que `C-12` y `C-13` estén mergeados en `main` y traerlos con `git merge origin/main` (sin rebase y sin mergear ramas ajenas que no estén en `main`), luego aplicar C-15, para que la suite pueda ejercitar los tres tipos de registro.

## Open Questions

- **IF-06:** retención y purga de auditoría. No afecta el contrato de C-15; se decide junto con la cátedra.
- **Índice `auditoria_turno(turno_id, ocurrio_en, id)`:** mejora futura si crece el volumen. Agregarlo después es aditivo porque el esquema se reaplica de forma idempotente.
