# Design — C-13 reprogramar-turno

## 1. Arquitectura y Separación de Responsabilidades

Siguiendo las decisiones D-02 y las reglas duras de `AGENTS.md`, la solución mantiene desacopladas las tres capas principales:

```
[Cliente HTTP] 
      │ (JSON)
      ▼
[app/api/turnos.py] ────────► [app/db/repositorio_turnos.py]
      │                                    │
      │ (Pydantic / RBAC / Reloj)          │ (SQL Parametrizado, BEGIN IMMEDIATE)
      ▼                                    ▼
[app/domain/reglas_turno.py]         [SQLite: turno + auditoria_turno]
      (Python Puro, sin DB/HTTP)
```

- **`app/domain/`**: Lógica pura e inmutable de validación (`validar_reprogramacion`). No importa FastAPI, ni SQL, ni bibliotecas externas. Recibe el reloj `ahora: datetime` explícitamente.
- **`app/db/`**: Acceso a datos con SQL parametrizado (`?`) dentro de transacciones inmediatas (`with transaccion(conexion):`), garantizando atomicidad entre la actualización del turno y la creación del registro de auditoría.
- **`app/api/`**: Deserialización, autenticación, validación de esquemas (Pydantic), inyección de reloj y orquestación.

---

## 2. Dominio Puro (`app/domain/reglas_turno.py`)

### Firma
```python
def validar_reprogramacion(
    turno: Turno,
    nuevo_inicio: datetime,
    ahora: datetime,
    duracion_minutos: int,
    horarios_profesional: list[HorarioAtencion],
    bloqueos_profesional: list[Bloqueo],
    bloqueos_sillon: list[Bloqueo],
    turnos_existentes: list[Turno],
    nuevo_profesional_id: int | None = None,
    nuevo_sillon_id: int | None = None,
) -> Turno:
    ...
```

### Secuencia de Validación
1. **Validar estado activo (`RN-TUR-10`):**
   Si `turno.estado != "reservado"` (por ejemplo si ya fue `"cancelado"`), lanza `TurnoNoModificable("No se puede reprogramar un turno cancelado.")`.
2. **Validar temporalidad del turno actual (`RN-TUR-09`):**
   Si `not es_futuro(turno, ahora)` (es decir, `turno.inicio <= ahora`), lanza `TurnoNoModificable("Solo se pueden reprogramar turnos futuros.")`.
3. **Determinar recursos y nuevo intervalo:**
   - `profesional_id = nuevo_profesional_id if nuevo_profesional_id is not None else turno.profesional_id`
   - `sillon_id = nuevo_sillon_id if nuevo_sillon_id is not None else turno.sillon_id`
   - `nuevo_fin = nuevo_inicio + timedelta(minutes=duracion_minutos)` (`RN-TUR-01`).
4. **Validar disponibilidad en agenda (`RN-TUR-07`, `RN-TUR-08`):**
   Reutiliza `validar_alta` (o sus sub-funciones de validación) pasando `excluir_turno_id=turno.id`:
   - El nuevo horario debe estar íntegramente contenido en una franja de atención del profesional (`FueraDeHorario` → 409).
   - No debe superponerse con bloqueos del profesional ni del sillón (`DentroDeBloqueo` → 409).
   - No debe superponerse con otros turnos activos del profesional, del sillón ni del mismo paciente (`ConflictoAgenda` → 409). Se ignora el propio turno (`turno.id`) permitiendo cambios horarios contiguos o solapados con su franja anterior.
5. **Retorno:**
   Nueva instancia inmutable de `Turno` con los atributos actualizados:
   ```python
   return Turno(
       id=turno.id,
       paciente_id=turno.paciente_id,
       profesional_id=profesional_id,
       sillon_id=sillon_id,
       prestacion_id=turno.prestacion_id,
       inicio=nuevo_inicio,
       fin=nuevo_fin,
       estado=turno.estado,
   )
   ```

---

## 3. Persistencia y Transaccionalidad (`app/db/`)

Para satisfacer `RN-AUD-01` y `RN-AUD-03`:
- Se define la función `reprogramar_turno(...)` en el repositorio de turnos.
- Ejecuta una única transacción atómica `with transaccion(conexion):` (SQLite `BEGIN IMMEDIATE`):
  1. Serializa el estado anterior a JSON:
     `antes = json.dumps({"inicio": turno_anterior.inicio.isoformat(), "fin": turno_anterior.fin.isoformat(), "profesional_id": turno_anterior.profesional_id, "sillon_id": turno_anterior.sillon_id})`
  2. Serializa el estado posterior a JSON:
     `despues = json.dumps({"inicio": turno_nuevo.inicio.isoformat(), "fin": turno_nuevo.fin.isoformat(), "profesional_id": turno_nuevo.profesional_id, "sillon_id": turno_nuevo.sillon_id})`
  3. `UPDATE turno SET inicio = ?, fin = ?, profesional_id = ?, sillon_id = ? WHERE id = ?`
  4. `INSERT INTO auditoria_turno (turno_id, accion, usuario_id, ocurrio_en, antes, despues) VALUES (?, 'reprogramar', ?, ?, ?, ?)`
- Si ocurre cualquier error antes o durante la escritura, se hace rollback y no queda rastro en `auditoria_turno`.

---

## 4. Capa API (`app/api/turnos.py`)

### Esquema de Entrada
```python
class ReprogramarTurnoRequest(BaseModel):
    nuevo_inicio: datetime
    nuevo_profesional_id: int | None = None
    nuevo_sillon_id: int | None = None
```

### Endpoint
`POST /turnos/{id}/reprogramar`
- **Autorización:** `Depends(requiere_rol("administracion", "recepcion"))` (odontólogos reciben 403; no autenticados 401).
- **Reloj:** `ahora = request.app.state.reloj()` para garantizar inyección de tiempo.
- **Flujo de Ejecución:**
  1. Carga el turno por ID; si no existe → 404 (`TurnoNoEncontrado`).
  2. Valida la existencia y estado activo de `nuevo_profesional_id` (si se envió) y `nuevo_sillon_id` (si se envió); si alguno no existe o está inactivo → 422 (`DatoInvalido`).
  3. Carga prestación asociada al turno para obtener su duración en minutos.
  4. Carga horarios de atención, bloqueos y turnos existentes para el nuevo contexto.
  5. Invoca `validar_reprogramacion(...)`. Ante errores de dominio (`TurnoNoModificable`, `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`), el middleware global los traduce a HTTP 409.
  6. Ejecuta la transacción de persistencia y retorna el turno actualizado (HTTP 200).

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
