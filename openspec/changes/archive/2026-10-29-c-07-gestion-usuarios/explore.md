# Explore — C-07 gestion-usuarios

Relevamiento previo al propose. **No implementa nada**: fija el estado actual, la brecha, los riesgos y las decisiones ya cerradas por el equipo.

## 1. Alcance declarado en el roadmap

`CHANGES.md` (sección `[C-07] gestion-usuarios`) define:

- `GET/POST /usuarios` y `PATCH /usuarios/{id}` (rol, `activo`, reset de contraseña), solo para administración.
- Validación: el rol `odontologo` exige `profesional_id` existente y activo; los demás roles lo dejan nulo.
- La respuesta nunca incluye `password_hash`.
- Tests: admin crea recepción y odontólogo vinculado, odontólogo sin profesional → 422, recepción usando la ruta → 403, usuario desactivado no puede loguear.
- Dependencias: `C-03` (archivado) y `C-04` (archivado) → gate 4 abierto.
- Governance: ALTO. Consumidor: `C-17 seed-y-flujo-e2e`.

```
C-03 auth (hecho) ──┐
                    ├──> C-07 gestion-usuarios ──> C-17 cierre MVP
C-04 profesionales ─┘         (gate 4 abierto)
```

## 2. Qué existe hoy

| Pieza | Estado | Evidencia |
|---|---|---|
| Tabla `usuario` (`username UNIQUE`, `rol CHECK`, `profesional_id` sin FK, `activo`) | Existe | `app/db/esquema.sql` |
| `Rol` y `Usuario` (sin `password_hash`) | Existe | `app/domain/usuarios.py` |
| `insertar_usuario`, `buscar_credenciales`, `buscar_usuario_por_id` | Existen | `app/db/repositorio.py` |
| `usuario_actual` (recarga en cada request → baja = 401) y `requiere_rol` | Existen | `app/api/auth.py` |
| `hashear` / `verificar` (Argon2id) | Existen | `app/api/seguridad.py` |
| `obtener_profesional_por_id` | Existe | `app/db/repositorio_profesionales.py` |
| `GET /usuarios`, `POST /usuarios`, `PATCH /usuarios/{id}` | **No existen** | ningún router los monta |
| `listar_usuarios`, `actualizar_usuario`, traducción de `UNIQUE(username)` | **No existen** | `repositorio.py` solo tiene login y búsqueda por id |
| Validación pura del vínculo rol ↔ profesional | **No existe** | — |
| Código de error `username_duplicado` | **No existe** | `errores-api` no lo define |
| Capability `usuarios` en `openspec/specs/` | **No existe** | solo `acceso-usuarios` (login/RBAC) |
| Fixtures `cliente`, `crear_usuario`, `token_de`, `reloj` | Existen | `tests/conftest.py` |
| Baseline de la suite | 393 tests verdes | `pytest --collect-only` |

**Conclusión:** no hay que inventar arquitectura. Es el mismo patrón de `C-04`/`C-05`/`C-06` (dominio puro + repositorio dedicado + router + tests por capa), con una diferencia: **la tabla y la entidad ya existen** (las creó `C-03` para el login) y hay que agregarles CRUD sin tocar las funciones de login.

## 3. Qué falta

### 3.1 Esquema

**No se toca `app/db/esquema.sql`.** La tabla `usuario` de `C-03` ya tiene todo lo necesario (`username UNIQUE`, `rol CHECK`, `profesional_id` nullable sin FK, `activo CHECK`). C-07 no agrega columnas ni migra datos: `admin_demo` y cualquier usuario creado por el seed siguen funcionando.

### 3.2 Dominio

En `app/domain/usuarios.py` (Python puro, sin DB ni HTTP):

- `validar_username(username: str) -> str`: `strip()` y rechazo de vacío con `DatoInvalido`.
- `validar_datos_usuario(*, rol, profesional_id, profesional: Profesional | None) -> tuple[Rol, int | None]`, con la invariante:
  - `rol == odontologo` → `profesional_id` obligatorio, el profesional debe existir y estar activo; si no, `DatoInvalido`.
  - `rol != odontologo` → `profesional_id` debe ser `None`; si viene un valor, `DatoInvalido`.
- La entidad `Usuario` no cambia y sigue sin `password_hash`.

La regla vive en dominio y no en el router (regla dura 8); el router solo busca el profesional con `obtener_profesional_por_id` y le pasa la entidad a la función pura.

### 3.3 Repositorio

