# Tasks — C-09 bloqueos

## 1. Dominio puro (`RN-REC-02`)

- [x] 1.1 Extender `Bloqueo` en `app/domain/models.py` con `id: int | None = None` y agregar `validar_datos_bloqueo(alcance, recurso_id, inicio, fin, motivo="")`, verificando con tests unitarios en `tests/domain/test_bloqueos.py` que un bloqueo con `inicio < fin` se construye válido, que `inicio == fin` o `inicio > fin` lanza `DatoInvalido` (`RN-REC-02`), que un `alcance` distinto de `"profesional"`/`"sillon"` lanza `DatoInvalido` y que los tests existentes de `tests/domain/test_reglas_turno.py` siguen pasando

## 2. Esquema y persistencia SQLite

- [x] 2.1 Agregar `CREATE TABLE IF NOT EXISTS bloqueo` y `CREATE INDEX IF NOT EXISTS idx_bloqueo_alcance_recurso_inicio ON bloqueo (alcance, recurso_id, inicio)` en `app/db/esquema.sql`, verificando con tests que `inicializar_esquema()` crea la tabla y el índice de forma idempotente
- [x] 2.2 Implementar `app/db/repositorio_bloqueos.py` con consultas SQL parametrizadas para verificar la existencia del recurso (`profesional` o `sillon` según `alcance`), insertar el bloqueo, listar bloqueos ordenados por `inicio` y eliminar por `id`, verificando con tests sobre SQLite temporal que un `recurso_id` inexistente lanza `DatoInvalido` y que `eliminar_bloqueo` borra el registro

## 3. Endpoints HTTP y control de acceso por rol

- [x] 3.1 Implementar el router `app/api/bloqueos.py` con `GET /bloqueos`, `POST /bloqueos` (`201`) y `DELETE /bloqueos/{id}` (`204`/`200` y `404` si no existe) integrando `usuario_actual` y `requiere_rol("administracion")` y montarlo en `app/main.py`, verificando con tests en `tests/api/test_bloqueos.py`: alta válida para profesional y para sillón (`201`), `inicio >= fin` (`422`), recurso inexistente (`422`), listado (`200`), eliminación de bloqueo existente y `DELETE` de `id` inexistente (`404`)
- [x] 3.2 Verificar en `tests/api/test_bloqueos.py` los permisos por rol (`RN-ACC-01`, `RN-ACC-02`): request sin token devuelve `401`, rol `recepcion` u `odontologo` intentando `POST /bloqueos` o `DELETE /bloqueos/{id}` devuelve `403`, y los tres roles autenticados pueden consultar `GET /bloqueos` (`200`)

## 4. Verificación integral del change

- [x] 4.1 Ejecutar `pytest tests` completo y verificar que toda la suite pasa en verde
- [x] 4.2 Verificar que `app/domain/` no importa `fastapi` ni `app.db`/`app.api` y que `app/db/repositorio_bloqueos.py` usa únicamente SQL parametrizado
- [x] 4.3 Ejecutar `openspec validate c-09-bloqueos --strict` y verificar que no reporta errores

## Workflow follow-up

- Esperar a que `C-02`, `C-04` y `C-05` estén mergeados en `main` antes de ejecutar `/opsx:apply c-09-bloqueos`.
- Verificar el change con la suite de tests en verde.
- Archivar con `/opsx:archive c-09-bloqueos` y marcar `C-09` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
