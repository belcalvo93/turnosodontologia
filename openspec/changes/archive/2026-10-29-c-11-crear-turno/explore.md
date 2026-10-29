# Explore — C-11 crear-turno

> Relevamiento previo al propose. También guardado en Engram (topic `opsx/c-11-crear-turno/explore`).
> Durante la exploración no se modificó ningún otro archivo del proyecto. Los designs de C-12, C-13 y C-14 **no se tocan**: los ajustes que les corresponden se listan en §5 para pasárselos a sus autores.

## 1. Qué pide C-11 (`CHANGES.md` §C-11)

| Ítem | Contenido |
|---|---|
| Tablas | `turno` (índices (`profesional_id`, `inicio`), (`sillon_id`, `inicio`), (`paciente_id`, `inicio`)) y `auditoria_turno` (solo `INSERT`) |
| Endpoints | `POST /turnos` (administración y recepción) y `GET /turnos/{id}` (autenticado, con RN-ACC-03) |
| Dominio | Reusa `validar_alta` de C-10 (`app/domain/reglas_turno.py`) |
| Errores | Conflicto, fuera de horario o bloqueo → `409`; recurso inexistente o inactivo, sin `sillon_id` → `422` (RN-GLO-01, RN-REC-03, RN-TUR-02) |
| Tests exigidos | `201` con estado `reservado` (RN-TUR-14), `409` por profesional y por sillón, contiguos aceptados, `422` con sillón inactivo, odontólogo creando → `403`, auditoría con usuario y fecha, doble reserva del mismo hueco → la segunda `409` (SE-06) |
| Dependencias | `C-06`, `C-08`, `C-09`, `C-10`; governance **CRÍTICO** |

## 2. Qué existe hoy en `main`

- `app/domain/models.py`: `Turno` (frozen, kw_only; sin `creado_por`/`creado_en`), `EstadoTurno = Literal["reservado", "cancelado"]`.
- `app/domain/reglas_turno.py`: `validar_alta(inicio, prestacion, profesional_id, sillon_id, paciente_id, horarios, bloqueos, turnos_activos, excluir_turno_id=None)` y `validar_reprogramacion(...)` (el dominio de C-13 ya está en `main`).
- `app/domain/errores.py`: `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`, `TurnoNoModificable`, `DatoInvalido`, ya mapeados en `app/api/errores.py` (409/422). El 404 se resuelve con `HTTPException(404)` → `no_encontrado`.
- `app/db/conexion.py`: `transaccion(conexion)` con `BEGIN IMMEDIATE`.
- `app/api/dependencias.py`: `obtener_conexion` y `obtener_ahora` (reloj inyectado, `app.state.reloj`; hoy devuelve `datetime.now(UTC)`, con zona).
- `app/db/repositorio_bloqueos.py`: fechas como `isoformat(timespec="seconds")` / `datetime.fromisoformat()`.

## 3. Contrato asumido por C-12, C-13 y C-14 (coincidencias)

| Contrato | C-12 | C-13 | C-14 | KB 04 |
|---|---|---|---|---|
| `turno` (id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado) | ✓ | ✓ | ✓ | ✓ |
| `auditoria_turno` (turno_id, accion, usuario_id, ocurrio_en, antes, despues) | ✓ | ✓ | — | ✓ |
| `estado` ∈ {`reservado`, `cancelado`} | ✓ | ✓ | ✓ | ✓ |
| `app/db/repositorio_turnos.py` + `app/api/turnos.py` | ✓ | ✓ | propios (`repositorio_agenda.py`, `agenda.py`) | — |

## 4. Decisiones tomadas

| # | Tema | Decisión |
|---|---|---|
| D1 | Dónde se valida y se escribe | La transacción se abre en el router (`app/api/turnos.py`) con `with transaccion(conexion):`; adentro se carga el contexto (repo, solo SQL), se llama a `validar_alta` (dominio puro) y se insertan turno + auditoría `crear`. Cubre la doble reserva (SE-06) y respeta `db → domain` solo tipos (regla dura 1) y la atomicidad (regla dura 5, RN-AUD-03) |
| D2 | Formato de `antes`/`despues` | C-11 define el formato canónico. En `crear`, `antes = NULL` (KB 04) y `despues` = snapshot completo del turno. Se fija en el design |
| D3 | Reloj | Nueva dependencia `obtener_ahora_local` en `app/api/dependencias.py`: usa `obtener_ahora` y `config.clinic_timezone` y devuelve un `datetime` local **sin `tzinfo`** (KB 04 §Convenciones). `obtener_ahora` queda igual (UTC, lo usa el JWT en `auth.py`). C-11 usa `obtener_ahora_local` para `ocurrio_en` y `creado_en` (ver D9: `validar_alta` no recibe `ahora`) |
| D4 | Formato de fechas | `inicio`, `fin`, `creado_en` y `ocurrio_en` con el mismo criterio que bloqueos (C-09): `isoformat(timespec="seconds")` al guardar, `datetime.fromisoformat()` al leer |
| D5 | 404 | Patrón actual: el repo devuelve `None` y el router responde `HTTPException(404)`. No se crean clases nuevas |
| D6 | Columnas de auditoría en `turno` | Se crean `creado_por` (FK `usuario`) y `creado_en`, porque están en KB 04 |
| D7 | RBAC de `GET /turnos/{id}` | RN-ACC-03: el odontólogo solo ve turnos de su `profesional_id`; uno de otro profesional → `403` (igual que C-14) |
| D8 | Nombres y piezas reutilizables | Repo: `crear_turno`, `obtener_turno`. Se exponen `TurnoResponse` (Pydantic) y la conversión fila → `Turno` para que C-12, C-13 y C-14 las reusen |

