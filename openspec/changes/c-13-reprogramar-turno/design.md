# Design — C-13 reprogramar-turno

## 1. Arquitectura y Separación de Responsabilidades

Siguiendo las decisiones D-02 y las reglas duras de `AGENTS.md`, la solución mantiene desacopladas las tres capas principales:

```
[Cliente HTTP] 
      │ (JSON)
      ▼
[app/api/turnos.py] ────────► [app/db/repositorio_turnos.py]
      │                                    │
      │ (Pydantic, RBAC, reloj, tx)        │ (SQL parametrizado)
      ▼                                    ▼
[app/domain/reglas_turno.py]         [SQLite: turno + auditoria_turno]
      (Python Puro, sin DB/HTTP)
```

- **`app/domain/`**: Lógica pura e inmutable de validación (`validar_reprogramacion`). No importa FastAPI, ni SQL, ni bibliotecas externas. Recibe el reloj `ahora: datetime` explícitamente.
- **`app/db/`**: Acceso a datos con SQL parametrizado (`?`). Sus funciones se llaman dentro de la transacción que abre el router; no validan reglas de negocio.
- **`app/api/`**: Deserialización, autenticación, validación de esquemas (Pydantic), inyección de reloj, orquestación y apertura de la transacción (`with transaccion(conexion):`, SQLite `BEGIN IMMEDIATE`), que garantiza la atomicidad entre la actualización del turno y su auditoría (C-11 D1).

---

## 2. Dominio Puro (`app/domain/reglas_turno.py`)

### Firma
```python
def validar_reprogramacion(
    turno: Turno,
    nuevo_inicio: datetime,
    ahora: datetime,
    prestacion: Prestacion,
    horarios: Sequence[HorarioAtencion],
    bloqueos: Sequence[Bloqueo],
    turnos_activos: Sequence[Turno],
    nuevo_profesional_id: int | None = None,
    nuevo_sillon_id: int | None = None,
    nuevo_profesional: Profesional | None = None,
    nuevo_sillon: Sillon | None = None,
) -> Turno:
    ...
```

### Secuencia de Validación
1. **Validar estado activo (`RN-TUR-10`):**
   Si `turno.estado != "reservado"` (por ejemplo si ya fue `"cancelado"`), lanza `TurnoNoModificable("No se puede reprogramar un turno cancelado.")`.
2. **Validar temporalidad del turno actual (`RN-TUR-09`):**
   Si `not es_futuro(turno, ahora)` (es decir, `turno.inicio <= ahora`), lanza `TurnoNoModificable("Solo se pueden reprogramar turnos futuros.")`.
3. **Validar solo los recursos que cambian (`RN-REC-03`, C-11 D10):**
   - Si `nuevo_profesional_id is not None`: `nuevo_profesional` inexistente (`None`) o inactivo lanza `DatoInvalido` (→ 422).
   - Si `nuevo_sillon_id is not None`: `nuevo_sillon` inexistente (`None`) o inactivo lanza `DatoInvalido` (→ 422).
   - Un id enviado siempre se valida, aunque coincida con el recurso actual del turno. Los recursos que no se envían, la prestación y el paciente no se revalidan: un turno cuyo recurso vigente quedó inactivo se puede mover de horario sin cambiarlo.
   - `validar_recursos_alta` no se llama acá, porque exige los cuatro recursos. Se extraen de ella helpers privados de profesional y sillón, con los mismos mensajes y sin cambiar su comportamiento, y los usan ambas funciones.
4. **Determinar recursos y nuevo intervalo:**
   - `profesional_id = nuevo_profesional_id if nuevo_profesional_id is not None else turno.profesional_id`
   - `sillon_id = nuevo_sillon_id if nuevo_sillon_id is not None else turno.sillon_id`
   - El nuevo `fin` lo calcula `validar_alta` a partir de `prestacion` (`RN-TUR-01`).
5. **Validar disponibilidad en agenda (`RN-TUR-07`, `RN-TUR-08`):**
   Reutiliza `validar_alta` pasando `excluir_turno_id=turno.id`:
   - El nuevo horario debe estar íntegramente contenido en una franja de atención del profesional (`FueraDeHorario` → 409).
   - No debe superponerse con bloqueos del profesional ni del sillón (`DentroDeBloqueo` → 409).
   - No debe superponerse con otros turnos activos del profesional, del sillón ni del mismo paciente (`ConflictoAgenda` → 409). Se ignora el propio turno (`turno.id`) permitiendo cambios horarios contiguos o solapados con su franja anterior.
6. **Retorno:**
   Nueva instancia inmutable de `Turno`, a partir del candidato que devuelve `validar_alta`, conservando `id` y `estado`:
   ```python
   return replace(candidato, id=turno.id, estado=turno.estado)
   ```

---

## 3. Persistencia y Transaccionalidad (`app/db/`)

