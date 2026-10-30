# Explore — C-12 cancelar-turno

> Relevamiento previo al propose. También guardado en Engram: `Exploración C-12 cancelar-turno` (topic `opsx/c-12-cancelar-turno/explore`).
> Durante la exploración no se creó ni modificó ningún otro archivo del proyecto.

## 1. Qué pide C-12 (`CHANGES.md` L352-366)

| Ítem | Contenido |
|---|---|
| Dominio | `app/domain/reglas_turno.py::validar_cancelacion(turno, ahora)`: turno futuro (`RN-TUR-09`) y no cancelado (`RN-TUR-10`) |
| Endpoint | `POST /turnos/{id}/cancelar` (administración y recepción): estado `cancelado` + auditoría con `antes`/`despues` en una transacción |
| Errores | Inexistente → **404**, pasado o en curso → **409**, ya cancelado → **409**, odontólogo → **403**, sin autenticar → **401** |
| Tests exigidos | Con reloj fijo (antes, igual, después); cancelar y volver a reservar el mismo hueco → **201** (`RN-TUR-06`); segunda cancelación → **409** |
| Dependencia | `C-11` (`crear-turno`), governance **ALTO** |

De la KB:
- **US-007 (`06_funcionalidades.md`):** como recepción, cancelar un turno futuro para liberar el horario del profesional y del sillón; el turno pasa a estado `cancelado` y deja de ocupar agenda; un turno pasado o ya cancelado no se puede cancelar; el horario liberado puede volver a reservarse; se registra auditoría de la cancelación.
- **Flujo 3 (`07_flujos_principales.md`):** `POST /turnos/{id}/cancelar` → carga el turno y valida permisos → el dominio verifica que sea futuro y que no esté ya cancelado (`RN-TUR-09`, `RN-TUR-10`) con hora actual inyectada → `app/db` marca el turno `cancelado` y agrega la auditoría (`antes`/`despues`) en una única transacción → el horario queda libre (`RN-TUR-06`).
- **Reglas (`05_reglas_de_negocio.md`):**
  - `RN-TUR-06`: cancelar un turno libera el horario (profesional, sillón y paciente quedan disponibles para ese intervalo).
  - `RN-TUR-08`: los turnos cancelados nunca generan conflicto en `validar_alta`.
  - `RN-TUR-09`: solo se pueden cancelar o reprogramar turnos futuros (`inicio > ahora`). Con `ahora = 09:00`, turno de las `10:00` es aceptado; de las `08:30` es rechazado; de las `09:00` exactas (en curso) es rechazado.
  - `RN-TUR-10`: un turno ya cancelado no se puede cancelar de nuevo (`409`).
  - `RN-AUD-01` y `RN-AUD-03`: toda cancelación registra auditoría (`accion = "cancelar"`, `usuario_id`, `ocurrio_en`, `antes`, `despues`) en la misma transacción; si la cancelación se rechaza (`409`), el turno no cambia y no se inserta auditoría.

## 2. Qué existe hoy y qué proveen C-02 / C-10 / C-11

**Ya existe (`C-10`)**
- `app/domain/models.py`: `Turno` con `estado: EstadoTurno = "reservado"` (`"reservado" | "cancelado"`).
- `app/domain/reglas_turno.py`: `validar_alta` ya ignora turnos cuyo `estado != "reservado"` (`L48: if turno.estado != "reservado" or es_excluido: continue`), lo que garantiza en dominio `RN-TUR-06` y `RN-TUR-08`.

**Provee `C-02` (`dominio-base`)**
- `TurnoNoModificable` en `app/domain/errores.py` (mapeado a HTTP `409`).
- `es_futuro(turno, ahora)` con reloj inyectado (`turno.inicio > ahora`).

**Provee `C-11` (`crear-turno`)**
- Tablas `turno` y `auditoria_turno` en `app/db/esquema.sql`.
- Router `app/api/turnos.py` con `POST /turnos` y `GET /turnos/{id}`, más las funciones de repositorio para turnos y auditoría.

