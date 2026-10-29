# Design — C-08 horarios-atencion

## Context

`C-08` implementa la disponibilidad horaria semanal de los profesionales odontológicos. Cada profesional puede tener una o varias franjas horarias por día de la semana (0 = lunes ... 6 = domingo), por ejemplo turno mañana y turno tarde. Las franjas de un mismo día no pueden superponerse (intervalos semiabiertos `[hora_desde, hora_hasta)`).

## Goals / Non-Goals

**Goals:**
- Validar en el dominio puro que `hora_desde < hora_hasta`, que `dia_semana` esté en `0..6` y que las franjas del mismo día no se superpongan (lanzando `DatoInvalido`).
- Persistir franjas en SQLite en la tabla `horario_atencion` con clave foránea a `profesional` e índice por profesional y día.
- Exponer `GET /profesionales/{id}/horarios` y `POST /profesionales/{id}/horarios` respetando la matriz RBAC (administración crea; recepción y administración leen; odontólogo solo lee los propios).
- Devolver `422` al intentar crear un horario para un profesional inexistente.

**Non-Goals:**
- Bloqueos horarios o vacaciones (`C-09`).
- Validación de que un turno caiga en horario de atención al momento de crearlo (ya implementado en `C-10` y consumido en `C-11`).
- Edición o borrado de franjas existentes (fuera del scope inicial de `C-08`).

## Decisions

- **D1 — Horas como cadenas ISO HH:MM en SQLite y objetos `time` en Python.** En la base de datos SQLite se guardan como `TEXT NOT NULL` con formato `"HH:MM"`. En Python se representan como `datetime.time`. Esto permite comparaciones lexicográficas correctas en SQL y tipado estricto en el dominio.
- **D2 — Intervalos semiabiertos para franjas horarias.** Dos franjas del mismo día `a` y `b` se solapan si `a.hora_desde < b.hora_hasta and b.hora_desde < a.hora_hasta`. Franjas contiguas (ej. `09:00 - 13:00` y `13:00 - 17:00`) no se solapan y son válidas.
- **D3 — Comprobación de existencia de profesional en `POST`.** Si el profesional no existe, se lanza `DatoInvalido("El profesional indicado no existe.")`, lo que resulta en HTTP `422` conforme a `CHANGES.md`.
- **D4 — Control de acceso para odontólogo en `GET`.** Si el rol es `odontologo`, se verifica `usuario.profesional_id == id`. Si no coincide (o es nulo), se responde `403` (`SinPermiso`).

## Risks / Trade-offs

- **[Turno que cruza el corte de mediodía]** → Mitigado por `_encaja_en_franja` en `reglas_turno.py` y verificado en `C-10`.
- **[Concurrencia en guardado]** → SQLite serializa transacciones inmediatas dentro de `transaccion(conexion)`.
