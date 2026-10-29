# Proposal

## Why

`C-03` dejó el login y el control por roles, pero no existe forma de crear usuarios: fuera de `admin_demo` (seed de desarrollo), el consultorio no puede dar de alta recepción ni odontólogos. Sin esta gestión, `C-17` no puede sembrar los tres usuarios demo y el MVP no puede operar con roles reales (US-013).

## What Changes

- Nuevas rutas `GET /usuarios`, `POST /usuarios` y `PATCH /usuarios/{id}`, exclusivas del rol `administracion` (`403` para recepción y odontólogo, `401` sin token).
- Alta y edición de usuarios con `username`, `rol`, `activo` y `profesional_id`; la contraseña se guarda solo como hash Argon2id y nunca se devuelve.
- Invariante rol ↔ profesional: `odontologo` exige un `profesional_id` existente y activo; cualquier otro rol lo deja nulo. Al cambiar el rol a uno distinto de `odontologo`, el servidor limpia `profesional_id` automáticamente.
- Reset de contraseña mediante el campo opcional `password` en `PATCH /usuarios/{id}`; sin política nueva de contraseña (`min_length=1`, igual que el login).
- `username` inmutable: si el body de `PATCH` lo incluye, responde `422` sin modificar el usuario.
- `username` duplicado responde `409` con un código nuevo `username_duplicado`.
- Baja lógica con `activo = false`; un usuario desactivado sigue listándose, no puede loguear y su token vigente deja de servir.
- Repositorio nuevo `app/db/repositorio_usuarios.py`; `app/db/repositorio.py` queda intacto para no tocar login ni seed.
- **Sin cambios de esquema**: la tabla `usuario` de `C-03` ya tiene todas las columnas.
- **Sin auditoría de usuarios** (IF-06: el MVP audita solo turnos) y **sin `DELETE`**.
- **Fuera de alcance:** política de contraseña más estricta y guardas contra el auto-bloqueo del administrador; ambas quedan como riesgos documentados.

## Capabilities

### New Capabilities

- `usuarios`: gestión administrativa del padrón de usuarios del sistema (alta, listado y edición parcial), incluida la invariante entre rol y profesional, el manejo del hash de contraseña y la baja lógica.

### Modified Capabilities

- `errores-api`: se agrega el código `username_duplicado` para el `409` por `username` ya existente.

## Impact

- **Código nuevo:** `app/api/usuarios.py`, `app/db/repositorio_usuarios.py`, `tests/domain/test_usuarios_gestion.py` (o equivalente), `tests/api/test_repositorio_usuarios.py` y `tests/api/test_usuarios.py`.
- **Código modificado (aditivo):** `app/domain/usuarios.py` (validaciones puras), `app/domain/errores.py` (`UsernameDuplicado`), `app/api/errores.py` (mapeo `409 username_duplicado`) y `app/main.py` (montaje del router).
- **Sin cambios:** `app/db/esquema.sql`, `app/db/repositorio.py`, `app/db/seed.py`, `app/api/auth.py` y `app/api/seguridad.py`.
- **API:** tres endpoints nuevos bajo `/usuarios`; ningún endpoint existente cambia de contrato.
- **Datos:** no hay migración; los usuarios existentes (`admin_demo`, fixtures) siguen siendo válidos.
- **Dependencias:** ninguna nueva; se reutilizan `hashear`, `obtener_conexion`, `transaccion`, `requiere_rol`, `buscar_usuario_por_id` y `obtener_profesional_por_id`.
- **Base de tests:** la suite actual tiene 393 tests verdes; el change debe cerrar sin regresiones.
