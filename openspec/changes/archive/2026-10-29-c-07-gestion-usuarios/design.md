# Design — C-07 gestion-usuarios

## Context

Ver `proposal.md` §Why. Estado y restricciones que condicionan el enfoque:

- `C-03` creó la tabla `usuario`, la entidad `Usuario` (deliberadamente sin `password_hash`), el enum `Rol`, `hashear`/`verificar` (Argon2id), `usuario_actual` y `requiere_rol`. El login ya recarga el usuario en cada request, así que desactivar una cuenta invalida su token sin trabajo adicional.
- `C-04` aporta `obtener_profesional_por_id`, que distingue activo de inactivo.
- `C-04`/`C-05`/`C-06` fijaron el patrón: dataclass + `validar_datos_*` puro, repositorio dedicado con centinela `_SIN_CAMBIO`, router con `exclude_unset=True`, escrituras en `transaccion()` y errores mapeados en `app/api/errores.py`.
- Reglas duras aplicables (`AGENTS.md`): 1 (dominio puro), 4 (SQL parametrizado), 7 (errores en español con código), 8 (reglas de negocio en `app/domain/`), 9 (secretos solo por entorno), 11 (cada RN con test), 12 (`snake_case` y type hints).
- Línea base: 393 tests verdes. Sin cambios de esquema ni migraciones: la tabla `usuario` ya tiene todas las columnas.

## Goals / Non-Goals

**Goals:**

- CRUD administrativo de usuarios con la invariante rol ↔ profesional validada en dominio puro.
- Alta y edición sin tocar las funciones de login de `app/db/repositorio.py`.
- Hash nuevo en cada creación y en cada reset; ninguna respuesta expone `password_hash`.
- Traducir `UNIQUE(username)` a un `409` estable y carrera-seguro.
- Tests por capa: dominio, repositorio y API.

**Non-Goals:**

- Política de contraseña más estricta que la del login (`min_length=1`).
- Guardas contra el auto-bloqueo del administrador (auto-desactivarse o quitarse el rol).
- Auditoría de gestión de usuarios (IF-06: el MVP audita solo turnos).
- Renombrar `username`, borrado físico, `PUT`/`DELETE`, filtros o paginación.
- Cambios en `app/db/esquema.sql`, `app/db/repositorio.py`, `app/db/seed.py`, `app/api/auth.py` o `app/api/seguridad.py`.

## Decisions

- **D1 — Sin cambios de esquema.** La tabla `usuario` de `C-03` ya tiene `username UNIQUE`, `rol CHECK`, `profesional_id` nullable sin FK y `activo CHECK`. No se toca `app/db/esquema.sql` ni se migran datos.
  *Por qué:* el proyecto no tiene sistema de migraciones y `CREATE TABLE IF NOT EXISTS` no altera tablas existentes; agregar columnas exigiría rehacer la tabla sin necesidad.

- **D2 — Dominio puro en `app/domain/usuarios.py`.** Se agregan:
  - `validar_username(username: str) -> str`: `strip()` y rechazo de vacío con `DatoInvalido`.
  - `validar_datos_usuario(*, rol: Rol, profesional_id: int | None, profesional: Profesional | None) -> tuple[Rol, int | None]`: aplica la invariante completa.
    - `rol == ODONTOLOGO`: `profesional_id` obligatorio, `profesional` no nulo, `profesional.activo` verdadero; si no, `DatoInvalido`.
    - `rol != ODONTOLOGO`: `profesional_id` debe ser `None`; si no, `DatoInvalido`.
  - `aplicar_cambios_usuario(actual: Usuario, *, rol: Rol | None = None, profesional_id: int | None | object = SIN_CAMBIO, activo: bool | None = None) -> tuple[Rol, int | None, bool]`: combina el estado actual con los campos provistos y aplica la limpieza automática de `profesional_id` al salir de `odontologo`. Usa un centinela `SIN_CAMBIO` propio del dominio para distinguir "omitido" de "null".
  *Por qué:* la invariante es una regla de negocio y no puede vivir en el router (regla dura 8). `Profesional` es una entidad de dominio, así que recibirla no viola la regla dura 1 (que prohíbe FastAPI y `app/db`/`app/api`, no los modelos del propio dominio).
  *Alternativas descartadas:* pasar booleanos (`existe`, `activo`) desde el router — esconde la regla y duplica semántica; usar `_SIN_CAMBIO` de `app/db` — invertiría la dependencia (dominio → db).

