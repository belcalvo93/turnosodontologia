# Design — C-16 bloqueos-turnos-afectados

Contexto: `explore.md` de este change. El código real en `main` ya incluye `C-09` (bloqueos) y `C-11` (turnos); este design solo decide **cómo** reportar los turnos afectados al crear un bloqueo.

## Decisions

### D-A1 — Resolución de `SE-09`: solo LISTAR los turnos afectados (decidida)

> **DECIDIDO el 2026-10-29 por Belén Calvo, responsable de C-16**, ante la falta de respuesta del grupo y siguiendo la propuesta MVP de `CHANGES.md` y `US-005`. **Revisión:** decisión revisable; si el grupo propone otra opción (rechazo con `409` o cancelación en cascada) antes o después del apply, el scope se reemplaza con un change nuevo que parta de este comportamiento.

- Crear un bloqueo **solo lista** los turnos `reservado` afectados: no se cancelan, no se modifican y **no se escribe en `auditoria_turno`** (ningún turno fue creado, reprogramado ni cancelado; `IF-06` deja fuera la auditoría de bloqueos).
- La cancelación de un turno afectado queda en `C-12` (y la reprogramación en `C-13`); recepción usa la lista para contactar a los pacientes.
- Se descartan para este MVP: Opción B (cancelación en cascada con auditoría — acopla con `C-12`, define tratamiento de turnos pasados y sube governance a ALTO) y Opción C (rechazo con `409` — impide bloquear rápido ante una urgencia).
- El governance de `C-16` queda en **MEDIO** (solo lectura de turnos; ningún `UPDATE` ni `DELETE`).

### D-A2 — Contrato JSON de `POST /bloqueos` plano y aditivo (confirmada por Bruno)

- La respuesta de `POST /bloqueos` mantiene su forma plana actual (`id, alcance, recurso_id, inicio, fin, motivo`) y **suma `turnos_afectados` al mismo nivel** (no se anida bajo `{"bloqueo": …}`, no se envuelve).
- Nuevo schema de salida **solo en `POST`**: `BloqueoCreadoSalida(BloqueoSalida)` con `turnos_afectados: list[TurnoResponse]`. `GET /bloqueos` sigue devolviendo `[BloqueoSalida]` sin el campo (evita consultas N+1 en el listado).
- Tests de `C-09`: solo se edita la aserción de igualdad exacta sobre la respuesta de `POST /bloqueos` en `tests/api/test_bloqueos.py` para incluir `"turnos_afectados": []` (aprobado por el usuario). El resto de los tests de `C-09` y todos los que prueban `GET`/`DELETE /bloqueos` no se tocan.

### D-A3 — Reportar todos los turnos `reservado` solapados, sin reloj

- Se reportan **todos** los turnos con `estado = 'reservado'` cuyo intervalo se solape con `[bloqueo.inicio, bloqueo.fin)` para el recurso bloqueado, sin filtrar por `ahora`. `POST /bloqueos` no inyecta reloj y ninguna función nueva llama a `datetime.now()` (Regla dura 2).
- Un bloqueo retroactivo también lista los turnos `reservado` de ese período: es el costo aceptado de no acoplar el reporte al reloj (alternativa descartada: filtrar con `es_futuro(turno, ahora)`).

### D-A4 — Filtro híbrido: preselección en SQL con `?`, regla final en dominio

- **SQL (persistencia, Regla dura 4):** una consulta parametrizada recupera los turnos `reservado` del recurso afectado y acota por rango:
  `WHERE estado = 'reservado' AND profesional_id = ? AND inicio < ? AND fin > ?` (o `sillon_id = ?` para el otro alcance), ordenada `inicio ASC, id ASC`. Es el mismo patrón de `listar_bloqueos_de_recursos` (`app/db/repositorio_bloqueos.py`) y `listar_turnos_activos_del_dia` (`app/db/repositorio_turnos.py`), con el string SQL como literal completo (sin f-strings ni concatenación) y reutilizando los literales de columna vía `COLUMNAS_TURNO`.
