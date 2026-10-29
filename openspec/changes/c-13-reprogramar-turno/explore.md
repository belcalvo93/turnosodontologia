# Explore — C-13 reprogramar-turno

> Relevamiento previo al propose. Guardado en el repositorio para trazabilidad del equipo.
> Durante la exploración no se modificó código de la aplicación.

## 1. Qué pide C-13 (`CHANGES.md` L367-382)

| Ítem | Contenido |
|---|---|
| Dominio | `app/domain/reglas_turno.py::validar_reprogramacion(...)`: turno futuro y activo, recalcula fin según duración de la prestación y reutiliza `validar_alta` excluyendo el propio `turno.id` (`RN-TUR-07`, `RN-TUR-08`). |
| Endpoint | `POST /turnos/{id}/reprogramar` con nuevo inicio y, opcionalmente, nuevo profesional y/o sillón; mantiene el mismo `turno_id` (`D-05`, `SE-21`). |
| Auditoría | Acción `reprogramar` con valores `antes`/`despues` en una sola transacción (`RN-AUD-01`); si se rechaza, no cambia el turno ni se audita (`RN-AUD-03`). |
| Errores | Horario ocupado, fuera de horario o dentro de bloqueo → **409**; cancelado o pasado → **409**; turno inexistente → **404**; recursos inexistentes o inactivos → **422**; odontólogo → **403**; sin autenticar → **401**. |
| Tests exigidos | Mover sobre su propio horario anterior aceptado (`RN-TUR-08`); horario ocupado por otro turno → 409 sin nuevo registro de auditoría (`RN-AUD-03`); cancelado o pasado → 409; conservación de `turno_id`. |
| Dependencia | `C-11` (`crear-turno`), governance **ALTO**. |

### Relevamiento desde la Base de Conocimiento (KB)

- **US-008 (`06_funcionalidades.md`):** Como recepción o administración, reprogramar un turno para moverlo a otro horario (y opcionalmente a otro profesional o sillón) sin tener que cancelarlo y crear uno nuevo. Criterios: conserva su identificador (`D-05`), se aplican las mismas reglas de solapamiento, horario y bloqueo que al crear (`RN-TUR-07`), y si el nuevo horario es inválido responde 409 dejando el turno intacto.
- **Flujo 4 (`07_flujos_principales.md`):** `POST /turnos/{id}/reprogramar` → la API carga el turno y el contexto del nuevo intervalo → el dominio verifica que el turno sea futuro y esté activo (`RN-TUR-09`, `RN-TUR-10`), recalcula el fin con la prestación y valida la agenda excluyendo al propio turno (`RN-TUR-07`, `RN-TUR-08`) → si es válido, `app/db` actualiza el turno y registra la auditoría con `antes`/`despues` en una única transacción.
- **Reglas de Negocio (`05_reglas_de_negocio.md`):**
  - `RN-TUR-01`: La duración del turno coincide con la duración de la prestación asignada (`fin = inicio + timedelta(minutes=duracion_minutos)`).
  - `RN-TUR-07`: Reprogramar conserva el mismo `turno_id` y exige validar disponibilidad exactamente igual que al crear.
  - `RN-TUR-08`: Al validar solapamiento, el turno que se reprograma no cuenta como conflicto consigo mismo (`excluir_turno_id=turno.id`). Los turnos cancelados nunca generan conflicto.
  - `RN-TUR-09`: Solo se pueden reprogramar turnos futuros (`inicio > ahora`). Si el turno ya comenzó o está en el pasado, se rechaza con `TurnoNoModificable` (HTTP 409).
  - `RN-TUR-10`: Un turno ya cancelado no se puede reprogramar (HTTP 409).
  - `RN-AUD-01` y `RN-AUD-03`: Toda reprogramación exitosa genera auditoría con valores antes y después. Si la reprogramación se rechaza, el turno queda inalterado y no se escribe auditoría (atomicidad estricta).
- **Decisiones y Supuestos (`09_decisiones_y_supuestos.md` y `10_preguntas_abiertas.md`):**
  - `D-05` / `SE-21`: Se decidió que reprogramar actualiza el turno existente in-place conservando su identificador estable y trazabilidad lineal, en lugar de encadenar turnos nuevos.

---

## 2. Estado Actual del Código y Dependencias

### Ya implementado en el repositorio
- **`C-02` (`dominio-base`):**
  - Modelos inmutables en `app/domain/models.py`: `Turno`, `HorarioAtencion`, `Bloqueo`.
  - Primitiva `solapan(a, b)` con intervalos semiabiertos `[inicio, fin)`.
  - Excepciones de dominio: `TurnoNoModificable`, `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`, `DatoInvalido`.
  - Reloj inyectable: `es_futuro(turno, ahora)`.
