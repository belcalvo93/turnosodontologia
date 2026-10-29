# Design — C-11 crear-turno

## Context

Motivación y alcance en `proposal.md`; relevamiento y decisiones confirmadas (D1–D9) en `explore.md`. Requisitos observables en `specs/turnos/spec.md` y `specs/auditoria-turnos/spec.md`.

Estado de `main` que condiciona el diseño:
- `app/domain/reglas_turno.py::validar_alta(inicio, prestacion, profesional_id, sillon_id, paciente_id, horarios, bloqueos, turnos_activos, excluir_turno_id=None)` (C-10) ya calcula `fin`, valida franja, bloqueos y solapamientos (profesional, sillón, paciente) e ignora turnos no `reservado`. **No recibe `ahora` y no se modifica** (D9).
- `app/domain/models.py::Turno` es `frozen` y `kw_only`, sin `creado_por`/`creado_en`.
- `app/db/conexion.py::transaccion` usa `BEGIN IMMEDIATE`: toma el lock de escritura de SQLite al inicio del bloque.
- `app/api/dependencias.py::obtener_ahora` devuelve el reloj inyectado (`app.state.reloj`) **con zona UTC**; lo usa el JWT.
- Ya existen `obtener_prestacion_por_id`, `obtener_profesional_por_id`, `obtener_sillon_por_id`, `obtener_paciente_por_id` (devuelven `None` si no existe) y `listar_horarios_por_profesional_y_dia`.
- Fechas de bloqueos (C-09): `isoformat(timespec="seconds")` al guardar y `datetime.fromisoformat()` al leer.
- En Windows, `zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")` falla con `ZoneInfoNotFoundError` si no está el paquete `tzdata` (verificado en el entorno de desarrollo).
- Governance **CRÍTICO**: el apply avanza por checkpoints (ver `tasks.md`).

## Goals / Non-Goals

**Goals:**
- Validar y escribir turno + auditoría `crear` en una única transacción `BEGIN IMMEDIATE` (SE-06, RN-AUD-03, reglas duras 5).
- Mantener el dominio puro: el router orquesta, el repositorio solo hace SQL, las reglas viven en `app/domain/` (reglas duras 1, 8).
- Fijar contratos que `C-12`, `C-13` y `C-14` reutilizan: tablas, snapshot de auditoría, `obtener_ahora_local`, `TurnoResponse`, conversión fila → `Turno`, `obtener_turno`, `registrar_auditoria`.

**Non-Goals:**
- Modificar `validar_alta` o la dataclass `Turno`.
- Rechazar altas en el pasado (ver "Mejoras futuras").
- Pruebas de concurrencia con hilos reales: la garantía la da `BEGIN IMMEDIATE` (cubierto por `base-tecnica`); el test de doble reserva es secuencial, como pide `CHANGES.md`.
- Endpoints de lectura de auditoría (`C-15`) y auditoría de recursos (`IF-06`).

## Decisions

### D1 — La transacción vive en el router (confirmada)

`POST /turnos` en `app/api/turnos.py`:

```
entrada (Pydantic: tipos, campos obligatorios, inicio sin tz)  → 422
usuario = requiere_rol(ADMINISTRACION, RECEPCION)               → 401 / 403
ahora_local = obtener_ahora_local
with transaccion(conexion):                                     # BEGIN IMMEDIATE
    prestacion, profesional, sillon, paciente = repos existentes (obtener_*_por_id)
    prestacion = validar_recursos_alta(...)                     # dominio → DatoInvalido 422
    horarios   = listar_horarios_por_profesional_y_dia(profesional_id, inicio.weekday())
    bloqueos   = listar_bloqueos_de_recursos(profesional_id, sillon_id, desde=dia 00:00, hasta=dia+1 00:00)
    activos    = listar_turnos_activos_del_dia(dia, profesional_id, sillon_id, paciente_id)
    candidato  = validar_alta(...)                              # dominio → 409
    creado     = crear_turno(conexion, candidato, creado_por=usuario.id, creado_en=ahora_local)
return 201 turno_a_response(creado)
```

