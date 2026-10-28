# Tasks — C-04 profesionales

## 1. Dominio puro

- [x] 1.1 Agregar la dataclass `Profesional` (`id`, `nombre`, `apellido`, `matricula=None`, `activo=True`) y la función `validar_datos_profesional(nombre, apellido, matricula=None)` en `app/domain/models.py` (o módulo de dominio), verificando con tests unitarios en `tests/domain/test_profesionales.py` que datos válidos se normalizan con `strip()`, que `matricula` vacía o en blanco pasa a `None`, y que `nombre` o `apellido` vacíos o de solo espacios lanzan `DatoInvalido`

## 2. Esquema y persistencia SQLite

- [x] 2.1 Agregar `CREATE TABLE IF NOT EXISTS profesional` en `app/db/esquema.sql` con `id`, `nombre`, `apellido`, `matricula` opcional y `activo` con default `1` y `CHECK` de `nombre`/`apellido` no vacíos, verificando con tests que `inicializar_esquema()` crea la tabla de forma idempotente
- [x] 2.2 Implementar `app/db/repositorio_profesionales.py` con consultas SQL parametrizadas para `crear_profesional`, `listar_profesionales`, `obtener_profesional_por_id` y `actualizar_profesional`, verificando con tests sobre SQLite temporal el alta, el listado ordenado por `id`, la búsqueda por `id` existente/inexistente y la desactivación lógica (`activo=False`) sin borrar la fila

## 3. Endpoints HTTP y control de acceso por rol

- [x] 3.1 Implementar el router `app/api/profesionales.py` con `GET /profesionales`, `POST /profesionales` (`201`) y `PATCH /profesionales/{id}` (`200` / `404`) integrando las dependencias `usuario_actual` y `requiere_rol("administracion")` de `C-03` y montarlo en `app/main.py`, verificando con tests en `tests/api/test_profesionales.py`: alta válida con y sin matrícula (`201`), `nombre` o `apellido` vacío (`422`), edición y desactivación con `activo=false` (`200`), profesional desactivado que sigue listándose como inactivo en `GET /profesionales` (`200`) y `PATCH` de `id` inexistente (`404`)
- [x] 3.2 Verificar en `tests/api/test_profesionales.py` las reglas de acceso `RN-ACC-01` y `RN-ACC-02`: request sin token devuelve `401`, rol `recepcion` u `odontologo` intentando `POST /profesionales` o `PATCH /profesionales/{id}` devuelve `403`, y los tres roles autenticados pueden consultar `GET /profesionales` (`200`)

## 4. Verificación integral del change

- [x] 4.1 Ejecutar `pytest tests` completo y verificar que pasan todos los tests existentes y los nuevos de dominio y API de `C-04`
- [x] 4.2 Verificar que `app/domain/` no importa `fastapi` ni `app.db`/`app.api` y que todas las consultas de `app/db/repositorio_profesionales.py` usan parámetros `?`
- [x] 4.3 Ejecutar `openspec validate c-04-profesionales --strict` y verificar que no reporta errores

## Workflow follow-up

- Esperar a que `C-03` (`auth-login-roles`) esté mergeado en `main` antes de ejecutar `/opsx:apply c-04-profesionales`.
- Verificar el change con la suite completa en verde.
- Archivar con `/opsx:archive c-04-profesionales` y marcar `C-04` como `[x]` en `CHANGES.md` solo con autorización explícita del usuario (regla dura 14).
