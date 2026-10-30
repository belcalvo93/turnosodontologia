# Tasks — C-12 cancelar-turno

## 1. Dominio puro (`RN-TUR-09`, `RN-TUR-10`)

- [x] 1.1 Implementar `validar_cancelacion(turno: Turno, ahora: datetime) -> Turno` en `app/domain/reglas_turno.py` usando `es_futuro(turno, ahora)` y `TurnoNoModificable`, verificando con tests unitarios en `tests/domain/test_cancelar_turno.py` (con reloj fijo `ahora = 09:00`): turno a las `10:00` devuelve turno con `estado="cancelado"`, turno a las `08:30` lanza `TurnoNoModificable`, turno a las `09:00` exactas lanza `TurnoNoModificable`, y turno ya `cancelado` lanza `TurnoNoModificable`

## 2. Persistencia transaccional y auditoría (`RN-AUD-01`, `RN-AUD-03`)

- [x] 2.1 Agregar `cancelar_turno(conexion, antes, despues, *, usuario_id, ocurrio_en)` en `app/db/repositorio_turnos.py` que, dentro de la transacción abierta por el router, actualice `estado = 'cancelado'` e inserte en `auditoria_turno` el registro `accion = 'cancelar'` con `usuario_id`, `ocurrio_en`, `antes` y `despues` (sin llamar al dominio, regla dura 1), verificando con tests que guarda el turno cancelado con un único registro de auditoría y que si la transacción se revierte no queda ni el cambio de estado ni la auditoría

## 3. Endpoint HTTP y liberación de agenda (`RN-TUR-06`, `RN-ACC-02`)

- [x] 3.1 Implementar `POST /turnos/{id}/cancelar` en `app/api/turnos.py` para los roles `administracion` y `recepcion` con reloj inyectado, verificando con tests en `tests/api/test_cancelar_turno.py`: cancelación de turno futuro (`200` con `estado = "cancelado"` y registro en `auditoria_turno`), turno en el instante exacto o pasado (`409`), segunda cancelación (`409` sin nuevo registro de auditoría) y turno inexistente (`404`)
- [x] 3.2 Verificar en `tests/api/test_cancelar_turno.py` que tras cancelar un turno de `10:00` a `10:30`, reservar un nuevo turno en el mismo intervalo con el mismo profesional, sillón y paciente responde `201` (`RN-TUR-06`), y que un usuario con rol `odontologo` recibe `403` (`RN-ACC-02`) y una petición sin token recibe `401` (`RN-ACC-01`)

## 4. Verificación integral del change

- [x] 4.1 Ejecutar `pytest tests` completo y verificar que toda la suite pasa en verde
- [x] 4.2 Verificar que `app/domain/` no llama a `datetime.now()` ni importa `fastapi`/`app.db`/`app.api`
- [x] 4.3 Ejecutar `openspec validate c-12-cancelar-turno --strict` y verificar que no reporta errores

## Workflow follow-up

- Esperar a que `C-11` (`crear-turno`) esté mergeado en `main` antes de ejecutar `/opsx:apply c-12-cancelar-turno`.
- Verificar el change con toda la suite en verde.
- Archivar con `/opsx:archive c-12-cancelar-turno` y marcar `C-12` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