Cualquier excepción dentro del bloque hace `rollback` (no queda turno ni auditoría) y la mapea el handler global. Como la lectura del contexto ocurre **después** de tomar el lock de escritura, una segunda reserva del mismo hueco espera (`busy_timeout`) y luego ve el turno ya confirmado → `409` (SE-06).

*Alternativa descartada:* validar en el repositorio (como proponía el design de C-12). Rompe `db → domain` solo tipos (regla dura 1).

### D2 — Formato canónico de `antes`/`despues` (confirmada)

```json
{"id": 7, "paciente_id": 1, "profesional_id": 1, "sillon_id": 1, "prestacion_id": 1,
 "inicio": "2026-01-12T10:00:00", "fin": "2026-01-12T10:30:00", "estado": "reservado"}
```

- Exactamente esas 8 claves, en ese orden, generadas por `snapshot_turno(turno: Turno) -> str` en `app/db/repositorio_turnos.py` con `json.dumps(..., ensure_ascii=False)`. Fechas con `isoformat(timespec="seconds")`.
- `crear`: `antes = NULL`, `despues = snapshot` del turno ya con `id`.
- `cancelar` / `reprogramar` (C-12/C-13): `antes = snapshot` previo y `despues = snapshot` nuevo, siempre completos.
- `creado_por`/`creado_en` **no** van en el snapshot: son metadatos del alta y ya están en `usuario_id`/`ocurrio_en` del registro `crear`. El snapshot contiene solo ids, fechas y estado (sin datos personales).

*Alternativa descartada:* snapshot parcial con solo los campos cambiados (`{"estado": ...}` en C-12). Obliga a C-15 a reconstruir estados y cada change inventaría su formato.

### D3 — `obtener_ahora_local` (confirmada)

En `app/api/dependencias.py`:

```python
def a_hora_local(instante: datetime, zona: str) -> datetime:
    """Convierte un instante con zona a hora local de `zona`, sin tzinfo."""
    return instante.astimezone(ZoneInfo(zona)).replace(tzinfo=None)

def obtener_ahora_local(
    request: Request, ahora: Annotated[datetime, Depends(obtener_ahora)]
) -> datetime:
    return a_hora_local(ahora, request.app.state.config.clinic_timezone)
```

- `a_hora_local` es una función pura testeable sin HTTP ni DB; `obtener_ahora_local` es la dependencia inyectable.
- `obtener_ahora` sigue devolviendo UTC con zona (JWT). Si el reloj devolviera un `datetime` naive, `astimezone` lo interpretaría como hora local del sistema: se documenta en el docstring que el reloj **debe** devolver un instante con zona (como hoy `_hora_real` y `RelojFijo`).
- En C-11 se usa solo para `creado_en` y `ocurrio_en` (D9).
- **Supuesto S1 — `tzdata`:** se agrega `tzdata` a `requirements.txt` sin marcador de plataforma (en Linux no molesta y garantiza la misma base de zonas en todos los entornos).

### D4 — Formato de fechas (confirmada)

`inicio`, `fin`, `creado_en` y `ocurrio_en` se guardan con `isoformat(timespec="seconds")` y se leen con `datetime.fromisoformat()`. El orden lexicográfico del texto coincide con el cronológico, lo que permite comparar en SQL (`inicio < ?`).

**Supuesto S2 — `inicio` con zona → 422 en la frontera:** `CrearTurnoRequest.inicio` se tipa con `pydantic.NaiveDatetime`. Un `inicio` con offset o `Z` lo rechaza Pydantic → `RequestValidationError` → `422 dato_invalido` con `detalles[campo=inicio]`. Es validación de formato de entrada (regla dura 8: Pydantic en la frontera), no regla de negocio; evita agregar parámetros a `validar_alta`. Resultado observable igual al de bloqueos (`422`).