- **Dominio (Regla dura 1 y 8):** `turnos_afectados_por_bloqueo(bloqueo, turnos)` aplica `_bloqueo_afecta(bloqueo, turno)` y `solapan(turno, bloqueo)` (semiabiertos `[inicio, fin)`, los contiguos no afectan — RN-TUR-04/05) y filtra `turno.estado == 'reservado'` (RN-TUR-08). Devuelve la lista ordenada por `(turno.inicio, turno.id or 0)`.
- La función vive en `app/domain/reglas_turno.py` junto a `_bloqueo_afecta`; los tests de dominio corren sin base de datos ni HTTP (Regla dura 11). El SQL nunca es la única garantía: la regla de negocio se puede testear pura.

### D-A5 — Alcances cubiertos: solo `profesional` y `sillon`

- El código real de `C-09` en `main` solo admite dos alcances: `CHECK (alcance IN ('profesional', 'sillon'))` en `esquema.sql` y `AlcanceBloqueo = Literal['profesional', 'sillon']` en `models.py`. `_bloqueo_afecta` mapea `profesional → turno.profesional_id` y `sillon → turno.sillon_id`.
- El alcance **global** ("consultorio", feriados generales) **queda explícitamente fuera de alcance**: es `SE-24` y requiere un change posterior que extienda `AlcanceBloqueo`, el `CHECK` de la tabla y la política de recursos.

### D-A6 — Reuso de piezas existentes (nada se duplica)

- **Repositorio:** `_SELECT_POR_ID` / `COLUMNAS_TURNO` / `turno_desde_fila` de `app/db/repositorio_turnos.py` para leer filas → `Turno`. La nueva consulta se agrega en `app/db/repositorio_turnos.py` (misma tabla, misma fila → misma conversión).
- **Serialización:** `TurnoResponse` y `turno_a_response` de `app/api/turnos.py` se importan en `app/api/bloqueos.py` (capa API → capa API; la lógica de negocio no sube al router, Regla dura 8). Así los turnos afectados se serializan exactamente igual que en `GET /turnos/{id}`: `YYYY-MM-DDTHH:MM:SS` y `estado` tipado.
- **Transacción:** la consulta de turnos afectados se hace **dentro** de la `transaccion(conexion)` que ya envuelve `crear_bloqueo`, de modo que el bloqueo y su reporte leen un estado consistente (el bloqueo ya está insertado en la misma transacción al consultar).

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| `[SE-09]` sigue como "abierta" en `knowledge-base/10_preguntas_abiertas.md` | La decisión queda registrada acá con fecha y responsable; `knowledge-base/` no se toca en este change (regla dura 14). Si el grupo cambia de criterio, el alcance se reemplaza |
| Aserción de igualdad exacta de `C-09` (`tests/api/test_bloqueos.py`, línea 46) | Única edición aprobada; el resto del archivo queda intacto y `GET /bloqueos` no cambia |
| Turnos `reservado` que solapan un bloqueo hasta que recepción los reprograme/cancele a mano | Comportamiento esperado bajo D-A1; la lista generada guía el contacto con los pacientes y `C-12`/`C-13`/`C-14` trabajan sobre el mismo estado |
| Filtro con `<=` / `>=` en vez de `<` / `>` (falsos positivos en turnos contiguos) | Reuso directo de `solapan()` + test de dominio del borde (`turno.fin == bloqueo.inicio` y `turno.inicio == bloqueo.fin` → no afectados) |

## Open Questions

- Formalizar la decisión D-A1 en `knowledge-base/10_preguntas_abiertas.md` §`SE-09`: pendiente de sync (fuera de este change; `knowledge-base/` no se modifica a mano, regla dura 14).
- `C-14` (agenda): cómo marcar visualmente turno reservado + bloqueo coexistentes — queda para el design de `C-14`.
