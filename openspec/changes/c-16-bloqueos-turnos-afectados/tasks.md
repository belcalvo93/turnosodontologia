# Tasks — C-16 bloqueos-turnos-afectados

> Strict TDD (Regla dura 11): cada tarea arranca con test en rojo y termina en verde. Nada corrobora dominio con HTTP ni base de datos. Governance: MEDIO.

## 1. Dominio (función pura, Regla dura 1)

- [x] 1.1 **Rojo:** en `tests/domain/test_reglas_turno.py` (o nuevo `tests/domain/test_bloqueos_turnos_afectados.py`), escribir los tests de `turnos_afectados_por_bloqueo(bloqueo, turnos)` sin implementarla: turnos `reservado` solapados de forma parcial son reportados, y los turnos de otro profesional o de otro sillón quedan fuera (`RN-TUR-05`). Datos ficticios.
- [x] 1.2 **Rojo:** test de contigüidad en el borde (`turno.fin == bloqueo.inicio` y `turno.inicio == bloqueo.fin` → NO afectados; `RN-TUR-04`) y test de exclusión de turnos `cancelado` (`RN-TUR-08`).
- [x] 1.3 **Rojo:** test de orden de la salida por `inicio ASC` y de que la función no depende del reloj (no recibe `ahora`; D-A3). El desempate por `id ASC` se prueba SOLO a nivel dominio con una lista armada a mano (dos turnos con el mismo `inicio` y distinto `id`): es un orden determinista defensivo que no ocurre con datos válidos, porque dos turnos `reservado` del mismo profesional o sillón no pueden empezar a la vez (RN-TUR-04 y RN-TUR-11).
- [x] 1.4 **Verde:** implementar en `app/domain/reglas_turno.py` la función pública `turnos_afectados_por_bloqueo(bloqueo: Bloqueo, turnos: Sequence[Turno]) -> list[Turno]`, reutilizando `_bloqueo_afecta` y `solapan` (Regla dura 3, semiabiertos `[inicio, fin)`), filtrando `estado == "reservado"`. Sin FastAPI, sin SQLite, sin `datetime.now()` (Regla dura 2). Ejecutar los tests de 1.1 a 1.3 en verde y el resto de `tests/domain/` sin regresiones.

## 2. Repositorio (SQL parametrizado, Regla dura 4)

- [x] 2.1 **Rojo:** en `tests/api/test_repositorio_turnos.py` (o el archivo de repositorios que use C-11 para SQLite), test de la nueva consulta SQL parametrizada con `?`: dados 3 turnos `reservado` (dos del recurso en rango, uno fuera de rango) + 1 `cancelado` en rango, devuelve exactamente los del recurso en rango, en el orden `inicio ASC, id ASC` y como `Turno` (via `turno_desde_fila`).
- [x] 2.2 **Rojo:** test de contigüidad en SQL (turno con `fin == inicio_bloqueo` o `inicio == fin_bloqueo` → excluido) para validar el patrón `inicio < ? AND fin > ?` (idéntico a `listar_bloqueos_de_recursos`).
- [x] 2.3 **Verde:** implementar en `app/db/repositorio_turnos.py` la consulta con SQL como literal completo (sin f-strings ni concatenación), reutilizando `COLUMNAS_TURNO` y `turno_desde_fila`. La conversión de `Turno` ←→ fila no se duplica.

## 3. Router (contrato plano D-A2, Regla dura 8)

- [ ] 3.1 **Rojo:** en `tests/api/test_bloqueos.py`, tests de API para `POST /bloqueos` con stock de datos ficticios (`"(ficticio)"`, `RN-PAC-03`): con 2 turnos `reservado` y 1 `cancelado` en rango → `201` con los 6 campos actuales + `turnos_afectados` (solo los 2 `reservado`, serializados como `TurnoResponse`, ordenados por `inicio ASC`); sin turnos → `turnos_afectados = []`; verificación posterior con `GET /turnos/{id}` de que los turnos siguen `reservado` y con `repositorio_turnos`/`auditoria_turno` de que no se agregaron filas de auditoría (`IF-06`, D-A1).
- [ ] 3.2 **Rojo:** test de que los reportes también salen para `alcance = "sillon"` y test de que `GET /bloqueos` sigue sin contener la clave `turnos_afectados` (contrato actual intacto).
- [ ] 3.3 **Verde:** en `app/api/bloqueos.py`, agregar `BloqueoCreadoSalida(BloqueoSalida)` con `turnos_afectados: list[TurnoResponse]` **solo para `POST`**, importando `TurnoResponse`/`turno_a_response` de `app/api/turnos.py`; dentro de la `transaccion(conexion)` actual, tras `crear_bloqueo`, consultar el repositorio (2.3) y filtrar con `turnos_afectados_por_bloqueo` (1.4). Sin lógica de negocio en el router, sin tocar `GET`/`DELETE`.
- [ ] 3.4 **Verde:** ejecutar toda la suite `pytest`.

## 4. Compatibilizar el test de `C-09` (única edición aprobada)

- [ ] 4.1 **Rojo → verde en un paso:** actualizar la aserción de igualdad exacta de la respuesta de `POST /bloqueos` en `tests/api/test_bloqueos.py` (línea 46) para incluir `"turnos_afectados": []`. El resto del archivo y los tests de `GET`/`DELETE /bloqueos` no se tocan.

## 5. Verify (para el cierre del change)

- [ ] 5.1 Correr toda la suite y los health checks; no archivar con nada en rojo.
- [ ] 5.2 Verificar trazabilidad RN→test: `RN-TUR-04`, `RN-TUR-05` y `RN-TUR-08` cubiertas por los tests de dominio; sin `RN` sin test.
- [ ] 5.3 Verificar datos ficticios en los fixtures nuevos: DNIs con sufijo `"(ficticio)"` y sin datos reales.
- [ ] 5.4 Guardar (`sync`) el delta del spec a `openspec/specs/bloqueos/spec.md` recién al archivar el change (paso `/opsx:archive`).