- **D3 — Repositorio nuevo, login intacto.** `app/db/repositorio_usuarios.py` define:
  - `crear_usuario(conexion, *, username, password_hash, rol, profesional_id=None, activo=True) -> Usuario`: envuelve `insertar_usuario` de `app/db/repositorio.py` en `try/except sqlite3.IntegrityError` y traduce `UNIQUE` a `UsernameDuplicado`; no duplica el SQL del alta.
  - `listar_usuarios(conexion) -> list[Usuario]` ordenado por `id ASC` (activos e inactivos).
  - `actualizar_usuario(conexion, id_usuario, *, password_hash=SIN_CAMBIO, rol=SIN_CAMBIO, profesional_id=SIN_CAMBIO, activo=SIN_CAMBIO) -> Usuario | None` con `UPDATE` que reescribe todas las columnas y devuelve el usuario actualizado.
  - Para leer por id se reutiliza `buscar_usuario_por_id` de `repositorio.py`.
  *Por qué:* separa el CRUD administrativo del camino de autenticación sin duplicar SQL; `repositorio.py` queda intacto, tal como pidió el equipo.
  *Alternativa descartada:* agregar `listar`/`actualizar` a `repositorio.py` — mezcla responsabilidades y arriesga los tests de `C-03`.

- **D4 — Router y modelos Pydantic.** `app/api/usuarios.py` montado en `app/main.py`:
  - `UsuarioEntrada` (`username`, `password`, `rol`, `profesional_id`), `UsuarioActualizar` (todos opcionales), `UsuarioSalida` (`id`, `username`, `rol`, `profesional_id`, `activo`).
  - `UsuarioActualizar` declara `username: str | None = None` **a propósito**: si aparece en `model_fields_set`, el router lanza `DatoInvalido` con un mensaje explícito ("El username no se puede modificar.") en vez de caer en el mensaje genérico de Pydantic.
  - `password: str | None = Field(default=None, min_length=1)`; `null` explícito → `DatoInvalido`; omitido → el hash se conserva.
  - `rol: Rol | None`, `activo: bool | None`; `null` explícito → `422` (`DatoInvalido`), coherente con C-06.
  - `profesional_id: int | None = None`; `exclude_unset=True` distingue omitido de `null`.
  - El router hashea con `hashear()` antes de crear o resetear; el texto plano no pasa de la frontera.
  *Por qué:* Pydantic valida forma y tipo en la frontera; el dominio valida la regla (regla dura 8). Declarar `username` en lugar de `extra="forbid"` permite un mensaje específico y no convierte un typo del cliente en un `422` genérico.

- **D5 — Flujo de alta.** `POST /usuarios`: validar username en dominio → `validar_datos_usuario` con el `Profesional` obtenido por `obtener_profesional_por_id` → hashear → `crear_usuario` dentro de `transaccion()` → `UsuarioSalida` con `201`.
  *Por qué:* el `UNIQUE` se resuelve dejando fallar la base dentro de la transacción, sin `SELECT` previo que abra una carrera.

- **D6 — Flujo de edición.** `PATCH /usuarios/{id}` dentro de `transaccion()`:
  1. `buscar_usuario_por_id`; si no existe → `HTTPException(404)` (`no_encontrado`).
  2. Rechazar `username` presente en `model_fields_set` → `DatoInvalido`.
  3. `aplicar_cambios_usuario(...)` para obtener `(rol_candidato, profesional_id_candidato, activo_candidato)`.
  4. Si `profesional_id_candidato` no es nulo, `obtener_profesional_por_id` y `validar_datos_usuario(...)`.
  5. Si vino `password`, `hashear(password)`; si no, conservar el hash con el centinela.
  6. `actualizar_usuario(...)` → `200`.
  *Por qué:* mantiene la invariante en un solo paso (incluida la transición odontólogo → recepción) y valida y escribe en la misma transacción.

