# Design — C-12 cancelar-turno

## Context

`C-12` pertenece al GATE 6 (después de `C-11 crear-turno`, en paralelo con `C-13 reprogramar-turno` y `C-14 agenda`) y está en el camino crítico (`C-11 → C-12 → C-15 → C-17`). Ver `proposal.md` para motivación y `explore.md` para el relevamiento.

Estado previo y restricciones:
- `C-02` aporta `TurnoNoModificable` en `app/domain/errores.py` y `es_futuro(turno, ahora)` con reloj inyectado.
- `C-10` ya ignora los turnos con `estado != "reservado"` en `validar_alta` (`app/domain/reglas_turno.py` L48), por lo que pasar un turno a `estado = "cancelado"` libera automáticamente el hueco en la validación de solapamientos (`RN-TUR-06`, `RN-TUR-08`).
- `C-11` crea las tablas `turno` y `auditoria_turno` y el router `app/api/turnos.py`.
- Reglas duras aplicables (`AGENTS.md`):
  1. `app/domain/` es Python puro.
  2. Nunca llamar `datetime.now()` dentro del dominio; recibir `ahora: datetime` por parámetro.
  5. Validar y escribir el cambio del turno y su auditoría en una única transacción (`RN-AUD-03`).
  6. `auditoria_turno` es append-only (solo `INSERT`).

## Goals / Non-Goals

**Goals:**
- Implementar `validar_cancelacion(turno: Turno, ahora: datetime) -> Turno` en `app/domain/reglas_turno.py` cumpliendo `RN-TUR-09` y `RN-TUR-10`.
- Persistir la transición a `cancelado` y el registro de auditoría (`accion = "cancelar"`, `antes`, `despues`, `usuario_id`, `ocurrio_en`) en una única transacción de escritura.
- Exponer `POST /turnos/{id}/cancelar` para `administracion` y `recepcion`, traduciendo `TurnoNoModificable` a `409` y turno inexistente a `404`.
- Probar con reloj fijo los tres casos de borde temporal (`ahora < inicio`, `ahora == inicio`, `ahora > inicio`), la segunda cancelación (`409`) y la reutilización del hueco liberado (`201`).

**Non-Goals:**
- Plazo mínimo configurable de anticipación (`IF-10` / `SE-08`, fuera del MVP).
- Reprogramación (`C-13`) o listado de auditoría (`C-15`).

## Decisions

- **D1 — Regla pura `validar_cancelacion(turno, ahora)` en `app/domain/reglas_turno.py`.**
  ```python
  def validar_cancelacion(turno: Turno, ahora: datetime) -> Turno:
      if turno.estado == "cancelado":
          raise TurnoNoModificable("El turno ya está cancelado.")
      if not es_futuro(turno, ahora):
          raise TurnoNoModificable("Solo se pueden cancelar turnos futuros.")
      return replace(turno, estado="cancelado")
  ```
  *Por qué:* chequea primero `RN-TUR-10` (estado `cancelado`) y luego `RN-TUR-09` (`turno.inicio > ahora`) con el reloj inyectado `ahora`, devolviendo una nueva instancia inmutable (`dataclasses.replace`) sin efectos secundarios. Tanto `RN-TUR-09` como `RN-TUR-10` lanzan `TurnoNoModificable`, que la capa API traduce a `409`.

- **D2 — Transacción única para actualizar turno e insertar auditoría (ajustado en apply).** Siguiendo el patrón de `C-11` y la regla dura 1 (`db → domain` solo tipos), el repositorio no llama al dominio. `POST /turnos/{id}/cancelar` orquesta todo dentro de `with transaccion(conexion):` (`BEGIN IMMEDIATE`):
  1. Carga el turno con `obtener_turno(conexion, turno_id)`. Si no existe, responde `404`.
  2. Llama a `validar_cancelacion(turno_actual, ahora)`. Si lanza `TurnoNoModificable`, la excepción sale del bloque, se hace `rollback` y no se ejecuta ningún `UPDATE` ni `INSERT` (`RN-AUD-03`).
  3. Llama a `cancelar_turno(conexion, turno_actual, usuario_id=..., ocurrio_en=ahora)` de `app/db/repositorio_turnos.py`, que ejecuta `UPDATE turno SET estado = 'cancelado' WHERE id = ?` e inserta en `auditoria_turno` el registro `accion = 'cancelar'` con `antes` (`estado: "reservado"`) y `despues` (`estado: "cancelado"`) usando `snapshot_turno` de `C-11`.
  *Por qué el ajuste:* la versión original ponía la llamada a `validar_cancelacion` dentro del repositorio, lo que rompía la regla dura 1 de `AGENTS.md`.

- **D3 — Reloj inyectado en el endpoint HTTP.** `POST /turnos/{id}/cancelar` obtiene el instante actual desde la dependencia de reloj de la app (`app.state.reloj`), convirtiéndolo a hora local del consultorio sin offset cuando corresponda, para que los tests de API en `tests/api/test_cancelar_turno.py` controlen exactamente el instante (`antes`, `igual`, `después` de `turno.inicio`).

## Estructura resultante (archivos tocados por C-12)

```
app/
├── domain/
│   └── reglas_turno.py            # + validar_cancelacion(turno, ahora)
├── db/
│   └── repositorio_turnos.py      # + cancelar_turno (UPDATE turno + INSERT auditoria_turno en transacción)
└── api/
    └── turnos.py                  # + POST /turnos/{id}/cancelar
tests/
├── domain/
│   └── test_reglas_turno.py       # + tests unitarios de validar_cancelacion (antes, igual, después, ya cancelado)
└── api/
    └── test_cancelar_turno.py     # tests de API (200, 409 pasado/en curso/doble cancelación, 404, 403, re-reserva 201)
```

## Risks / Trade-offs

- **[Conflicto de merge con `C-13 reprogramar-turno` en `reglas_turno.py` y `turnos.py`]** → Mitigación: ambos changes se apoyan en `C-11` y agregan una función de dominio y un endpoint distinto (`/cancelar` vs `/reprogramar`); ubicar el bloque de cancelación de forma autocontenida facilita el merge.
- **[Diferencia entre `ahora` con timezone (JWT en UTC) y `Turno.inicio` (hora local sin offset)]** → Mitigación: normalizar el instante del reloj de la app a la zona `CLINIC_TIMEZONE` sin `tzinfo` en un único helper compartido de `app/api/` antes de pasarlo al dominio.

## Migration Plan

No requiere cambios de esquema SQL (las tablas `turno` y `auditoria_turno` ya las crea `C-11`). Rollback: revertir el merge del change.

## Open Questions

Ninguna.