### D5 — 404 (confirmada)

`obtener_turno(conexion, turno_id) -> Turno | None`; el router lanza `HTTPException(status_code=404)` y el handler global responde `no_encontrado`. No se crean errores nuevos.

### D6 — `creado_por` y `creado_en` solo en la base (confirmada; elección de alcance)

Se agregan a la tabla `turno` (KB 04) y los escribe `crear_turno`, pero **la dataclass `Turno` no cambia**: son metadatos de trazabilidad, no participan de ninguna regla de dominio, y agregarlos obligaría a tocar `validar_alta`/`validar_reprogramacion` y sus tests (C-10/C-13) o a dejarlos opcionales con `None`, lo que debilita el tipo. `TurnoResponse` tampoco los expone (**Supuesto S3**): el "quién y cuándo" se consulta por auditoría (`C-15`).

### D7 — RBAC (confirmada)

- `POST /turnos`: `requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION)` → odontólogo `403`, sin token `401`.
- `GET /turnos/{id}`: `usuario_actual`; primero se busca el turno (`404` si no existe, para todos los roles) y luego `puede_ver_turno(usuario, turno)`; si es `False` → `SinPermiso` (`403`).
- **Supuesto S4 — `puede_ver_turno` en dominio:** `app/domain/usuarios.py::puede_ver_turno(usuario: Usuario, turno: Turno) -> bool`: `True` para administración y recepción; para odontólogo, `usuario.profesional_id is not None and usuario.profesional_id == turno.profesional_id`. Es regla de negocio (RN-ACC-03), testeable sin HTTP, y `C-14` puede reutilizar el mismo criterio.
- Orden 404 antes de 403: el id de turno no es dato sensible; se prioriza un error coherente para todos los roles.

### D8 — Piezas reutilizables (confirmada)

`app/db/repositorio_turnos.py` (solo SQL parametrizado; importa solo tipos de `app.domain`):

| Función | Uso |
|---|---|
| `COLUMNAS_TURNO` + `turno_desde_fila(fila) -> Turno` | conversión fila → `Turno` (C-12, C-13, C-14) |
| `obtener_turno(conexion, turno_id) -> Turno \| None` | GET, C-12, C-13 |
| `listar_turnos_activos_del_dia(conexion, *, dia, profesional_id, sillon_id, paciente_id) -> list[Turno]` | contexto de alta (y C-13) |
| `snapshot_turno(turno) -> str` | formato D2 |
| `registrar_auditoria(conexion, *, turno_id, accion, usuario_id, ocurrio_en, antes, despues) -> None` | C-11 (`crear`), C-12, C-13 |
| `crear_turno(conexion, turno, *, creado_por, creado_en) -> Turno` | INSERT turno + `registrar_auditoria("crear")` |

- `AccionAuditoria = Literal["crear", "cancelar", "reprogramar"]` se define en el repositorio.
- **Supuesto S5 — `crear_turno` escribe turno y auditoría juntos:** así ningún llamador puede insertar un turno sin su registro `crear`. Precondición documentada: se llama dentro de `transaccion(...)`; la atomicidad la da la transacción del router.
- `listar_turnos_activos_del_dia`: `estado = 'reservado' AND (profesional_id = ? OR sillon_id = ? OR paciente_id = ?) AND inicio < ? AND fin > ?` con la ventana `[dia 00:00, dia+1 00:00)`. **Supuesto S6:** se filtra por el día del `inicio` y no por el intervalo exacto porque el `fin` lo calcula el dominio (RN-TUR-01) después; un turno no puede cruzar de día porque debe entrar en una franja. El dominio sigue siendo quien decide el solapamiento.
- **Supuesto S7 — consulta de bloqueos en `repositorio_bloqueos.py`:** se agrega `listar_bloqueos_de_recursos(conexion, *, profesional_id, sillon_id, desde, hasta) -> list[Bloqueo]` con `((alcance = 'profesional' AND recurso_id = ?) OR (alcance = 'sillon' AND recurso_id = ?)) AND inicio < ? AND fin > ?`, reutilizando `_bloqueo_desde_fila`. Los bloqueos pueden abarcar varios días (vacaciones), por eso se filtra por intersección con la ventana del día.

