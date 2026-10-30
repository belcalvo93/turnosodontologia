# Skill Registry

**Uso exclusivo del delegador.** Todo agente que lance sub-agentes lee este registro para resolver las reglas compactas y las inyecta directamente en el prompt del sub-agente. Los sub-agentes NO leen este registro ni los `SKILL.md`.

Las skills vienen versionadas en el repositorio (`.agents/skills/` para OpenCode y `.claude/skills/` para Claude Code); `skills-lock.json` registra su origen y versión. Las skills de la fundación (`active-orchestrator`, `find-skill`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-creator`) no se listan: no se usan al programar los changes.

## User Skills

| Skill | Cuándo usarla | Ruta |
|-------|---------------|------|
| fastapi | Escribir routers, dependencias y modelos Pydantic de la API (C-03 en adelante) | `.agents/skills/fastapi/SKILL.md` |
| fastapi-templates | Armar la estructura inicial del proyecto y `conftest.py` (C-01 `foundation-setup`) | `.agents/skills/fastapi-templates/SKILL.md` |
| python-testing-patterns | Escribir tests con pytest: unitarios del dominio, de API y e2e (todos los changes, Strict TDD) | `.agents/skills/python-testing-patterns/SKILL.md` |
| auth-implementation-patterns | Login, token y roles (C-03 `auth-login-roles`, dominio CRÍTICO) | `.agents/skills/auth-implementation-patterns/SKILL.md` |
| api-design-principles | Definir rutas, códigos de estado y formato de errores de la API | `.agents/skills/api-design-principles/SKILL.md` |
| revisor-escenarios-sdd | Revisar specs y tasks.md de un change al terminar un /opsx:propose, antes de /opsx:apply; cruza escenarios con la KB y el contrato de errores-api | `.agents/skills/revisor-escenarios-sdd/SKILL.md` |

## Compact Rules

### fastapi
- Declarar parámetros y dependencias con `Annotated` (`Annotated[int, Path()]`, `Annotated[Session, Depends(...)]`), no con valores por defecto.
- No usar `...` (Ellipsis) en operaciones de ruta ni en modelos Pydantic: un campo obligatorio simplemente no lleva valor por defecto.
- Tipar el retorno de cada operación de ruta o usar `response_model`: la salida se valida y se documenta sola.
- Una operación HTTP por función; los routers se montan con `include_router` y llevan su propio prefijo.
- Usar `def` para operaciones bloqueantes (SQLite síncrono) y `async def` solo si no se bloquea el hilo.
- No usar `RootModel` de Pydantic.
- Las dependencias (`Depends`) inyectan la sesión de base de datos y el usuario autenticado; no se importan como globales.

### fastapi-templates
- Estructura propuesta en `knowledge-base/08_arquitectura_propuesta.md`: `app/domain/` (Python puro), `app/api/` (routers), `app/db/` (persistencia SQLite) y `tests/` espejo. La estructura de la KB prevalece sobre la de la skill.
- El dominio no importa FastAPI ni SQLite (D-02).
- Los tests de API usan `TestClient` y una base SQLite temporal o en memoria, creada en una fixture de `tests/conftest.py`.
- Manejo de errores centralizado: las excepciones de dominio se traducen a códigos HTTP en la capa `api`, no dentro del dominio.

### python-testing-patterns
- Strict TDD: primero el test que falla (RED), luego el mínimo código para pasarlo (GREEN), luego refactor; mínimo 2 casos por comportamiento (camino feliz y borde o error).
- Cada escenario del spec y cada regla `RN-xx` tiene al menos un test que la verifica.
- Estructura AAA (Arrange, Act, Assert) y nombres `test_<unidad>_<escenario>_<resultado esperado>`.
- Tests unitarios del dominio sin base de datos ni HTTP; tests de integración con SQLite temporal; e2e solo en C-17.
- Aislamiento: cada test crea sus propios datos con fixtures; ningún test depende del orden de otro.
- Sin aserciones triviales (tautologías, solo de tipo): deben ejercitar comportamiento.
- Todo dato de prueba es ficticio (RN-PAC-03).

### auth-implementation-patterns
- Nunca guardar contraseñas en texto plano: hash con bcrypt o argon2.
- Tokens de acceso de vida corta (15 a 30 minutos) y con expiración; el secreto no va en el repositorio (variable de entorno o archivo de ejemplo con valores ficticios).
- Autenticación y autorización siempre del lado del servidor: 401 si no hay token válido, 403 si el rol no alcanza.
- Validar todas las entradas del login; no revelar si falló el usuario o la contraseña.
- Registrar los intentos de acceso fallidos (auditoría).
- Mecanismo definitivo pendiente (D-03, JWT candidato): no decidirlo dentro de un change; resolverlo en `propose`.

### api-design-principles
- Sustantivos en plural para colecciones (`/turnos`, `/pacientes`); la acción va en el método HTTP.
- Códigos de estado según la KB: 401 sin autenticar, 403 sin permiso, 409 conflicto (solapamiento, DNI duplicado, cancelar dos veces), 422 datos inválidos, 404 recurso inexistente.
- Formato de error único y estable para todos los endpoints.
- Paginación en las colecciones grandes (por ejemplo, la agenda).
- La estructura de la API no copia el esquema de la base de datos.
- OpenAPI/Swagger de FastAPI como documentación; mantenerlo coherente con los specs.

### revisor-escenarios-sdd
- Solo lectura: informa hallazgos con archivo y línea; no modifica archivos ni resuelve por su cuenta, el humano decide qué corregir.
- Contar los escenarios reales contando las líneas `#### Scenario:`; no confiar en el número total que declare un documento.
- Cruzar cada escenario con su RN-xx en `knowledge-base/05_reglas_de_negocio.md`: que el número exista y que la regla diga lo que el escenario afirma.
- No imponer códigos HTTP de memoria: cotejar con `openspec/specs/errores-api/spec.md` (404 si el id va en la ruta, 422 si el dato viene en el cuerpo, 409 dominio/unicidad, 401 sin token, 403 con token sin permiso).
- Bordes a revisar: intervalos semiabiertos `[inicio, fin)`, recurso inexistente, rol sin permiso, listas vacías, estados del turno y datos ficticios (RN-PAC-03).
- Cada RN-xx del change mapea a al menos una tarea de test en `tasks.md` (regla dura 11) y consta la tarea de verificación final con pytest.
- Mínimo 3 escenarios por historia del change: camino esperado, error de negocio y borde.

## Project Conventions

| Elemento | Dónde | Nota |
|----------|-------|------|
| Stack | `knowledge-base/09_decisiones_y_supuestos.md` (D-01) | Python + FastAPI + pytest + SQLite (provisional); persistencia sin ORM (D-07) |
| Arquitectura | `knowledge-base/08_arquitectura_propuesta.md` | Dominio separado del framework y de la base de datos (D-02) |
| Reglas de negocio | `knowledge-base/05_reglas_de_negocio.md` | Cada regla `RN-xx` tiene una verificación por API que sirve de test |
| Modelo de datos | `knowledge-base/04_modelo_de_datos.md` | Fechas en hora local del consultorio e intervalos semiabiertos (D-06) |
| Roadmap | `CHANGES.md` | 17 changes en 6 fases; solo el MVP (D-04) |
| Visión, actores, funcionalidades, flujos, preguntas abiertas | `knowledge-base/01`, `02`, `03`, `06`, `07`, `10` | Leer antes de proponer un change |
| Discovery | `docs/discovery/informe-discovery.md` | Origen del MVP y de los vacíos del mercado |
| Datos de pacientes | RN-PAC-03 y D-08 | Solo datos ficticios en código, seeds, ejemplos, tests y capturas |
| Idioma | Todo el proyecto | Documentación, specs y comunicación en español |
| Tests | `tests/` | Strict TDD; un test por escenario del spec |