Para satisfacer `RN-AUD-01` y `RN-AUD-03`:
- Se define la función `reprogramar_turno(...)` en `app/db/repositorio_turnos.py`. **Precondición:** se llama dentro de la transacción que abre el router (C-11 D1); no abre una propia.
- Dentro de esa transacción:
  1. `UPDATE turno SET inicio = ?, fin = ?, profesional_id = ?, sillon_id = ? WHERE id = ?`, con fechas en `isoformat(timespec="seconds")` (C-11 D4).
  2. `registrar_auditoria(conexion, turno_id=..., accion="reprogramar", usuario_id=..., ocurrio_en=..., antes=snapshot_turno(turno_anterior), despues=snapshot_turno(turno_nuevo))`.
- `antes` y `despues` usan el snapshot canónico completo de 8 claves, incluido `estado` (C-11 D2).
- Si ocurre cualquier error antes o durante la escritura, se hace rollback y no queda rastro en `auditoria_turno`.

---

## 4. Capa API (`app/api/turnos.py`)

### Esquema de Entrada
```python
class ReprogramarTurnoRequest(BaseModel):
    nuevo_inicio: NaiveDatetime  # con offset o `Z` → 422 (C-11 D4)
    nuevo_profesional_id: int | None = None
    nuevo_sillon_id: int | None = None
```

### Endpoint
`POST /turnos/{id}/reprogramar`
- **Autorización:** `Depends(requiere_rol("administracion", "recepcion"))` (odontólogos reciben 403; no autenticados 401).
- **Reloj:** dependencia `obtener_ahora_local` (C-11 D3). El reloj UTC directo no sirve: `es_futuro` lanzaría `TypeError` al comparar un `datetime` con zona contra `turno.inicio`, que es naive.
- **Flujo de Ejecución** (toda la lectura y la validación ocurren dentro de la transacción, C-11 D1; así dos reprogramaciones al mismo hueco no pasan juntas):
  ```
  entrada (Pydantic: nuevo_inicio sin tz)                          → 422
  usuario = requiere_rol(ADMINISTRACION, RECEPCION)                → 401 / 403
  ahora_local = obtener_ahora_local
  with transaccion(conexion):                                      # BEGIN IMMEDIATE
      turno = obtener_turno(conexion, id)                          # None → HTTPException(404)
      profesional_id, sillon_id = nuevos si se enviaron, si no los del turno
      prestacion = obtener_prestacion_por_id(turno.prestacion_id)  # solo para la duración; no se valida si está activa
      nuevo_profesional, nuevo_sillon = obtener_*_por_id solo para los ids enviados
      horarios = listar_horarios_por_profesional_y_dia(profesional_id, nuevo_inicio.weekday())
      bloqueos = listar_bloqueos_de_recursos(profesional_id, sillon_id, desde=dia 00:00, hasta=dia+1 00:00)
      activos  = listar_turnos_activos_del_dia(dia, profesional_id, sillon_id, paciente_id)
      nuevo    = validar_reprogramacion(...)                       # dominio → 409 / 422 / 409 (ver orden abajo)
      reprogramar_turno(conexion, turno, nuevo, usuario_id=usuario.id, ocurrio_en=ahora_local)
  return 200 turno_a_response(nuevo)
  ```
- **404:** `HTTPException(status_code=404)`, que el handler global responde como `no_encontrado`. No se crea `TurnoNoEncontrado` (C-11 D5).
- **Respuesta:** `TurnoResponse` / `turno_a_response` de C-11 (D8).
- **Errores de dominio:** `TurnoNoModificable`, `ConflictoAgenda`, `FueraDeHorario` y `DentroDeBloqueo` los traduce a HTTP 409 el handler global; `DatoInvalido`, a HTTP 422.
- **Orden de validación de negocio**, una vez que el turno existe, fijado dentro de `validar_reprogramacion` y sin reglas en el router:
  1. Turno cancelado o pasado → 409 `TurnoNoModificable`.
  2. Recurso nuevo inexistente o inactivo → 422 `DatoInvalido`.
  3. Fuera de horario, bloqueo o conflicto de agenda → 409.
- **Contexto cargado antes de validar:** si el profesional nuevo no existe, sus horarios llegan vacíos, pero el dominio lanza `DatoInvalido` antes de usarlos. El router solo pasa datos; no decide sobre ellos.

---

## 5. Cumplimiento de Reglas Duras del Proyecto

- **Regla 1 (Aislamiento de dominio):** `app/domain/reglas_turno.py` no importa nada de `app/api/` ni `app/db/`.
- **Regla 2 (Reloj inyectado):** `validar_reprogramacion` recibe `ahora: datetime` explícitamente; ningún `datetime.now()` en dominio.
- **Regla 3 (Intervalos semiabiertos):** Los intervalos se evalúan como `[inicio, fin)`.
- **Regla 4 (Consultas parametrizadas):** Toda sentencia SQL utiliza parámetros `?`.
- **Regla 5 (Atomicidad de auditoría):** Turno y auditoría se escriben en la misma transacción (`RN-AUD-03`).
- **Regla 6 (Auditoría append-only):** Solo se hace `INSERT` en `auditoria_turno`.
- **Regla 7 (Errores consistentes):** Mapeo a HTTP 409, 422, 403, 401 y 404.
- **Regla 10 (Datos ficticios):** Nombres y datos de prueba rotulados como ficticios.
- **Regla 12 (Estilo):** Tipado estricto con anotaciones de tipo de Python 3.11 y `snake_case`.
