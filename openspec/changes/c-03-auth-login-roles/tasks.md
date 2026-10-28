# Tasks — C-03 auth-login-roles

> **Strict TDD**: en cada tarea con código, primero se escribe el test y se ve fallar (RED), después va el mínimo código para que pase (GREEN), luego se triangula con un segundo caso y por último se refactoriza con la suite en verde.
> **Governance CRÍTICO**: el apply se hace por grupos, con un checkpoint con el equipo al cerrar cada grupo.
> Todos los usuarios, contraseñas y secretos de los tests son ficticios (por ejemplo `recepcion_ficticia` / `clave-ficticia-123`, y secretos de 32 caracteres o más rotulados como ficticios).

## 1. Red de seguridad y dependencias

- [x] 1.1 Correr `pytest tests` antes de tocar nada y registrar el baseline, verificando que todos los tests actuales (dominio de C-10 y API de C-01) pasan. Si alguno falla, se reporta como falla previa y no se corrige en este change.
- [x] 1.2 Agregar `PyJWT>=2.10` y `pwdlib[argon2]>=0.2` a `requirements.txt` e instalarlas en el `.venv`, verificando que `pip install -r requirements.txt` termina sin error, que `python -c "import jwt, pwdlib; from pwdlib.hashers.argon2 import Argon2Hasher"` funciona y que `pytest tests` sigue en verde.

## 2. Ajustes a la base técnica de C-01