**Archivo nuevo `app/db/repositorio_usuarios.py`** (SQL parametrizado, regla dura 4):

- `crear_usuario(conexion, *, username, password_hash, rol, profesional_id=None, activo=True) -> Usuario`: wrapper sobre `insertar_usuario` de `app/db/repositorio.py` que traduce `sqlite3.IntegrityError` de `UNIQUE(username)` a `UsernameDuplicado`. No duplica el SQL de inserción.
- `listar_usuarios(conexion) -> list[Usuario]` ordenado por `id ASC` (activos e inactivos).
- `actualizar_usuario(conexion, id_usuario, *, password_hash=None, rol=..., profesional_id=..., activo=...) -> Usuario | None` con centinela `_SIN_CAMBIO` para distinguir "omitido" de "null".

`app/db/repositorio.py` **no se modifica**: `buscar_credenciales`, `buscar_usuario_por_id` e `insertar_usuario` quedan intactas para no tocar login ni seed. Para leer un usuario por id se reutiliza `buscar_usuario_por_id`.

### 3.4 Router

`app/api/usuarios.py`, montado en `app/main.py`:

| Ruta | Status | Roles |
|---|---|---|
| `GET /usuarios` | 200 / 401 / 403 | solo administración |
| `POST /usuarios` | 201 / 409 / 422 / 401 / 403 | solo administración |
| `PATCH /usuarios/{id}` | 200 / 404 / 409 / 422 / 401 / 403 | solo administración |

- Todas usan `requiere_rol(Rol.ADMINISTRACION)`; recepción y odontólogo → `403 sin_permiso`; sin token → `401 no_autenticado`.
- `UsuarioSalida` explícito: `id`, `username`, `rol`, `profesional_id`, `activo`. Nunca `password_hash`.
- El router hashea la contraseña con `hashear()` (capa API, igual que el seed de `C-03`); el dominio nunca recibe texto plano.
- Escrituras dentro de `transaccion()`; lectura por request con `obtener_conexion` (patrón C-04/C-05/C-06).
- `PATCH` sin `PUT`/`DELETE`: la baja es `activo = false`.

## 4. El problema de diseño central: transiciones de rol en `PATCH`

Validar la invariante de forma literal deja la transición **imposible en un solo request**:

- `PATCH {rol: "recepcion"}` sobre un odontólogo falla porque todavía tiene `profesional_id`.
- `PATCH {profesional_id: null}` sobre un odontólogo falla porque sigue siendo odontólogo.

Decisión cerrada: **al cambiar el rol a un valor distinto de `odontologo`, el servidor limpia `profesional_id` automáticamente**. La simétrica: si el rol pasa a `odontologo`, el request debe traer un `profesional_id` existente y activo en el mismo PATCH; si no, `422` sin modificar el usuario.

```
PATCH rol=recepcion   -> profesional_id := NULL      (automático)
PATCH rol=odontologo  -> profesional_id obligatorio  (422 si falta o no sirve)
PATCH sin rol         -> se valida el rol actual contra el profesional_id candidato
```

## 5. Decisiones cerradas

1. **Reset de contraseña = campo `password` opcional en `PATCH /usuarios/{id}`.** Si viene, se hashea y se actualiza; si se omite, el hash no cambia. No hay endpoint dedicado.
2. **Sin política nueva de contraseña.** Se mantiene `min_length=1` como en `POST /auth/login`. No se agrega una regla de largo mínimo: queda registrado como riesgo/pregunta abierta en el design, no como requisito.
3. **`username` es inmutable en `PATCH`.** Si el body trae `username` (aunque sea `null` o igual al actual) → `422 dato_invalido` con mensaje explícito en español, sin modificar el usuario. El mecanismo concreto (campo declarado + rechazo explícito o `extra="forbid"` con mensaje mapeado) se define en el design.
4. **`username` duplicado → `409 username_duplicado`.** Se agrega `UsernameDuplicado(ErrorDominio)` en `app/domain/errores.py` y su entrada `(409, "username_duplicado")` en `MAPEO_DOMINIO` de `app/api/errores.py`. Es el **único código de error nuevo** del change. El mensaje en español no repite el username recibido.
5. **Profesional inexistente, inactivo o ausente para odontólogo → `422 dato_invalido`.** Se usa `DatoInvalido`, que ya está mapeado; no se crea código nuevo ni se usa `404`/`409`.
6. **Repositorio nuevo `app/db/repositorio_usuarios.py`.** Concentra `crear_usuario`, `listar_usuarios` y `actualizar_usuario`; `app/db/repositorio.py` queda intacto (login y seed no se tocan).
7. **Sin cambios de esquema.** No se toca `app/db/esquema.sql` ni se agregan migraciones.
8. **`GET /usuarios` completo.** Devuelve activos e inactivos ordenados por `id ASC`, sin filtros ni paginación; solo administración.
9. **`PATCH` parcial con `exclude_unset=True`.** `rol`, `activo` y `profesional_id` no son anulables donde la invariante lo impide; `password` omitido no cambia nada.
10. **Sin auditoría de usuarios.** IF-06 define que el MVP audita solo turnos; se documenta como decisión explícita.
11. **Sin `DELETE` ni baja física.** La desactivación es `activo = false`; un usuario desactivado sigue listándose.
12. **Capability nueva `usuarios`.** El CRUD vive en su propio spec (como `pacientes`/`profesionales`); `acceso-usuarios` queda para login y RBAC, con referencia cruzada. El delta de `errores-api` suma `username_duplicado`.