`app/api/turnos.py`: `CrearTurnoRequest` (entrada), `TurnoResponse` (`id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio: str`, `fin: str`, `estado: EstadoTurno`) y `turno_a_response(turno) -> TurnoResponse` (fechas `isoformat(timespec="seconds")`, igual que `BloqueoSalida`).

### D9 — `validar_alta` sin `ahora` (confirmada)

No se modifica. `obtener_ahora_local` se usa únicamente para `creado_en` y `ocurrio_en`. Resuelve la contradicción de `explore.md` (D3 menciona "el `ahora` de la validación de alta"; prevalece D9).

### D10 — Recursos inexistentes o inactivos en dominio (Supuesto S8)

`app/domain/reglas_turno.py::validar_recursos_alta(prestacion: Prestacion | None, profesional: Profesional | None, sillon: Sillon | None, paciente: Paciente | None) -> Prestacion` (función nueva; `validar_alta` intacta). Lanza `DatoInvalido` con mensajes en español en este orden: prestación inexistente / inactiva, profesional inexistente / inactivo, sillón inexistente / inactivo, paciente inexistente. Devuelve la prestación no nula para pasarla a `validar_alta`. RN-REC-03 es regla de negocio → dominio (regla dura 8), no un `if` en el router. Tests en un archivo nuevo (`tests/domain/test_recursos_alta.py`) para no chocar con los cambios de C-12/C-13 en `test_reglas_turno.py`.

*Alternativa descartada:* que el repositorio lance `DatoInvalido` (patrón de `crear_bloqueo`). Mezcla la regla de "activo" con SQL.

### D11 — Esquema SQLite

En `app/db/esquema.sql`, después de `bloqueo`:

```sql
-- Turnos (C-11, KB 04 §Turno, RN-TUR-02/14). Fechas: hora local sin offset (D4).
CREATE TABLE IF NOT EXISTS turno (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id    INTEGER NOT NULL REFERENCES paciente(id),
    profesional_id INTEGER NOT NULL REFERENCES profesional(id),
    sillon_id      INTEGER NOT NULL REFERENCES sillon(id),
    prestacion_id  INTEGER NOT NULL REFERENCES prestacion(id),
    inicio         TEXT    NOT NULL,
    fin            TEXT    NOT NULL,
    estado         TEXT    NOT NULL DEFAULT 'reservado'
                           CHECK (estado IN ('reservado', 'cancelado')),
    creado_por     INTEGER NOT NULL REFERENCES usuario(id),
    creado_en      TEXT    NOT NULL,
    CHECK (inicio < fin)
);

CREATE INDEX IF NOT EXISTS idx_turno_profesional_inicio ON turno (profesional_id, inicio);
CREATE INDEX IF NOT EXISTS idx_turno_sillon_inicio      ON turno (sillon_id, inicio);
CREATE INDEX IF NOT EXISTS idx_turno_paciente_inicio    ON turno (paciente_id, inicio);

-- Auditoría de turnos (C-11, KB 04 §AuditoriaTurno, RN-AUD-01/02). Solo INSERT.
CREATE TABLE IF NOT EXISTS auditoria_turno (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    turno_id   INTEGER NOT NULL REFERENCES turno(id),
    accion     TEXT    NOT NULL CHECK (accion IN ('crear', 'cancelar', 'reprogramar')),
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    ocurrio_en TEXT    NOT NULL,
    antes      TEXT    NULL,
    despues    TEXT    NOT NULL
);

CREATE TRIGGER IF NOT EXISTS auditoria_turno_sin_update
    BEFORE UPDATE ON auditoria_turno
BEGIN
    SELECT RAISE(ABORT, 'auditoria_turno es de solo agregado');
END;

CREATE TRIGGER IF NOT EXISTS auditoria_turno_sin_delete
    BEFORE DELETE ON auditoria_turno
BEGIN
    SELECT RAISE(ABORT, 'auditoria_turno es de solo agregado');
END;
```

