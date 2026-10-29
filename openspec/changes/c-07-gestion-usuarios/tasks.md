# Tasks

## 1. Dominio puro

- [ ] 1.1 Escribir en `tests/domain/test_usuarios_gestion.py` los tests de `validar_username` (trim, vacío, solo espacios) y de `validar_datos_usuario` (odontólogo con profesional activo; sin profesional, inexistente o inactivo; rol no odontólogo con `profesional_id`; rol no odontólogo sin vínculo) y verificar que fallan por ausencia de la función
- [ ] 1.2 Implementar `validar_username` y `validar_datos_usuario` en `app/domain/usuarios.py` y verificar que los tests de 1.1 pasan
- [ ] 1.3 Escribir los tests de `aplicar_cambios_usuario` (campo omitido conserva valor; `null` explícito de `profesional_id`; salir de `odontologo` limpia el vínculo; entrar a `odontologo` sin profesional falla; `activo` omitido conserva) y verificar que fallan
- [ ] 1.4 Implementar `aplicar_cambios_usuario` y el centinela `SIN_CAMBIO` en `app/domain/usuarios.py` y verificar que los tests de 1.3 pasan
- [ ] 1.5 Verificar la pureza del módulo con `test_modulo_usuarios_no_importa_capas_externas` (sin FastAPI, `app.db` ni `app.api`) y confirmar que sigue verde

## 2. Persistencia y errores

- [ ] 2.1 Agregar `UsernameDuplicado(ErrorDominio)` en `app/domain/errores.py` y su entrada `(409, "username_duplicado")` en `MAPEO_DOMINIO` de `app/api/errores.py`
- [ ] 2.2 Escribir en `tests/api/test_repositorio_usuarios.py` los tests de `crear_usuario` (alta válida con hash, `username` duplicado → `UsernameDuplicado`, otra `IntegrityError` se re-lanza), `listar_usuarios` (orden por `id`, incluye inactivos) y `actualizar_usuario` (rol, activo, `profesional_id`, hash nuevo y hash conservado con centinela; id inexistente → `None`) y verificar que fallan
- [ ] 2.3 Implementar `app/db/repositorio_usuarios.py` con `crear_usuario` (wrapper de `insertar_usuario` con traducción de `UNIQUE`), `listar_usuarios` y `actualizar_usuario` con centinela, y verificar que los tests de 2.2 pasan
- [ ] 2.4 Verificar que `app/db/repositorio.py`, `app/db/seed.py` y `app/api/seguridad.py` no tienen cambios (`git diff --stat` vacío para esos archivos) y que los tests de login de `C-03` siguen verdes

## 3. API de usuarios

- [ ] 3.1 Escribir en `tests/api/test_usuarios.py` los tests de alta (`POST /usuarios`): 201 de recepción sin `profesional_id`, 201 de odontólogo con profesional activo, 409 `username_duplicado`, 422 por odontólogo sin profesional/inexistente/inactivo, 422 por rol no odontólogo con `profesional_id`, 422 por username vacío, 422 por password vacía, 422 por rol fuera de los tres, y respuesta sin `password_hash`; verificar que fallan
- [ ] 3.2 Crear `app/api/usuarios.py` con `UsuarioEntrada`, `UsuarioActualizar`, `UsuarioSalida`, el helper `_a_salida`, el `POST /usuarios` y el montaje del router en `app/main.py`; verificar que los tests de 3.1 pasan
- [ ] 3.3 Escribir los tests de `GET /usuarios`: 200 ordenado por `id` con activos e inactivos, respuesta sin `password_hash` en ningún elemento, 403 para recepción y 403 para odontólogo; verificar que fallan
- [ ] 3.4 Implementar `GET /usuarios` con `listar_usuarios` y verificar que los tests de 3.3 pasan
- [ ] 3.5 Escribir los tests de `PATCH /usuarios/{id}`: desactivar, reactivar, `rol` nulo → 422, `activo` nulo → 422, `username` presente → 422 sin cambios, id inexistente → 404, recepción → odontólogo con profesional válido, recepción → odontólogo sin profesional → 422, odontólogo → recepción limpia `profesional_id`, odontólogo → administración limpia `profesional_id`, cambio de profesional conservando el rol, cambio a profesional inactivo → 422, reset de contraseña (hash nuevo, login con la nueva, login con la vieja 401), `password` omitida conserva el hash, `password` vacía → 422 y respuesta sin secretos; verificar que fallan
- [ ] 3.6 Implementar `PATCH /usuarios/{id}` con `aplicar_cambios_usuario`, `obtener_profesional_por_id`, `hashear` y `actualizar_usuario` dentro de `transaccion()` y verificar que los tests de 3.5 pasan
- [ ] 3.7 Escribir y verificar los tests de acceso: 401 sin token en las tres rutas, 403 de recepción y odontólogo en las tres, 405 `metodo_no_permitido` en `DELETE /usuarios/{id}`, login 401 `credenciales_invalidas` de un usuario desactivado y 401 `no_autenticado` de un token emitido antes de la desactivación

## 4. Verificación e integración

- [ ] 4.1 Correr la suite completa (`python -m pytest -q`) y verificar 0 fallos y que el total sea 393 más los tests nuevos
- [ ] 4.2 Correr `openspec validate c-07-gestion-usuarios --strict` y verificar que no reporta errores ni warnings
- [ ] 4.3 Verificar con `git status`/`git diff` que no se modificaron `app/db/esquema.sql`, `app/db/repositorio.py`, `app/db/seed.py`, `app/api/auth.py` ni `app/api/seguridad.py`, y que no hay secretos ni contraseñas reales en fixtures (RN-PAC-03, regla dura 9)
- [ ] 4.4 Revisar la trazabilidad de los requirements del delta `usuarios` y `errores-api`: cada uno tiene al menos un test que lo cubre, y anotar la tabla requirement → test en la verificación del change

## Workflow follow-up

- Correr la verificación del proyecto y dejar el resultado registrado (no se archiva con tests en rojo).
- Archivar con `/opsx:archive c-07-gestion-usuarios` cuando la revisión esté aprobada.
- Marcar `[C-07]` en `CHANGES.md` solo si el usuario lo pide (regla dura 14).
- No hacer commit ni push sin pedido explícito del usuario (regla dura 13).
