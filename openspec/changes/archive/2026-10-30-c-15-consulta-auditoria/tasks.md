# Tasks

## 1. Entidad y repositorio de lectura

- [x] 1.1 Escribir en `tests/api/test_repositorio_auditoria.py` los tests de `listar_auditoria_por_turno`: devuelve todos los registros de un turno y ninguno de otro, ordena por `ocurrio_en` y desempata por `id`, parsea `antes`/`despues` a objetos, devuelve el `username` del usuario que operó, deja `antes` en `None` para el alta y devuelve lista vacía si el turno no tiene registros; verificar que fallan por ausencia de la función
- [x] 1.2 Agregar `RegistroAuditoria` (dataclass frozen) en `app/domain/models.py` con `id`, `turno_id`, `accion`, `usuario_id`, `username`, `ocurrio_en`, `antes` y `despues`, y verificar que los tests de pureza del dominio siguen verdes
- [x] 1.3 Implementar `app/db/repositorio_auditoria.py` con `listar_auditoria_por_turno` (SELECT parametrizado con `LEFT JOIN usuario` y `ORDER BY ocurrio_en ASC, id ASC`) y verificar que los tests de 1.1 pasan
- [x] 1.4 Verificar que `app/db/repositorio_turnos.py` y `app/api/turnos.py` no tienen cambios (`git diff --stat` vacío para ambos) y que los tests de auditoría de `C-11` siguen verdes

## 2. Endpoint de consulta

- [x] 2.1 Escribir en `tests/api/test_auditoria.py` los tests del contrato de `GET /auditoria?turno_id=` y verificar que **fallan antes de implementar**: 200 con los 3 registros en orden `crear` → `reprogramar` → `cancelar`, turno con solo el alta devuelve 1 registro, `antes`/`despues` llegan como objetos con las 8 claves canónicas, `antes` es `null` solo en `crear`, la reprogramación conserva el `id` y cambia el `inicio`, y `ocurrio_en` tiene formato `YYYY-MM-DDTHH:MM:SS`
- [x] 2.2 Crear `app/api/auditoria.py` con `RegistroAuditoriaSalida`, `AuditoriaResponse` y `GET /auditoria` (sin verificar todavía la existencia del turno) y montar el router en `app/main.py`; verificar que los tests de 2.1 pasan
- [x] 2.3 Escribir los tests de `turno_id` y verificar que **fallan antes de implementar**: ausente → 422, `0` → 422, negativo → 422, no entero → 422, e inexistente → 404 con `codigo` `no_encontrado`; agregar la verificación de existencia con `obtener_turno()` y el `404` en `app/api/auditoria.py`, y verificar que los tests pasan
- [x] 2.4 Escribir los tests de identidad y datos sensibles y verificar que **fallan antes de implementar** (el modelo de 2.2 todavía no expone `username`): `username` correcto, usuario desactivado después de operar sigue apareciendo, y la respuesta no contiene `password_hash`, `password`, `rol`, `dni`, `nombre` ni `apellido`; agregar `username` a `RegistroAuditoriaSalida` y cerrar la proyección del `SELECT`, y verificar que los tests pasan

## 3. Acceso y solo lectura

- [x] 3.1 Escribir y verificar los tests de acceso: sin token → 401 `no_autenticado`, recepción → 403 `sin_permiso`, odontólogo → 403 `sin_permiso`, y un rol sin permiso consultando un `turno_id` inexistente recibe 403 (no 404)
- [x] 3.2 Escribir y verificar los tests de solo lectura (RN-AUD-02): `PATCH` y `DELETE` sobre `/auditoria` responden 405, `PATCH` y `DELETE` sobre `/auditoria/{id}` responden 404, y en ambos casos la cantidad de registros de auditoría no cambia

## 4. Integración y verificación

- [x] 4.1 Esperar a que `C-12` y `C-13` estén mergeados en `main`; traerlos con `git merge origin/main` (sin rebase y sin mergear ramas ajenas que no estén en `main`) y verificar que el escenario de 3 registros corre contra el código real
- [x] 4.2 Correr la suite completa (`.venv\Scripts\python.exe -m pytest -q`) y verificar 0 fallos y que el total sea 718 más los tests nuevos
- [x] 4.3 Correr `openspec validate c-15-consulta-auditoria --strict` y verificar que no reporta errores ni warnings
- [x] 4.4 Verificar con `git status`/`git diff` que no se modificaron `app/db/esquema.sql`, `app/db/repositorio_turnos.py`, `app/api/turnos.py` ni `app/api/errores.py`, y que no hay secretos ni datos reales en fixtures (regla dura 9, RN-PAC-03)
- [x] 4.5 Revisar la trazabilidad del delta `auditoria-turnos`: cada requirement nuevo tiene al menos un test que lo cubre y anotar la tabla requirement → test en la verificación del change

## Workflow follow-up

- Correr la verificación del proyecto y dejar el resultado registrado (no se archiva con tests en rojo).
- Archivar con `/opsx:archive c-15-consulta-auditoria` cuando la revisión esté aprobada.
- Marcar `[C-15]` en `CHANGES.md` solo si el usuario lo pide (regla dura 14).
- No hacer commit ni push sin pedido explícito del usuario (regla dura 13).