- `REFERENCES usuario(id)`: la tabla `usuario` existe desde C-03 (su propia columna `profesional_id` no tiene FK, pero eso no afecta a estas).
- **Supuesto S9 — triggers append-only:** RN-AUD-02 se refuerza en la base (además de no exponer rutas). `RAISE(ABORT, ...)` llega a Python como `sqlite3.IntegrityError`. No se agrega índice sobre `auditoria_turno`: lo decide `C-15` según su consulta.
- `CHECK (inicio < fin)` compara texto ISO; vale por el formato uniforme de D4.

### Estructura resultante

```
app/
├── main.py                       # + include_router(router_turnos)
├── api/
│   ├── dependencias.py           # + a_hora_local, obtener_ahora_local
│   └── turnos.py                 # NUEVO: POST /turnos, GET /turnos/{id}, TurnoResponse
├── db/
│   ├── esquema.sql               # + turno, auditoria_turno, índices, triggers
│   ├── repositorio_bloqueos.py   # + listar_bloqueos_de_recursos
│   └── repositorio_turnos.py     # NUEVO (ver D8)
└── domain/
    ├── reglas_turno.py           # + validar_recursos_alta (validar_alta intacta)
    └── usuarios.py               # + puede_ver_turno
requirements.txt                  # + tzdata
tests/
├── domain/test_recursos_alta.py  # NUEVO
├── domain/test_permisos_turno.py # NUEVO
├── api/test_hora_local.py        # NUEVO
├── api/test_repositorio_turnos.py# NUEVO (esquema, repo, atomicidad, append-only)
├── api/test_repositorio_bloqueos.py # + tests de listar_bloqueos_de_recursos
└── api/test_turnos.py            # NUEVO (API)
```

## Ajustes para C-12/C-13/C-14

Los designs de esos changes **no se modifican desde C-11**. Esta es la lista que su autor debe aplicar antes de su `/opsx:apply`.

**C-12 cancelar-turno**
- Sacar `validar_cancelacion` del repositorio: el router abre `with transaccion(conexion):`, llama a `obtener_turno` (`None` → `HTTPException(404)`), valida en el dominio y recién después llama al repositorio para el `UPDATE` + `registrar_auditoria(accion="cancelar")` (D1, regla dura 1).
- Unificar el nombre de la función del repo como `cancelar_turno` (su design usa `cancelar_turno_en_db` en D2 y `cancelar_turno` en el árbol).
- `antes`/`despues` con `snapshot_turno` completo (las 8 claves de D2), no solo `{"estado": ...}`.
- Usar la dependencia `obtener_ahora_local` en lugar de `request.app.state.reloj()` (D3): así `es_futuro` compara hora local sin `tzinfo` contra `turno.inicio`. Se cae la mitigación de crear "un helper compartido" propio.
- Responder con `TurnoResponse` / `turno_a_response` de C-11 (D8).