**Falta implementar en `C-12`**
- `validar_cancelacion(turno: Turno, ahora: datetime) -> Turno` en `app/domain/reglas_turno.py`:
  1. Si `turno.estado == "cancelado"` → lanza `TurnoNoModificable("El turno ya está cancelado.")` (`RN-TUR-10`).
  2. Si `not es_futuro(turno, ahora)` (`turno.inicio <= ahora`) → lanza `TurnoNoModificable("Solo se pueden cancelar turnos futuros.")` (`RN-TUR-09`).
  3. Devuelve una copia del `Turno` con `estado="cancelado"`.
- Función transaccional en `app/db/` que lea el turno, invoque `validar_cancelacion`, haga `UPDATE turno SET estado = 'cancelado' WHERE id = ?` e `INSERT INTO auditoria_turno (turno_id, accion, usuario_id, ocurrio_en, antes, despues) VALUES (...)` dentro del mismo bloque `with transaccion(conexion):` (regla dura 5).
- Endpoint `POST /turnos/{id}/cancelar` en `app/api/turnos.py` protegido con `requiere_rol("administracion", "recepcion")` y reloj inyectado.

## 3. Riesgos y decisiones para el propose

| # | Riesgo / duda | Recomendación |
|---|---|---|
| 1 | **Reloj inyectado en dominio y en API (regla dura 2)** | `validar_cancelacion(turno, ahora)` recibe `ahora: datetime` (hora local del consultorio sin offset, coherente con `Turno.inicio`). En la API se obtiene el instante actual desde el reloj inyectado en la aplicación (`app.state.reloj`), permitiendo testear en API con reloj fijo antes (`08:30`), igual (`09:00`) y después (`10:00`) sin depender de `datetime.now()` |
| 2 | **Atomicidad de turno + auditoría (regla dura 5 y `RN-AUD-03`)** | Si `validar_cancelacion` lanza `TurnoNoModificable` (`409`), la transacción no ejecuta ningún `UPDATE` ni `INSERT` en `auditoria_turno`. Se verifica con un test explícito que tras un `409` la cantidad de filas en `auditoria_turno` permanece en 1 (solo la de creación) |
| 3 | **Coordinación con `C-13 reprogramar-turno` (Joaquín)** | `C-12` y `C-13` corren en el GATE 6 después de `C-11` y ambos agregan una función en `app/domain/reglas_turno.py` y una ruta en `app/api/turnos.py`. Mantener `validar_cancelacion` y `POST /turnos/{id}/cancelar` en bloques claramente delimitados al final de cada archivo facilita el merge |

## 4. Resumen

`C-12 cancelar-turno` cierra el ciclo de cancelación en el camino crítico (`C-11 → C-12 → C-15 → C-17`). Agrega `validar_cancelacion(turno, ahora)` en dominio puro (`RN-TUR-09`, `RN-TUR-10`), el endpoint `POST /turnos/{id}/cancelar` para administración y recepción que actualiza el estado a `cancelado` y registra la auditoría `cancelar` con valores `antes`/`despues` en una única transacción (`RN-AUD-01`, `RN-AUD-03`), y demuestra con tests de dominio y de API que el hueco liberado puede volver a reservarse (`RN-TUR-06`).

**Fuentes consultadas**

- `CHANGES.md` §C-12, §Camino crítico.
- `knowledge-base/07_flujos_principales.md` §Flujo 3.
- `knowledge-base/06_funcionalidades.md` §US-007.
- `knowledge-base/05_reglas_de_negocio.md` §RN-TUR-06, §RN-TUR-08, §RN-TUR-09, §RN-TUR-10, §RN-AUD-01, §RN-AUD-03.
- `knowledge-base/10_preguntas_abiertas.md` §SE-08, §SE-11.
- Repo: `app/domain/reglas_turno.py`, `app/domain/models.py`, `app/domain/errores.py`.