- **D7 — `UsernameDuplicado` → `409 username_duplicado`.** Se agrega el error en `app/domain/errores.py` y su entrada `(409, "username_duplicado")` en `MAPEO_DOMINIO`. El mensaje ("Ya existe un usuario con ese nombre de usuario.") no repite el valor recibido ni expone SQLite.
  *Por qué:* regla dura 7 y precedente de `DniDuplicado` en C-06. Es el único código de error nuevo.
  *Alternativa descartada:* reutilizar `NombreDuplicado` (`nombre_duplicado` no describe el conflicto) o un `HTTPException(409)` en el router (el handler genérico lo convertiría en `error_http`).

- **D8 — Salida explícita y sin secretos.** `UsuarioSalida` se construye campo por campo desde `Usuario`; nunca se serializa el hash. Los tests de API fijan `"password_hash" not in cuerpo` y `"password" not in cuerpo` en `GET`, `POST` y `PATCH`.
  *Por qué:* la entidad `Usuario` ya no tiene el hash, pero el contrato debe quedar blindado por test ante un cambio futuro.

- **D9 — Errores de la edición.** `404` vía el handler global; `422` vía `DatoInvalido` (rol/activo nulos, username presente, password vacía, profesional inválido); `409` vía `UsernameDuplicado` en el alta. No se usa `403` para errores de datos ni `400`.
  *Por qué:* mantiene el contrato de `errores-api` y la traducción centralizada.

- **D10 — Organización de specs.** Capability nueva `usuarios` para el CRUD; delta de `errores-api` para `username_duplicado`. `acceso-usuarios` no cambia: su requirement de datos de usuario ya delega en C-07 la validación del profesional y el comportamiento de login/RBAC es el mismo.
  *Por qué:* consistente con `pacientes`, `profesionales`, `sillones` y `prestaciones`; evita un spec de autenticación que crezca sin límite.

## Risks / Trade-offs

- **[Auto-bloqueo del administrador]** Un admin único puede desactivarse o quitarse el rol y dejar el sistema sin administración → Fuera de scope por decisión del equipo; se documenta como riesgo operativo y se mitiga con backups/seed en desarrollo. Un change futuro puede agregar guardas.
- **[Contraseñas débiles]** `min_length=1` no impide contraseñas triviales → Riesgo aceptado para el MVP por decisión del equipo; no se agrega una regla que la KB no pide. Endurecerlo es un change posterior.
- **[Transición de rol]** Cambiar `rol` y `profesional_id` en requests separados puede confundir al cliente → Limpieza automática al salir de `odontologo` y `422` explícito al entrar sin profesional; los escenarios del spec fijan el contrato.
- **[`profesional_id` sin FK]** La base no impide un id huérfano → Validación en aplicación en alta y edición; es una decisión definitiva de `C-03` (SQLite no permite agregar FK sin rehacer la tabla).
- **[Fuga del hash]** Una respuesta futura podría serializar la entidad completa → `UsuarioSalida` explícito y tests que fijan la ausencia de `password_hash`.
- **[Regresión en login]** Tocar `repositorio.py` rompería `C-03` → No se modifica; el CRUD vive en un módulo nuevo y reutiliza solo lectura.
- **[Doble request de profesionales]** El flujo de edición puede consultar el profesional dos veces (candidato y validación) → Aceptable: son lecturas por id dentro de la misma transacción y el volumen del MVP es mínimo.
- **[`usuario` con filas existentes]** `admin_demo` ya existe en development → El change no migra ni resiembra; el listado lo incluye y el alta no lo toca.
- **[Suite de 393 tests]** Un cambio en el mapeo de errores o en `main.py` puede afectar tests globales → Correr la suite completa y agregar los tests nuevos en los mismos módulos por capa.
- **[Integración con C-09 y C-12]** Las ramas de C-09 (bloqueos) y C-12 (cancelar-turno), aún sin mergear, también modifican `app/main.py`, `app/domain/errores.py` y `app/api/errores.py` → conflicto textual esperable al integrar. Mitigación: `git merge origin/main` antes de cerrar el apply, conservar las entradas de ambos changes y correr la suite completa.

## Migration Plan

No hay migración de datos ni de esquema. El despliegue es aditivo: se agregan módulos y el montaje del router. Rollback = quitar el router de `app/main.py` y borrar los archivos nuevos; la tabla `usuario`, el login y los usuarios existentes no se ven afectados.

## Open Questions

Ninguna bloqueante. Quedan para una iteración futura, sin cambiar specs ni tareas de este change: política de contraseña (largo mínimo/complejidad) y guardas de auto-bloqueo del administrador.
