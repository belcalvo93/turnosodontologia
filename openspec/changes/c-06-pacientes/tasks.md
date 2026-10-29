# Tasks — C-06 pacientes

> TDD estricto: primero el test que falla, después el código mínimo, después el verde. **Un test por regla, sin agrupar.** No se avanza de tarea sin confirmación explícita.

## 1. Dominio puro y contrato de error 409

- [x] 1.1 Escribir primero `tests/domain/test_pacientes.py` con un test por regla (normalización de `nombre` con `strip()`, normalización de `apellido` con `strip()`, normalización de `dni` con `strip()`, `nombre` vacío → `DatoInvalido`, `apellido` vacío → `DatoInvalido`, `dni` vacío → `DatoInvalido`, `telefono` con `strip()`, `obra_social` con `strip()`, `nro_afiliado` con `strip()`, opcionales en `""` → `None`, opcionales omitidos → `None`, `Paciente` con `id` opcional) y luego implementar `Paciente` y `validar_datos_paciente()` en `app/domain/models.py`; verificar con `pytest tests/domain/test_pacientes.py -v`
- [x] 1.2 Agregar `DniDuplicado` en `app/domain/errores.py` y su entrada `(409, "dni_duplicado")` en `MAPEO_DOMINIO` de `app/api/errores.py`; verificar sumando la ruta de prueba y el caso parametrizado en `tests/api/test_errores.py` que comprueban `409` con `{"codigo": "dni_duplicado", "mensaje": <español sin el DNI>}` mediante `pytest tests/api/test_errores.py -v`

## 2. Esquema SQLite y repositorio

- [x] 2.1 Agregar `CREATE TABLE IF NOT EXISTS paciente` al final de `app/db/esquema.sql` (`nombre`, `apellido` y `dni` `NOT NULL` con `CHECK (length(trim(...)) > 0)`, `dni UNIQUE`, `telefono`/`obra_social`/`nro_afiliado` `NULL`); escribir en `tests/api/test_repositorio_pacientes.py` un test por regla (esquema idempotente, `nombre` vacío, `nombre` solo espacios, `apellido` vacío, `apellido` solo espacios, `dni` vacío, `dni` solo espacios, `dni` duplicado, `dni` `NULL` rechazado, opcionales `NULL` aceptados) y verificar con `pytest tests/api/test_repositorio_pacientes.py -v`
- [x] 2.2 Implementar `app/db/repositorio_pacientes.py` (`crear_paciente`, `listar_pacientes`, `obtener_paciente_por_id`, `actualizar_paciente` con centinela `_SIN_CAMBIO`, SQL parametrizado y traducción de `IntegrityError` con `UNIQUE` a `DniDuplicado`) con un test por regla en `tests/api/test_repositorio_pacientes.py`: crear y obtener por id, obtener id inexistente → `None`, listar ordenado por `id`, actualizar `nombre`/`apellido`, actualizar `dni`, actualizar `telefono`/`obra_social`/`nro_afiliado`, limpiar un opcional con `None`, actualizar id inexistente → `None`, crear con DNI duplicado → `DniDuplicado`, actualizar a DNI existente → `DniDuplicado`, `IntegrityError` no-`UNIQUE` (por ejemplo `nombre` en blanco) no se traduce, y la fila conserva los valores previos tras un duplicado; verificar con `pytest tests/api/test_repositorio_pacientes.py -v`

## 3. Endpoints HTTP y control de acceso por rol

- [ ] 3.1 Implementar `app/api/pacientes.py` con `GET /pacientes` (`200`, `requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION)`) y `POST /pacientes` (`201`, `requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION)`), montándolo en `app/main.py`; escribir en `tests/api/test_pacientes.py` un test por regla, sin agrupar: alta válida con obra social, alta válida sin opcionales, normalización de DNI con espacios, `nombre` vacío `422`, `nombre` solo espacios `422`, `apellido` vacío `422`, `apellido` solo espacios `422`, `dni` vacío `422`, `dni` solo espacios `422`, DNI duplicado `409` sin repetir el DNI, `nro_afiliado` sin `obra_social` `201`, listado ordenado por `id`, listado de recepción `200`, listado de odontólogo `403`, recepción POST `201`, odontólogo POST `403`, sin token en GET `401` y sin token en POST `401`; verificar con `pytest tests/api/test_pacientes.py -v`
- [ ] 3.2 Implementar `PATCH /pacientes/{id}` en `app/api/pacientes.py` (`200`, `404` con `HTTPException`, `422`/`409` desde dominio y `UNIQUE`, `requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION)`); escribir en `tests/api/test_pacientes.py` un test por regla, sin agrupar: PATCH de nombre/apellido/DNI, PATCH de opcionales, limpieza de `telefono` con `null` `200`, limpieza de `obra_social` con `null` `200`, limpieza de `nro_afiliado` con `null` `200`, `nombre` `null` `422` sin modificar, `apellido` `null` `422` sin modificar, `dni` `null` `422` sin modificar, `nombre` solo espacios `422` sin modificar, `apellido` solo espacios `422` sin modificar, `dni` solo espacios `422` sin modificar, PATCH con el mismo DNI del paciente `200` sin conflicto, PATCH a DNI ajeno `409` conservando el anterior, PATCH id inexistente `404` con `codigo` `no_encontrado` y mensaje en español, recepción PATCH `200`, odontólogo PATCH `403` y sin token en PATCH `401`; verificar con `pytest tests/api/test_pacientes.py -v`

## 4. Verificación integral del change

- [ ] 4.1 Ejecutar `pytest tests -q` completo y verificar que pasan todos los tests del baseline y los nuevos de dominio, repositorio y API de `C-06`
- [ ] 4.2 Verificar que `app/domain/models.py` y `app/domain/errores.py` no importan `fastapi`, `sqlite3`, `app.db` ni `app.api`, y que `app/db/repositorio_pacientes.py` solo usa marcadores `?` (sin concatenar ni interpolar SQL)
- [ ] 4.3 Ejecutar `openspec validate c-06-pacientes --strict` y verificar que no reporta errores

## Workflow follow-up

- Esperar la aprobación del propose antes de ejecutar `/opsx:apply c-06-pacientes`.
- Archivar con `/opsx:archive c-06-pacientes` cuando la suite completa esté en verde, y marcar `C-06` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
- Al hacer el propose de `C-11` (crear-turno), incluir como requisito habilitar la lectura de `GET /pacientes` para el rol `odontologo` acotada a los pacientes de sus propios turnos, y agregar el test correspondiente que hoy queda pendiente por el `403` de `C-06`.