### Por qué D3 usa una dependencia aparte

`obtener_ahora` devuelve un instante **con zona UTC** (lo usa `auth.py` para el JWT), pero KB 04 §Convenciones exige fechas en hora local del consultorio **sin offset**, y `Turno.inicio` es naive local. Usarlo tal cual dejaría dos formatos mezclados en la base, y comparar `inicio` (naive) con `ahora` (aware) en `es_futuro` lanza `TypeError`. `obtener_ahora_local` resuelve la conversión en un único lugar inyectable, sin cambiar el reloj del JWT.

### D9 — `ahora` y `validar_alta` (resuelto)

`validar_alta` (C-10) **no recibe `ahora`** y C-11 **no la modifica**: C-10 lo dejó afuera a propósito, la KB no prohíbe crear turnos en el pasado y RN-TUR-09 aplica solo a cancelar y reprogramar. En C-11, `obtener_ahora_local` se usa únicamente para `creado_en` y `ocurrio_en`. Rechazar altas en el pasado queda como mejora futura (anotada en el design).

## 5. Ajustes para C-12/C-13/C-14 (borrador; pasa al design de C-11)

**C-12 cancelar-turno**
- Sacar la llamada a `validar_cancelacion` del repositorio: el router abre `with transaccion(conexion):`, usa `obtener_turno`, valida en el dominio y llama al repo para `UPDATE` + `INSERT` (D1).
- Unificar el nombre de la función del repo como `cancelar_turno` (el design usa `cancelar_turno_en_db` en D2 y `cancelar_turno` en el árbol).
- `antes`/`despues` con el snapshot completo de C-11, no solo `{"estado": ...}` (D2).
- Usar `obtener_ahora_local` en lugar de `request.app.state.reloj()` (D3). Así `es_futuro` compara hora local sin `tzinfo` contra `inicio`; se cae la mitigación del design de crear "un helper compartido" propio.
- Responder con el `TurnoResponse` de C-11 (D8).

**C-13 reprogramar-turno**
- Mover la carga de contexto y `validar_reprogramacion` **dentro** de la transacción del router (hoy valida fuera: dos reprogramaciones al mismo hueco pasan juntas) (D1).
- `antes`/`despues` con el snapshot completo de C-11, incluido `estado` (D2).
- Usar `obtener_ahora_local` en lugar de `request.app.state.reloj()` (D3); con el reloj UTC directo, `es_futuro` falla por mezclar naive y aware.
- 404 con `obtener_turno` → `None` → `HTTPException(404)`; eliminar `TurnoNoEncontrado` (D5).
- Actualizar en el design la firma de `validar_reprogramacion` a la que ya está en `main` (`prestacion`, `horarios`, `bloqueos`, `turnos_activos`).
- Responder con el `TurnoResponse` de C-11 (D8).

**C-14 agenda**
- 404 con el patrón `HTTPException(404)`; eliminar `ProfesionalNoEncontrado`/`SillonNoEncontrado` (D5).
- Reusar la conversión fila → `Turno` de C-11 en lugar de duplicar el mapeo (D8).
- `desde`/`hasta` como hora local sin offset y comparados con el formato de D4 (la comparación `inicio < ?` es lexicográfica sobre TEXT).
- Corregir en el texto el rango `[desde, hasta]` → `[desde, hasta)` (el SQL ya es semiabierto).

## 6. Fuentes consultadas

- `CHANGES.md` §C-11, §C-12, §Riesgos (SE-06, IF-06).
- `knowledge-base/04_modelo_de_datos.md` §Convenciones, §Turno, §AuditoriaTurno.
- `knowledge-base/05_reglas_de_negocio.md` §RN-TUR-02, §RN-TUR-14, §RN-REC-03, §RN-ACC-03, §RN-AUD-01/02/03.
- `openspec/changes/c-13-reprogramar-turno/design.md`, `openspec/changes/c-14-agenda/design.md`, `origin/bruno-c12-cancelar-turno:openspec/changes/c-12-cancelar-turno/design.md`.
- Repo: `app/domain/{models,reglas_turno,errores}.py`, `app/db/{conexion,esquema.sql,repositorio_bloqueos}.py`, `app/api/{dependencias,errores,bloqueos,auth}.py`, `app/main.py`.