## 6. Preguntas abiertas

Ninguna bloqueante. Dos temas quedan derivados al design **como riesgos, no como reglas**:

- **Política de contraseña:** el MVP no impone largo mínimo porque la KB no lo pide y el login ya acepta `min_length=1`. Se registra el riesgo de contraseñas débiles y la posibilidad de endurecerlo en un change futuro.
- **Auto-bloqueo del administrador:** un admin único puede desactivarse a sí mismo o quitarse el rol y dejar el sistema sin administración. Fuera de scope de C-07; se documenta como riesgo operativo.

## 7. Riesgos del change

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Romper `C-03` al tocar el acceso a usuarios | Login y RBAC | `repositorio.py` no se modifica; el CRUD va en `repositorio_usuarios.py` |
| `usuario` ya tiene filas (`admin_demo`) | Migración | Sin cambios de esquema; el change es solo aditivo en código |
| Fuga de `password_hash` en una respuesta | Seguridad (RN-ACC-04) | `UsuarioSalida` explícito + test que fija `"password_hash" not in respuesta` en las tres rutas |
| Contraseñas débiles (`min_length=1`) | Seguridad | Riesgo aceptado y documentado; sin regla nueva por decisión del equipo |
| Un admin se deja afuera del sistema | Operación | Fuera de scope; riesgo documentado en el design |
| Transición de rol imposible en un paso | Contrato de la API | Limpieza automática de `profesional_id` al salir de `odontologo` |
| `profesional_id` sin FK en la base | Integridad | Validación en aplicación (decisión definitiva de `C-03`) |
| Usuario desactivado con token vigente | Acceso | Ya resuelto por `usuario_actual`, que recarga el usuario en cada request; se verifica de punta a punta |
| Divergencia de estilo con C-04/C-05/C-06 | Consistencia | Mismas firmas `validar_datos_*`, `transaccion()` y `exclude_unset=True` |
| Regresión de los 393 tests | Estabilidad | Correr la suite completa al cerrar el change |

## 8. Escenarios candidatos para el delta de spec

- **Alta:** admin crea recepción → 201 sin `password_hash`; crea odontólogo con profesional activo → 201; odontólogo sin `profesional_id` → 422; con profesional inexistente → 422; con profesional inactivo → 422; no-odontólogo con `profesional_id` → 422; `username` duplicado → 409 `username_duplicado`; `password` vacía → 422; sin token → 401; recepción y odontólogo → 403 `sin_permiso`.
- **Listado:** admin ve activos e inactivos ordenados por `id`; recepción → 403; sin token → 401.
- **Edición:** `rol` recepción → odontólogo con profesional válido; odontólogo → recepción limpia `profesional_id`; desactivar y reactivar; `password` nueva cambia el hash y permite login; `password` omitida no cambia el hash; `username` en el body → 422 sin modificar; `id` inexistente → 404 `no_encontrado`.
- **Integración con auth:** usuario desactivado por PATCH no puede loguear (`401 credenciales_invalidas`) y su token vigente pasa a `401 no_autenticado`.

## 9. Próximo paso

El change quedó chico y sin sorpresas: **no toca `esquema.sql`**, agrega un repositorio y un router nuevos, una función de validación pura en `app/domain/usuarios.py` y **un solo código de error nuevo** (`username_duplicado`). Los 422 de profesional inválido reutilizan `DatoInvalido`, que ya está mapeado.

Sigue `/opsx:propose` para escribir proposal + specs + design + tasks.