**C-13 reprogramar-turno**
- Mover la carga de contexto y `validar_reprogramacion` **dentro** de la transacción del router (su design valida afuera: dos reprogramaciones al mismo hueco pasarían juntas) (D1).
- `antes`/`despues` con `snapshot_turno` completo, incluido `estado` (D2); hoy su design omite `id`, `paciente_id`, `prestacion_id` y `estado`.
- Usar `obtener_ahora_local` en lugar de `request.app.state.reloj()` (D3); con el reloj UTC directo, `es_futuro` lanza `TypeError` al comparar naive con aware.
- 404 con `obtener_turno` → `None` → `HTTPException(404)`; eliminar `TurnoNoEncontrado` (D5).
- Validar existencia/actividad de `nuevo_profesional_id`/`nuevo_sillon_id` con `validar_recursos_alta` (D10) en lugar de lógica propia en el router.
- Cargar el contexto con `listar_turnos_activos_del_dia` y `listar_bloqueos_de_recursos` (D8) y usar `nuevo_inicio` con `NaiveDatetime` (D4).
- Actualizar en su design la firma de `validar_reprogramacion` a la que ya está en `main` (`prestacion`, `horarios`, `bloqueos`, `turnos_activos`).
- Responder con `TurnoResponse` de C-11 (D8).

**C-14 agenda**
- 404 con el patrón `HTTPException(404)`; eliminar `ProfesionalNoEncontrado`/`SillonNoEncontrado` (D5).
- Reusar `COLUMNAS_TURNO` + `turno_desde_fila` de C-11 en lugar de duplicar el mapeo (D8).
- `desde`/`hasta` como hora local sin offset (`NaiveDatetime`) y serializados con el formato de D4 antes de compararlos en SQL (la comparación `inicio < ?` es lexicográfica sobre TEXT).
- Corregir en el texto el rango `[desde, hasta]` → `[desde, hasta)` (el SQL ya es semiabierto).
- Puede reutilizar el criterio de `puede_ver_turno` (D7) para RN-ACC-03.

## Mejoras futuras

- **Rechazar altas en el pasado (D9).** Hoy `POST /turnos` acepta un `inicio` anterior al momento actual: la KB no lo prohíbe y RN-TUR-09 aplica solo a cancelar y reprogramar. Si se decide prohibirlo, se agrega una regla de dominio que reciba `ahora` (de `obtener_ahora_local`) y lance `TurnoNoModificable` o `DatoInvalido`; requiere nueva RN en la KB y un change propio.
- Índice sobre `auditoria_turno (turno_id)` cuando `C-15` defina su consulta.

## Risks / Trade-offs

- **[Lock de escritura durante la lectura del contexto]** → Aceptado: `BEGIN IMMEDIATE` serializa todas las altas (un escritor a la vez, D-01). Con la escala del MVP (SE-16) las transacciones duran milisegundos; `busy_timeout=5000` absorbe la espera.
- **[Microsegundos en `inicio`]** → `isoformat(timespec="seconds")` trunca; un `inicio` con fracciones se validaría con un valor y se guardaría con otro. Mitigación: los clientes envían minutos exactos; mismo criterio aceptado en C-09. Si aparece, se normaliza en la frontera.
- **[`tzdata` como dependencia nueva]** → Paquete oficial de la PSF sin dependencias. Sin él, `obtener_ahora_local` falla en Windows en cada alta.
- **[Reloj naive]** → `astimezone` sobre naive usaría la zona del sistema. Mitigación: contrato documentado de `obtener_ahora` (siempre con zona) y test con `RelojFijo` (UTC).
- **[Divergencia con C-12/C-13/C-14 ya propuestos]** → Mitigación: sección "Ajustes para C-12/C-13/C-14", a comunicar a sus autores antes de su apply.
- **[Triggers en un esquema sin migraciones]** → `CREATE TRIGGER IF NOT EXISTS` es idempotente; una base de desarrollo previa no tiene las tablas, así que se crean completas.

## Migration Plan

Las tablas, índices y triggers se crean con `IF NOT EXISTS` al arrancar (`inicializar_esquema`). No hay datos previos de turnos. Instalar dependencias de nuevo (`pip install -r requirements.txt`) por `tzdata`. Rollback: revertir el merge del change (las tablas nuevas no son referenciadas por tablas anteriores).

## Open Questions

Ninguna que cambie specs o tareas. Rechazar altas en el pasado queda como mejora futura.