- **`C-10` (`reglas-alta-turno`):**
  - `validar_alta(prestacion, horarios, bloqueos, turnos_existentes, inicio, profesional_id, sillon_id, paciente_id, excluir_turno_id=None)` en `app/domain/reglas_turno.py`.
  - Soporta el parámetro `excluir_turno_id`, ignorando el turno coincidente para evitar falsos positivos de solapamiento.
- **`C-08` (`horarios-atencion`):**
  - Tabla `horario_atencion` y consultas de franjas por profesional y día de la semana.

### Que proveerá `C-11` (`crear-turno`)
- Tablas SQLite `turno` y `auditoria_turno`.
- Router `app/api/turnos.py` con `POST /turnos` y `GET /turnos/{id}`.
- Funciones de base de datos para cargar un turno por id y registrar auditoría.

### Lo que agregará `C-13`
1. **Dominio puro (`app/domain/reglas_turno.py`):**
   - Función `validar_reprogramacion(...)`:
     - Verifica que `turno.estado == "reservado"` (si es cancelado → `TurnoNoModificable`).
     - Verifica que `es_futuro(turno, ahora)` (si es pasado o presente → `TurnoNoModificable`).
     - Determina el nuevo profesional y sillón (usa los provistos o mantiene los actuales).
     - Recalcula `nuevo_fin = nuevo_inicio + timedelta(minutes=duracion_minutos)`.
     - Invoca `validar_alta(..., excluir_turno_id=turno.id)` con el nuevo intervalo.
     - Retorna el nuevo `Turno` con los datos actualizados y el mismo `id`.
2. **Capa de Persistencia (`app/db/`):**
   - Repositorio de turnos: función para actualizar turno y guardar auditoría atómicamente (`UPDATE turno ...` + `INSERT INTO auditoria_turno ...`) dentro del context manager `transaccion(conexion)`.
3. **Capa API (`app/api/turnos.py`):**
   - Endpoint `POST /turnos/{id}/reprogramar`.
   - Esquemas Pydantic `ReprogramarTurnoRequest` y `TurnoResponse`.
   - Dependencias de autorización: `requiere_rol("administracion", "recepcion")`.
   - Inyección de reloj desde `app.state.reloj`.

---

## 3. Riesgos Técnicos y Mitigaciones

| # | Riesgo / Desafío | Mitigación |
|---|---|---|
| 1 | **Dependencia de C-11 (`crear-turno`)** | C-13 espera la creación de tablas en C-11 para la integración con base de datos. Sin embargo, toda la lógica de dominio puro (`validar_reprogramacion`) y sus tests unitarios se pueden implementar y probar de forma completamente aislada ahora mismo (Strict TDD de dominio). |
| 2 | **Regla dura 2: Reloj inyectado** | `validar_reprogramacion` recibe obligatoriamente `ahora: datetime` como parámetro sin consultar `datetime.now()`. En la API se inyecta desde `app.state.reloj(request)`. |
| 3 | **Regla dura 5: Atomicidad de auditoría (`RN-AUD-03`)** | Si la reprogramación falla por cualquier regla de negocio (conflicto de horario, bloqueo, etc.), se propaga la excepción HTTP 409 y se produce rollback; no se registra ninguna fila en `auditoria_turno`. Se valida mediante tests que comparan el conteo de filas de auditoría. |
| 4 | **Reprogramación parcial (cambio solo de horario, o también de profesional/sillón)** | El request permite `nuevo_inicio` obligatorio, y `nuevo_profesional_id` / `nuevo_sillon_id` opcionales. Si se omiten, se conservan los recursos asignados previamente. |
| 5 | **Moverse sobre su propio intervalo previo (`RN-TUR-08`)** | Al mover por ejemplo un turno de 10:00-10:30 a 10:15-10:45, existe solapamiento físico en [10:15, 10:30), pero al excluir `turno.id`, el sistema no debe rechazar la operación. |

---

## 4. Resumen y Siguientes Pasos

`C-13` completa la funcionalidad crítica de modificación de turnos del MVP (`US-008`, `RN-TUR-07`, `RN-TUR-08`, `D-05`). 
Procedemos a formalizar la propuesta (`proposal.md`), el diseño técnico (`design.md`), las tareas desglosadas (`tasks.md`) y la especificación ejecutable con escenarios Dado/Cuando/Entonces (`specs/reprogramar-turno/spec.md`).
