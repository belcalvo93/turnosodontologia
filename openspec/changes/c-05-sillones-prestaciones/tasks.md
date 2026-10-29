# Tasks — C-05 sillones-prestaciones

## 1. Dominio puro y contrato de error 409

- [x] 1.1 Escribir primero `tests/domain/test_sillones.py` y `tests/domain/test_prestaciones.py` (nombre con `strip()`, nombre vacío/de espacios → `DatoInvalido`, duración `0` y negativa → `DatoInvalido`, duración válida devuelta, default `activo`/`activa` en `True`) y luego implementar `Sillon` y `validar_datos_sillon()` / `validar_datos_prestacion()` en `app/domain/models.py`; verificar con `pytest tests/domain/test_sillones.py tests/domain/test_prestaciones.py`
- [x] 1.2 Agregar `NombreDuplicado` en `app/domain/errores.py` y su entrada `(409, "nombre_duplicado")` en `MAPEO_DOMINIO` de `app/api/errores.py`; verificar sumando la ruta de prueba y el caso parametrizado en `tests/api/test_errores.py` que comprueban `409` con `{"codigo": "nombre_duplicado", "mensaje": <español>}` mediante `pytest tests/api/test_errores.py`

## 2. Esquema SQLite y repositorios

- [x] 2.1 Agregar `CREATE TABLE IF NOT EXISTS sillon` y `CREATE TABLE IF NOT EXISTS prestacion` al final de `app/db/esquema.sql` (nombre `NOT NULL UNIQUE` con `CHECK (length(trim(nombre)) > 0)`, `duracion_minutos CHECK (> 0)`, `activo`/`activa` con default `1` y `CHECK IN (0,1)`); verificar con `pytest tests/api/test_repositorio_sillones.py tests/api/test_repositorio_prestaciones.py` que `inicializar_esquema()` es idempotente y que cada `CHECK`/`UNIQUE` rechaza con `sqlite3.IntegrityError`
- [x] 2.2 Implementar `app/db/repositorio_sillones.py` (`crear_sillon`, `listar_sillones`, `obtener_sillon_por_id`, `actualizar_sillon` con centinela `_SIN_CAMBIO`, SQL parametrizado y traducción de `IntegrityError` con `UNIQUE` a `NombreDuplicado`); verificar con `pytest tests/api/test_repositorio_sillones.py` el alta, el listado ordenado por `id`, la búsqueda existente/inexistente, la baja lógica sin borrar la fila y el duplicado que lanza `NombreDuplicado`
- [x] 2.3 Implementar `app/db/repositorio_prestaciones.py` con las mismas cuatro operaciones y la misma traducción de `UNIQUE` a `NombreDuplicado`, incluyendo `duracion_minutos` y el campo `activa`; verificar con `pytest tests/api/test_repositorio_prestaciones.py` el alta con duración válida, la actualización de duración, la baja lógica, el `id` inexistente y el duplicado traducido

## 3. Endpoints HTTP y control de acceso por rol

- [x] 3.1 Implementar `app/api/sillones.py` con `GET /sillones` (`usuario_actual`), `POST /sillones` (`201`, `requiere_rol(Rol.ADMINISTRACION)`) y `PATCH /sillones/{id}` (`200`, `404` con `HTTPException`, `422`/`409` desde dominio y `UNIQUE`) montándolo en `app/main.py`; verificar con `pytest tests/api/test_sillones.py`: alta válida normalizada, duplicado `409`, nombre vacío `422`, nombre `null` `422` sin modificar el sillón, desactivación que sigue listándose, edición parcial, `id` inexistente `404` con `codigo` `no_encontrado`, recepción/odontología `403` y sin token `401`
- [x] 3.2 Implementar `app/api/prestaciones.py` con `GET /prestaciones` (`usuario_actual`), `POST /prestaciones` (`201`, solo administración) y `PATCH /prestaciones/{id}` (`200`/`404`/`422`/`409`) montándolo en `app/main.py`; verificar con `pytest tests/api/test_prestaciones.py`: alta válida, duración `0` y negativa `422` (RN-REC-01), nombre `null` y `duracion_minutos` `null` `422` sin modificar la prestación, nombre duplicado `409`, cambio de duración, `activa=false` que sigue listándose, `id` inexistente `404` con `codigo` `no_encontrado`, recepción/odontología `403` y sin token `401`

## 4. Verificación integral del change

- [ ] 4.1 Ejecutar `pytest tests` completo y verificar que pasan todos los tests del baseline y los nuevos de dominio, repositorio y API de `C-05`
- [ ] 4.2 Verificar que `app/domain/models.py` y `app/domain/errores.py` no importan `fastapi`, `sqlite3`, `app.db` ni `app.api`, y que `app/db/repositorio_sillones.py` y `app/db/repositorio_prestaciones.py` solo usan marcadores `?` (sin concatenar ni interpolar SQL)
- [ ] 4.3 Ejecutar `openspec validate c-05-sillones-prestaciones --strict` y verificar que no reporta errores

## Workflow follow-up

- Esperar la aprobación del propose antes de ejecutar `/opsx:apply c-05-sillones-prestaciones`.
- Archivar con `/opsx:archive c-05-sillones-prestaciones` cuando la suite completa esté en verde, y marcar `C-05` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
- Al hacer el propose de C-11 (crear-turno), incluir como requisito que no se aceptan turnos nuevos sobre un sillón con activo = false ni sobre una prestación con activa = false (RN-REC-03); C-05 solo los deja consultables.
