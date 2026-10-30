# Proposal — C-16 bloqueos-turnos-afectados

## Why

Cuando administración crea un bloqueo horario (`POST /bloqueos`), puede haber turnos ya reservados (`estado = 'reservado'`) que quedan dentro del intervalo del recurso bloqueado (vacaciones de un profesional, mantenimiento de un sillón). Hoy el endpoint responde `201` con el bloqueo y **no informa** ese impacto (`US-005`, Flujo 5): recepción no tiene forma de saber qué pacientes hay que contactar. `C-09` declaró explícitamente esto como *Non-Goal* ("queda para `C-16 bloqueos-turnos-afectados` una vez decidida `SE-09`"). Con `SE-09` ya decidida (2026-10-29, ver design.md D-A1) y `C-11` (tabla `turno`, `repositorio_turnos.py`) y `C-09` en `main`, `C-16` está desbloqueado.

## What Changes

- Se agrega en `app/domain/reglas_turno.py` la función pura `turnos_afectados_por_bloqueo(bloqueo, turnos) -> list[Turno]`, que reutiliza `_bloqueo_afecta` y `solapan` (intervalos semiabiertos `[inicio, fin)`), filtra solo turnos `reservado` y ordena por `inicio ASC, id ASC`. Sin FastAPI, sin SQLite, sin reloj (`datetime.now()` prohibido, RN-TUR-09).
- Se agrega en `app/db/` una consulta SQL parametrizada con `?` que recupera los turnos `reservado` del recurso afectado acotados por rango (`inicio < ? AND fin > ?`, patrón de `listar_bloqueos_de_recursos` y `listar_turnos_activos_del_dia`), reutilizando `COLUMNAS_TURNO` y `turno_desde_fila`.
- Se extiende `POST /bloqueos` para responder, junto al bloqueo creado, `turnos_afectados: list[TurnoResponse]` al mismo nivel (JSON plano, decisión D-A2 confirmada por Bruno), serializado reutilizando `TurnoResponse` y `turno_a_response` de `app/api/turnos.py`. Todo dentro de la `transaccion(conexion)` existente. **No cancela ni modifica** los turnos y **no escribe** en `auditoria_turno` (IF-06: los bloqueos no se auditan; la cancelación es `C-12`).
- `GET /bloqueos` queda sin el campo `turnos_afectados` (no se penaliza con consultas N+1).
- Única edición aprobada en tests de `C-09`: la aserción de igualdad exacta de la respuesta de `POST /bloqueos` en `tests/api/test_bloqueos.py` pasa a incluir `"turnos_afectados": []`. El resto de los tests de `C-09` y `GET /bloqueos` no se tocan.

**Fuera de alcance:**
- Cancelar, reprogramar o modificar los turnos afectados (`C-12`/`C-13`); escribir en `auditoria_turno` (IF-06).
- `SE-09` alternativas: rechazo del bloqueo con `409` o cancelación en cascada (decisión registrada en design.md D-A1, revisable si el grupo propone otra cosa).
- Alcance de bloqueo **global** / "consultorio" (feriados generales): el código real de `C-09` solo admite `profesional` y `sillon` (`CHECK (alcance IN ('profesional', 'sillon'))` en `esquema.sql`); es `SE-24` y un change posterior.
- Cambiar el esquema, `validar_alta` o el comportamiento de `GET`/`DELETE /bloqueos`.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `bloqueos`: al crear un bloqueo sobre profesional o sillón, `POST /bloqueos` reporta en su respuesta los turnos `reservado` que se solapan con el intervalo del recurso bloqueado, sin alterarlos. Cubre `RN-TUR-04` (solapamiento semiabierto), `RN-TUR-05` (bloqueo afecta al recurso del turno) y `RN-TUR-08` (solo los turnos activos ocupan agenda).

## Impact

- **Archivos modificados:** `app/domain/reglas_turno.py` (nueva función pública pura; `_bloqueo_afecta` intacta), `app/db/repositorio_turnos.py` (nueva consulta parametrizada reutilizando `COLUMNAS_TURNO` y `turno_desde_fila`), `app/api/bloqueos.py` (`POST /bloqueos` devuelve `BloqueoCreadoSalida(BloqueoSalida)` con `turnos_afectados`, sin tocar `GET`/`DELETE`), `tests/domain/test_reglas_turno.py` (o `tests/domain/test_bloqueos_turnos_afectados.py`) y `tests/api/test_bloqueos.py` (solo la aserción aprobada).
- **Sin cambios:** `app/domain/intervalos.py`, `app/domain/models.py`, `app/db/esquema.sql`, `app/api/turnos.py` (solo se importa), `app/domain/reglas_turno.py::validar_alta`, `GET/DELETE /bloqueos`.
- **Governance:** MEDIO.
- **Dependencias:** `C-11` (en `main`). Los únicos bloqueos de la cadena ya están completados y archivados (`C-02`, `C-04`, `C-05`, `C-06`, `C-08`, `C-09` y `C-10`); no quedan precondiciones pendientes.