- [x] 2.1 _(check_same_thread=False resuelto por Belén en PR #31; este test cubre el cierre desde otro hilo: `test_abrir_conexion_se_puede_cerrar_desde_otro_hilo`)_ Escribir en `tests/api/test_conexion.py` un test que abre una conexión con `abrir_conexion` en el hilo principal y ejecuta `SELECT 1` y `close()` desde un `threading.Thread`. Verificar que falla en RED con `ProgrammingError`. Después pasar `check_same_thread=False` en `abrir_conexion` y su docstring, verificando que el test nuevo y los 5 tests existentes de conexión pasan.
- [x] 2.2 Escribir tests en `tests/api/test_config.py` para los defaults de autenticación (entorno vacío → `HS256`, `60` minutos, sin contraseña de seed, secreto no vacío) y para un `JWT_SECRET` explícito, que se respeta tal cual. Sumar los campos a `Config` y a `cargar_config`, verificando que los tests nuevos y los 3 existentes pasan.
- [x] 2.3 Escribir tests de que `APP_ENV=test` sin `JWT_SECRET` produce dos secretos distintos en dos cargas, y de que `APP_ENV=production` sin `JWT_SECRET` lanza `ConfigInvalida` con un mensaje que nombra `JWT_SECRET`. Implementar el secreto aleatorio solo para `development`/`test`, verificando que ningún secreto queda escrito en el código (búsqueda en `app/config.py`).
- [x] 2.4 Escribir tests de que `ACCESS_TOKEN_EXPIRE_MINUTES=abc` y `=0`, y `JWT_ALGORITHM=none`, lanzan `ConfigInvalida` con un mensaje que nombra la variable, y de que `HS512` se acepta. Implementar las validaciones, verificando que los tests pasan.
- [x] 2.5 Escribir tests de que `GET /docs` y `GET /openapi.json` responden `200` con `APP_ENV=development` y `404` con `APP_ENV=test`. Condicionar `docs_url`, `redoc_url` y `openapi_url` en `create_app`, verificando que los tests pasan y que `tests/api/test_main.py` sigue en verde.

## 3. Formato global de errores (RN-GLO-01)

- [x] 3.1 Crear `tests/api/rutas_prueba.py` con un router solo de test con rutas que lanzan `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo` y `DatoInvalido`, y la fixture `cliente_con_rutas_prueba` en `tests/conftest.py`. Escribir tests de que cada ruta responde `409` (`conflicto_agenda`, `fuera_de_horario`, `dentro_de_bloqueo`) o `422` (`dato_invalido`) con exactamente `{codigo, mensaje}` y el `mensaje` del error de dominio. Implementar `registrar_manejadores` en `app/api/errores.py` con la tabla de mapeo de dominio y llamarla desde `create_app`, verificando que los tests pasan.
- [x] 3.2 Escribir un test que recorre las subclases de `ErrorDominio` y verifica que todas tienen entrada en la tabla de mapeo, y otro que verifica que una subclase sin mapeo (definida en el test) responde `500` con `codigo` `error_interno`. Implementar el fallback, verificando que los tests pasan.
- [x] 3.3 Escribir tests de que `GET /no-existe` responde `404` con `codigo` `no_encontrado` y de que un método no admitido sobre una ruta de prueba responde `405` con `metodo_no_permitido`, ambos sin la clave `detail`. Implementar el handler de `StarletteHTTPException`, verificando que los tests pasan.
- [x] 3.4 Escribir tests sobre una ruta de prueba con un body Pydantic: `{}` devuelve `422` `dato_invalido` con `detalles` para cada campo faltante ("Campo obligatorio."), y un tipo incorrecto devuelve `detalles` con `campo` sin el prefijo `body` y `mensaje` en español. Un error de todo el cuerpo (body que no es un objeto o JSON mal formado) devuelve `campo` `"body"`. Implementar el handler de `RequestValidationError` con el diccionario de mensajes por `type`, verificando que los tests pasan.
- [x] 3.5 Definir `ErrorApi`, `NoAutenticado`, `SinPermiso` y `CredencialesInvalidas` en `app/api/errores.py`, con tests sobre rutas de prueba que las lanzan. Verificar que responden `401` (`no_autenticado` / `credenciales_invalidas`) con la cabecera `WWW-Authenticate: Bearer` y `403` (`sin_permiso`) sin esa cabecera, todas en formato `{codigo, mensaje}`.

## 4. Usuarios en dominio y persistencia

- [x] 4.1 Escribir tests en `tests/domain/test_usuarios.py` de que `Rol` tiene exactamente `administracion`, `recepcion` y `odontologo`, y de que `Usuario` es inmutable y no tiene atributo `password_hash`. Implementar `app/domain/usuarios.py` en Python puro, verificando que los tests pasan y que el módulo no importa `fastapi`, `app.db` ni `app.api`.
- [x] 4.2 Escribir tests en `tests/api/test_esquema_usuario.py` (base temporal + `inicializar_esquema`):
  - la tabla `usuario` existe después del arranque;
  - un `username` duplicado lanza `IntegrityError`;
  - el rol `paciente` lanza `IntegrityError`;
  - un administrador con `profesional_id` NULL se inserta sin error;
  - aplicar el esquema dos veces no falla.

  Agregar la tabla a `esquema.sql` con el comentario sobre la ausencia de FK, verificando que los tests pasan.
- [x] 4.3 Escribir tests en `tests/api/test_repositorio.py`:
  - `insertar_usuario` devuelve el id;
  - `buscar_credenciales` devuelve `(Usuario, hash)` para un username existente y `None` para uno inexistente;
  - `buscar_usuario_por_id` devuelve el usuario con su `activo` y su `rol` actuales.

  Implementar `app/db/repositorio.py` con consultas parametrizadas, verificando que los tests pasan y que no hay SQL armado con f-strings ni con `%` (búsqueda en el archivo).

## 5. Hash y token (sin HTTP)

- [x] 5.1 Escribir tests en `tests/api/test_seguridad.py`:
  - `hashear("clave-ficticia-123")` no es igual a la contraseña ni la contiene;
  - dos hashes de la misma contraseña son distintos;
  - `verificar` acepta la contraseña correcta y rechaza `otra-clave-ficticia`.

  Implementar `hashear` y `verificar` con `pwdlib` Argon2id, verificando que los tests pasan (RN-ACC-04).
- [x] 5.2 Escribir tests de `emitir_token(..., ahora)` y `decodificar_token(..., ahora)`, con `ahora` como **parámetro obligatorio** y un instante fijo `T` (por ejemplo `2026-01-05T12:00:00+00:00`):
  - la ida y vuelta en `T` conserva `sub` (string) y `rol`;
  - `exp - iat` es igual a `ACCESS_TOKEN_EXPIRE_MINUTES` minutos;
  - un token emitido en `T`, decodificado con `ahora = T + 59 min`, es válido;
  - con `ahora = T + 60 min` (el límite exacto) lanza `TokenVencido`;
  - con `ahora = T - 1 min` (`iat` en el futuro) es inválido;
  - un token firmado con otra clave, uno con `alg: none` y uno sin `sub` lanzan error.

  Implementar con PyJWT (`algorithms` fijo, `verify_exp`/`verify_iat` desactivados) y la comparación de tiempo propia contra `ahora`, verificando que los tests pasan y que `app/api/seguridad.py` no llama a `datetime.now`.

## 6. Login y autorización

- [x] 6.1 Implementar `obtener_conexion` en `app/api/dependencias.py` (abre la conexión, hace `yield` y cierra en `finally`), con un test sobre una ruta de prueba que la usa. Verificar que la ruta responde sin `ProgrammingError` de hilo y que la conexión queda cerrada después del request.
- [x] 6.1b Agregar a `tests/conftest.py` `RelojFijo` (instante inicial fijo en UTC, `__call__` y `avanzar(minutes=...)`) y la fixture `reloj`, y hacer que `cliente` y `cliente_con_rutas_prueba` pasen `reloj` a `create_app`. Escribir tests de que una ruta de prueba que depende de `obtener_ahora` devuelve el instante del `RelojFijo`, y de que avanza después de `avanzar(...)`. Implementar el parámetro `reloj` de `create_app` (guardado en `app.state.reloj`, default `datetime.now(timezone.utc)`) y `obtener_ahora` en `app/api/dependencias.py`, verificando que los tests pasan y que el default de `create_app` es el único lugar de `app/` que lee la hora real.
- [x] 6.2 Agregar a `tests/conftest.py` las fixtures `crear_usuario` (que inserta un usuario ficticio con hash real) y `token_de` (que emite un token para un usuario usando el instante actual del `RelojFijo`). Escribir el test de que `POST /auth/login` con `recepcion_ficticia` / `clave-ficticia-123` responde `200` con `token_type` `bearer` y un `access_token` decodificable con el id y el rol del usuario. Implementar el router de `app/api/auth.py` y montarlo en `create_app`, verificando que el test pasa.
- [x] 6.3 Escribir tests de que el login con un usuario inexistente, con una contraseña incorrecta y con un usuario inactivo responde `401` `credenciales_invalidas`, y de que los tres cuerpos son **idénticos**. Implementar la verificación contra el hash ficticio cuando el usuario no existe, verificando que los tests pasan.

  > **Nota para el verify: tests de la 6.3 sin fase RED propia** (todos en `tests/api/test_auth.py`):
  > - `test_login_de_usuario_inexistente_responde_credenciales_invalidas` y `test_login_con_contrasena_incorrecta_responde_credenciales_invalidas`: pasaron en el primer intento, porque la 6.2 ya rechazaba esos dos casos (era necesario para manejar el `None` de `buscar_credenciales` y para no aceptar cualquier contraseña).
  > - `test_los_tres_logins_fallidos_devuelven_el_mismo_cuerpo`: sí falló, pero solo por el caso del usuario inactivo. Su RED no es independiente del de `test_login_de_usuario_inactivo_responde_credenciales_invalidas`.
  > - `test_el_hash_ficticio_se_calcula_una_sola_vez` y `test_usuario_inactivo_igual_verifica_su_contrasena`: son tests de triangulación escritos después del GREEN, y pasaron en el primer intento.
  >
  > Con RED propio: `test_login_de_usuario_inactivo_responde_credenciales_invalidas` (respondía `200`) y `test_usuario_inexistente_igual_verifica_contra_un_hash_ficticio` (`verificar` no se llamaba).
- [x] 6.4 Escribir tests de que `POST /auth/login` con `{}`, con `password` faltante y con `password` numérico responde `422` `dato_invalido` con `detalles` del campo correspondiente. Verificar que pasan con el handler del grupo 3 y el modelo Pydantic con `min_length=1`.

  > **Nota para el verify: ningún test de la 6.4 tiene fase RED propia.** Es una tarea de verificación. El handler de validación es del grupo 3 y el modelo con `min_length=1` es de la 6.2. Los cuatro tests de `tests/api/test_auth.py` pasaron en el primer intento: body vacío, `password` faltante, `password` numérico y, como triangulación, `username` y `password` vacíos.
  >
  > Para comprobar que el último test detecta la falta de `min_length`, hice una prueba de mutación manual: saqué `Field(min_length=1)` de `CredencialesEntrada`, el test falló (`1 failed, 15 passed`), y restauré el archivo con `git checkout`.
- [x] 6.5 Escribir tests sobre `GET /prueba/autenticado`: sin cabecera, con `Basic ...`, con texto arbitrario y con un token firmado con otra clave, todos `401` `no_autenticado` con la cabecera `WWW-Authenticate: Bearer`. Con un token válido debe responder `200`. Implementar `usuario_actual` con `HTTPBearer(auto_error=False)`, validando el token con `obtener_ahora`, verificando que los tests pasan (RN-ACC-01).

  > **Nota para el verify: RED de la 6.5** (todos en `tests/api/test_usuario_actual.py`):
  > - Los 6 tests de la tarea fallaron juntos por un mismo motivo: `ImportError`, porque `usuario_actual` no existía. Es un RED compartido; ninguno falló por su comportamiento particular. Son: sin cabecera, `Basic`, texto arbitrario sin esquema, texto arbitrario como `Bearer`, otra clave y token válido.
  > - Sin RED propio, porque pasaron en el primer intento: `test_token_con_algoritmo_none_responde_no_autenticado`, `test_token_valido_de_un_usuario_que_no_existe_responde_no_autenticado` y `test_cada_token_valido_identifica_a_su_propio_usuario`. Son de triangulación.
  > - Con RED propio: `test_token_firmado_por_el_sistema_con_sub_no_numerico_responde_no_autenticado`. Falló con `ValueError`, que en producción habría sido un 500, y se corrigió capturando el `ValueError` de `int(sub)`.
  > - Uso de `obtener_ahora`: no tiene un test aparte. Lo cubre `test_token_valido_responde_200_con_el_usuario`, porque el token vence en `2026-01-05T13:00Z` y con la hora real de la máquina ya estaría vencido.
  > - `usuario_actual` todavía no rechaza a los usuarios inactivos: lo agrega la 6.6, con su propio RED.
- [x] 6.5b Escribir el test de **token vencido moviendo el reloj fijo, sin esperar**:
  - login de `recepcion_ficticia` con el `RelojFijo` en `T` (`ACCESS_TOKEN_EXPIRE_MINUTES=60`);
  - `reloj.avanzar(minutes=59)` → `GET /prueba/autenticado` responde `200`;
  - `reloj.avanzar(minutes=1)` (en `T + 60`) → responde `401` `no_autenticado` con `WWW-Authenticate: Bearer`.

  Verificar que el test pasa, que no usa `sleep` y que su resultado no cambia con la hora real de la máquina.

  > **Nota para el verify: el test de la 6.5b no tiene fase RED propia.** Es `test_el_token_vence_al_mover_el_reloj_fijo_sin_esperar`, en `tests/api/test_usuario_actual.py`, y pasó en el primer intento, porque el login (6.2), el reloj (6.1b) y `usuario_actual` (6.5) ya existían.
  >
  > Para comprobar que detecta el borde del vencimiento, hice una prueba de mutación manual: cambié `exp <= instante` por `exp < instante` en `decodificar_token`, y el test falló en T+60 (`200 == 401`). Restauré el archivo editándolo y `git diff app/` quedó vacío.
  >
  > Una búsqueda en el test de `sleep`, `datetime.now` y `time.time` no encontró ningún uso. La única coincidencia es el comentario que lo aclara. El token vence en `2026-01-05T13:00Z`, así que el resultado no depende de la hora de la máquina.
- [x] 6.6 Escribir tests de que un token válido de un usuario desactivado después del login responde `401` `no_autenticado`, y de que un usuario cuyo rol cambió de `recepcion` a `odontologo` después del login recibe `403` en `GET /prueba/solo-recepcion`. Verificar que `usuario_actual` recarga el usuario desde la base y usa el rol guardado, no el del token.

  > **División acordada con el equipo:** el test del `403` en `GET /prueba/solo-recepcion` necesita `requiere_rol`, que llega en la 6.7, así que **se movió a la 6.7**. En la 6.6 quedó el test del usuario desactivado. Que se usa el rol guardado y no el del token se verifica sin `requiere_rol`: `GET /prueba/autenticado` devuelve el rol de la base.
  >
  > **Nota para el verify: RED de la 6.6** (todos en `tests/api/test_usuario_actual.py`):
  > - Con RED propio: `test_token_valido_de_un_usuario_desactivado_despues_del_login_responde_no_autenticado`, que respondía `200`.
  > - Sin RED propio, porque son de triangulación y pasaron en el primer intento: `test_usuario_actual_usa_el_rol_guardado_y_no_el_del_token` (desde la 6.5, `usuario_actual` ya recargaba el usuario desde la base) y `test_usuario_reactivado_vuelve_a_ser_aceptado_con_el_mismo_token`.
- [x] 6.7 Escribir tests de que `recepcion_ficticia` recibe `403` `sin_permiso` en `GET /prueba/solo-admin` y `200` en `GET /prueba/admin-o-recepcion`, y de que un `administracion_ficticia` recibe `200` en `solo-admin`. Implementar `requiere_rol(*roles)`, verificando que los tests pasan (RN-ACC-02, mecanismo). **Movido desde la 6.6:** escribir también el test de que un usuario cuyo rol cambió de `recepcion` a `odontologo` después del login recibe `403` en `GET /prueba/solo-recepcion`.

  > **Nota para el verify: RED de la 6.7** (todos en `tests/api/test_requiere_rol.py`):
  > - Los 4 tests de la tarea fallaron juntos por un mismo motivo: `ImportError`, porque `requiere_rol` no existía. Es un RED compartido; ninguno falló por su comportamiento particular. Son: recepción en `solo-admin`, recepción en `admin-o-recepcion`, administración en `solo-admin`, y el cambio de rol en `solo-recepcion`, que vino de la 6.6.
  > - Sin RED propio, porque son de triangulación y pasaron en el primer intento: `test_sin_token_una_ruta_con_rol_responde_401_y_no_403`, `test_odontologo_no_entra_a_una_ruta_de_admin_o_recepcion` (que también verifica que el 403 no lleva `WWW-Authenticate`) y `test_administracion_tambien_entra_a_una_ruta_de_admin_o_recepcion`.
- [x] 6.8 Escribir un test de punta a punta: crear `recepcion_ficticia` y loguearse; verificar que la fila de `usuario` no contiene `clave-ficticia-123` en ninguna columna y que la respuesta del login tampoco la contiene (RN-ACC-04). Verificar también que `GET /health` sigue respondiendo `200` sin token.

  > **Nota para el verify: ningún test de la 6.8 tiene fase RED propia.** Es una tarea de verificación de punta a punta sobre piezas que ya existían. Los cuatro tests de `tests/api/test_auth.py` pasaron en el primer intento:
  > - `test_la_contrasena_no_queda_en_la_base_ni_en_la_respuesta_del_login`;
  > - `test_health_sigue_respondiendo_200_sin_token`;
  > - `test_la_contrasena_no_aparece_en_ningun_byte_del_archivo_de_la_base` (triangulación);
  > - `test_health_ignora_un_token_invalido` (triangulación).
  >
  > Para comprobar que el primero detecta una fuga, hice una prueba de mutación manual: hice que el login devolviera `access_token=credenciales.password`, y el test falló (`'clave-ficticia-123' not in '{"access_to...'`). Restauré la línea editando el archivo y `git diff app/` quedó vacío.
  >
  > Límite conocido: hoy ningún código de `app/` inserta usuarios, porque los tests los crean con la fixture `crear_usuario`, que ya hashea. Por eso no hay una mutación de `app/` que haga que la contraseña se guarde en texto plano. Ese camino aparece con el seed (grupo 7), y lo cubren las tareas 7.x.

## 7. Seed de desarrollo

- [x] 7.1 Escribir tests en `tests/api/test_seed.py` de `sembrar_admin_demo` sobre una base temporal: la primera llamada crea un único `admin_demo` activo con rol `administracion`, y la segunda llamada con otro hash no crea duplicados ni cambia el `password_hash`. Implementar `app/db/seed.py` con `INSERT ... ON CONFLICT(username) DO NOTHING` dentro de `transaccion()`, verificando que los tests pasan y que `app/db/seed.py` no importa `app.api`.

  > **Nota para el verify: RED de la 7.1** (todos en `tests/api/test_seed.py`):
  > - Los 2 tests de la tarea fallaron juntos por un mismo motivo: `ModuleNotFoundError`, porque `app.db.seed` no existía. Es un RED compartido; ninguno falló por su comportamiento particular.
  > - Sin RED propio, porque son de triangulación y pasaron en el primer intento: `test_no_modifica_un_admin_demo_existente_aunque_este_inactivo_y_con_otro_rol`, `test_agrega_admin_demo_sin_tocar_a_los_demas_usuarios` y `test_el_seed_queda_confirmado_y_lo_ve_otra_conexion`.
  > - Límite conocido: que la escritura va "dentro de `transaccion()`" se verifica leyendo `app/db/seed.py`, no con un test. Como la conexión está en autocommit, el test de "otra conexión la ve" pasaría igual sin la transacción.
  > - Una búsqueda de `app.api` en `app/db/seed.py` no encontró ningún import.
- [x] 7.2 Escribir tests de arranque:
  - con `APP_ENV=development` y `SEED_ADMIN_PASSWORD=clave-demo-ficticia` existe `admin_demo`, y `POST /auth/login` con esas credenciales responde `200`;
  - dos arranques sobre la misma base dejan un solo `admin_demo`;
  - con `APP_ENV=test` y la variable definida, la tabla queda vacía;
  - con `development` sin la variable, el arranque no falla y la tabla queda vacía.

  Conectar el seed en el `lifespan`, verificando que los tests pasan.

  > **Nota para el verify: RED de la 7.2** (todos en `tests/api/test_seed.py`):
  > - Con RED propio: `test_en_development_con_la_variable_crea_admin_demo_y_permite_el_login` (el login daba `401`) y `test_dos_arranques_sobre_la_misma_base_dejan_un_solo_admin_demo` (`0 == 1`).
  > - Sin RED propio: `test_en_test_con_la_variable_no_crea_usuarios` y `test_en_development_sin_la_variable_arranca_y_no_crea_usuarios`. Son de la tarea, pero verifican que el seed *no* ocurre, así que pasaban antes de conectarlo.
  > - Sin RED propio, porque son de triangulación y pasaron en el primer intento: `test_en_production_con_la_variable_no_crea_usuarios`, `test_la_contrasena_del_seed_no_queda_en_el_archivo_de_la_base` y `test_rearrancar_con_otra_contrasena_no_cambia_la_de_admin_demo`.
  >
  > Prueba de mutación manual: hice que el `lifespan` pasara `seed_admin_password` sin hashear, y fallaron 3 tests (el login, el de los bytes del archivo y el de rearrancar). Restauré la línea editando el archivo. Este es el caso de "guardar la contraseña en texto plano" que en la 6.8 no se podía mutar desde `app/`.

## 8. Documentación

- [x] 8.1 **Edición manual de un integrante** (los permisos del agente no permiten leer ni escribir `.env.example`): agregar a `.env.example` los placeholders
  - `JWT_SECRET=<cambiar-por-un-valor-largo-y-aleatorio-de-32-caracteres-o-mas>`
  - `JWT_ALGORITHM=HS256`
  - `ACCESS_TOKEN_EXPIRE_MINUTES=60`
  - `SEED_ADMIN_PASSWORD=<definir-localmente>`

  Verificar que `git diff .env.example` muestra solo placeholders y que `git status` no lista ningún `.env`.
- [x] 8.2 Actualizar `README.md`:
  - las variables nuevas en la tabla y en los ejemplos de PowerShell y bash;
  - que sin `JWT_SECRET` fuera de development/test la app no arranca;
  - cómo crear `admin_demo` en desarrollo;
  - un ejemplo de `POST /auth/login` y del uso de `Authorization: Bearer`;
  - el formato de error `{codigo, mensaje, detalles?}`;
  - que `/docs` existe solo en development;
  - la sección "Estructura" con los archivos nuevos.

  Verificar que el ejemplo de login documentado funciona contra `uvicorn app.main:app` con `admin_demo`.

  > **Nota para el verify:**
  > - Los dos ejemplos de login del README (curl y PowerShell) se ejecutaron tal como están escritos contra `uvicorn app.main:app` en el puerto 8000, con `APP_ENV=development` y `SEED_ADMIN_PASSWORD=clave-demo-ficticia`. Respondieron `200` y `token_type` `bearer`.
  > - También se comprobaron contra la app real:
  >   - el `401` con `WWW-Authenticate: Bearer`;
  >   - el `422` con `detalles`;
  >   - `/docs` en `200` con development y en `404` con test;
  >   - el fallo de arranque sin `JWT_SECRET` con `APP_ENV=production`.
  > - El ejemplo de `Authorization: Bearer` usa `<ruta-protegida>` y **no se pudo ejecutar**, porque `app/` todavía no tiene rutas protegidas (llegan desde C-04). El mecanismo lo cubren los tests de las tareas 6.5 a 6.7.
  > - Fuera de la lista de la tarea, también actualicé "Estado actual": sumé C-03 y cambié `44 passed` por `194 passed`, que estaba desactualizado.

## 9. Verificación del change

- [x] 9.1 Correr `pytest tests` completo, verificando que pasan los tests del baseline de 1.1 y todos los nuevos, y que cada RN tocada (RN-ACC-01, RN-ACC-02 en su mecanismo, RN-ACC-04 y RN-GLO-01) tiene al menos un test.

  > **Resultado de la 9.1:** `pytest tests` dio `194 passed`, con 0 tests fallidos, con error, salteados o `xfail`. El único warning es el conocido `StarletteDeprecationWarning` de `httpx`.
  >
  > **Baseline:** extraje `app/` y `tests/` del merge-base con `main` (`d2041ee`) con `git archive`, a una carpeta temporal. Ahí la suite da `44 passed`. Los **44 IDs de ese baseline** están todos entre los aprobados de la suite actual, sin renombres ni bajas. Los otros **150 tests** no estaban en el baseline:
  > - **149 son de C-03.**
  > - **1 es de Belén**, del PR #31: `tests/api/test_conexion.py::test_abrir_conexion_se_puede_usar_desde_otro_hilo`, del commit `9507573`. Llegó a la rama después del merge-base, por eso no figura en el baseline.
  >
  > **Cobertura de las RN:**
  >
  > | RN | Archivo de tests | Tests | Qué verifica |
  > |---|---|---|---|
  > | RN-ACC-01 | `tests/api/test_usuario_actual.py` | 14 | Responde 401 `no_autenticado` con `WWW-Authenticate: Bearer` en estos casos: sin cabecera, `Basic`, texto arbitrario, otra clave, `alg: none`, usuario inexistente, `sub` no numérico, usuario desactivado y vencimiento en T+60 con el reloj fijo. Con un token válido responde 200. |
  > | RN-ACC-02 (mecanismo) | `tests/api/test_requiere_rol.py` | 7 | Con un rol no admitido responde 403 `sin_permiso`, y sin token responde 401. Autoriza el rol guardado en la base y no el del token. |
  > | RN-ACC-04 | `tests/api/test_seguridad.py`, `tests/api/test_auth.py` y `tests/api/test_seed.py` | 18 relevantes | Argon2id con sal, y el hash no contiene la contraseña. La contraseña no queda en la fila, en los bytes del `.db` ni en la respuesta del login, ni siquiera la del seed. Hay hash ficticio para usuarios inexistentes. |
  > | RN-GLO-01 | `tests/api/test_errores.py` | 17 | Formato `{codigo, mensaje, detalles?}` en español para 401, 403, 404, 405, 409, 422 y 500. |
- [x] 9.2 Verificar con una búsqueda de imports que `app/domain/` no importa `fastapi`, `jwt`, `pwdlib`, `app.db` ni `app.api`, y que `app/db/` no importa `fastapi` ni `app.api`.

  > **Resultado de la 9.2:** no se encontró ningún import prohibido.
  > - `app/domain/`: no importa `fastapi`, `starlette`, `jwt`, `pwdlib`, `app.db` ni `app.api`. Solo usa la biblioteca estándar y módulos de `app.domain`.
  > - `app/db/`: no importa `fastapi`, `starlette` ni `app.api`. De `app.domain` importa solo los tipos `Rol` y `Usuario` (`repositorio.py` y `seed.py`), como permite la regla dura 1.
  > - En los dos directorios: no hay imports relativos, ni dinámicos (`importlib`/`__import__`), ni de la forma `from app import api/db`.
  > - Control del patrón: la misma búsqueda sobre `app/api/` encuentra 16 imports, así que el "ninguno" es un resultado real y no un patrón roto.
- [x] 9.3 Verificar que no hay secretos versionados (búsqueda de `JWT_SECRET=` con valores reales y de contraseñas en `app/` y `tests/`), y que todos los usuarios y contraseñas de los tests están rotulados como ficticios.

  > **Resultado de la 9.3:** no hay secretos versionados.
  >
  > **`.env`:** no está versionado (`.gitignore:4`). El único archivo `.env*` en git es `.env.example`.
  >
  > **`JWT_SECRET`:**
  > - En `app/` no hay ningún valor asignado. El secreto sale del entorno o, en development/test, de `secrets.token_urlsafe`.
  > - En `tests/`, los 5 secretos literales dicen `ficticio` en su propio texto: `secreto-ficticio-de-test-...`, `secreto-ficticio-de-produccion-...` y `otra-clave-ficticia-...`.
  > - En el README y en este `tasks.md` solo aparecen los placeholders `cambiar-por-...`.
  > - En el historial `main..HEAD` (fuera de `openspec/`), las únicas líneas agregadas con `JWT_SECRET=` o `SEED_ADMIN_PASSWORD=` son esos placeholders y los de `.env.example`: `<cambiar-por-un-valor-largo-...>` y `<definir-localmente>`.
  >
  > **Contraseñas:**
  > - En `app/` no hay ningún literal de contraseña. El hash ficticio sale de `secrets.token_urlsafe`.
  > - En `tests/`, todos los valores dicen `ficticia`: `clave-ficticia-123`, `otra-clave-ficticia`, `clave-demo-ficticia`, `otra-clave-demo-ficticia` y las variantes de `test_seguridad.py`. Las excepciones son `""` y `123`, los casos de validación de la 6.4, que no son contraseñas.
  >
  > **Usuarios:** todos los de los tests dicen `ficticio`/`ficticia` (`recepcion_ficticia`, `odontologo_ficticio`, `administracion_ficticia`, `admin_ficticio`, `inactivo_ficticio`, `fantasma_ficticio` y `otro_fantasma_ficticio`), salvo `admin_demo`. Ese nombre lo fija el spec del seed. Es un usuario de demostración y su contraseña sí está rotulada (`clave-demo-ficticia`).
- [x] 9.4 Verificar con una búsqueda en `tests/` que ningún test usa `time.sleep`, `datetime.now`, `datetime.utcnow`, `date.today` ni `time.time`, y en `app/` que la única lectura de la hora real es el default del `reloj` en `create_app`.

  > **Resultado de la 9.4:**
  > - **`app/`:** la única lectura de la hora real es `_hora_real()` en `app/main.py`, que devuelve `datetime.now(UTC)`. Es el reloj por defecto de `create_app`.
  > - **`tests/`:** ninguna llamada a `time.sleep`, `sleep(`, `datetime.now`, `datetime.utcnow`, `date.today`, `time.time`, `.now(`, `.utcnow(` ni `.today(`. Tampoco hay imports de `time` ni de `freezegun`.
  >
  > **Corrección hecha en esta tarea, acordada con el equipo:** la primera búsqueda encontró `datetime.now(UTC)` en el test de la 6.1b `test_sin_reloj_inyectado_la_app_usa_la_hora_real_en_utc` (`tests/api/test_dependencias.py`). Ese test acotaba el reloj por defecto entre dos lecturas de la hora real.
  > - Se reescribió como `test_sin_reloj_inyectado_la_app_usa_datetime_now_en_utc`. Usa un doble de `datetime` en `app.main` (con `monkeypatch`) que devuelve `INSTANTE_INICIAL` y registra la zona pedida.
  > - Verifica que el reloj por defecto devuelve lo que da `datetime.now` y que lo pide en `UTC`.
  > - Prueba de mutación manual: cambié `datetime.now(UTC)` por `datetime.now()` en `_hora_real()`, y el test falló (`[None] == [UTC]`). Restauré la línea editando el archivo y `git diff app/` quedó vacío.
- [ ] 9.5 Correr `openspec validate c-03-auth-login-roles --strict`, verificando que no reporta errores.

## Workflow follow-up

- Implementar con `/opsx:apply c-03-auth-login-roles`, respetando las reglas duras de `AGENTS.md` y el checkpoint con el equipo al cierre de cada grupo (governance CRÍTICO).
- Verificar el change antes de archivar: suite en verde, login de `admin_demo` en development y `/health` respondiendo.
- Archivar con `/opsx:archive` y marcar `C-03` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
