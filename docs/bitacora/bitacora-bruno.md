# Bitácora de decisiones — Bruno Fiouchetta

**Etapas a cargo:** etapa 1 (fundación), etapa 2 (Discovery), convención de Engram, changes C-04 (`profesionales`), C-09 (`bloqueos`), C-12 (`cancelar-turno`), tareas 3.2, 3.3 y 4.4 de C-18 (`frontend-minimo`), auditoría de archivados y entrega.

---

## B-01 — `openspec init`

- **Fecha:** 2026-10-08.
- **Qué hice:** corrí `/active-orchestrator:init` en el repo vacío. Hizo `openspec init` solo para Claude Code.
- **Decisión:** borrar las skills `openspec-*` que el init copió dentro del proyecto, porque ya estaban instaladas globalmente con Active Stack. Los comandos `/opsx` quedaron en `.claude/commands/opsx/`.

## B-02 — Bifurcación del Discovery: Sí

- **Fecha:** 2026-10-08.
- **Decisión:** responder **Sí**, porque la consigna lo exige.

## B-03 — Parar acá después de la etapa 1

- **Fecha:** 2026-10-08.
- **Decisión:** parar después de la bifurcación para commitear la etapa 1 sola antes de arrancar el Discovery (una rama y un PR por etapa). El estado quedó en `step: "discovery"`.
- **Evidencia:** PR #1.

## B-04 — Primera búsqueda sin el enunciado

- **Fecha:** 2026-10-08.
- **Qué pasó:** antes de pasarle el PDF del TP al agente, le pedí que buscara competidores y analizó solo 3: AgendaPro, Dentalink y Wati.
- **Decisión:** cuando le pasé el enunciado cambió el alcance. La carpeta pasó a ser `docs/discovery/` y la consigna de investigación se hizo tal cual, con 15 sistemas o más y las secciones A a D. Las 3 notas quedaron en `docs/discovery/sources/`.

## B-05 — Informe, primera versión → Ajustar

- **Fecha:** 2026-10-08.
- **Qué estaba mal:** el agente relevó 18 sistemas, pero al revisarlo contra la consigna encontré tres problemas:
  - usaba la abreviatura "NE" en vez de escribir "No evidenciado", que es lo que pide la consigna;
  - juntaba en una sola celda cosas que la consigna pide por separado (sobreturnos, exportación, soporte, etc.);
  - el conteo de países del resumen estaba mal.
- **Decisión:** **Ajustar**. Se abrió una subtabla por cada eje de la consigna (A.2 a A.11) y se buscó evidencia nueva en centros de ayuda y tutoriales oficiales.
- **Si hubiera dado Continuar:** habríamos entregado una tabla que no cumple el formato pedido.
- **Evidencia:** la consigna literal quedó en `docs/discovery/consigna-investigacion.md` para que sea trazable.

## B-06 — Checklist de 11 puntos (discovery-research)

- **Fecha:** 2026-10-08.
- **Decisiones que después usó el change:**
  - sin solapamiento por profesional, por sillón **y por paciente**;
  - intervalos semiabiertos: un turno que empieza justo cuando termina otro es válido;
  - se rechaza un turno fuera del horario de atención o dentro de un bloqueo;
  - sin sobreturnos;
  - se cancela o reprograma solo un turno futuro, sin anticipación mínima en el MVP;
  - ninguna integración externa en el MVP.
- **Supuesto:** la escala (una sede, varios odontólogos y sillones) quedó como supuesto, porque no la confirmé.
- **Evidencia:** `docs/discovery/discovery.md`.

## B-07 — Parar acá hasta verificar fuentes

- **Fecha:** 2026-10-08.
- **Decisión:** no di Continuar, porque la consigna pide verificar al menos 5 fuentes antes de usar el informe. Repartimos una fuente por integrante, de tipos distintos.

## B-08 — Un archivo de verificación por integrante

- **Fecha:** 2026-10-09.
- **Qué pasó:** al principio cada uno iba a escribir en la tabla del informe. Como las filas son líneas largas, iba a haber conflictos de merge.
- **Decisión:** adoptar el formato de Belén (`verificacion-belen.md`), un archivo por integrante. Belén mergeó su PR antes de que cerrara la etapa, así que traje `main` a mi rama para no perder nada.

## B-09 — Mi verificación de AgendaPro: 2 errores del agente

- **Fecha:** 2026-10-09.
- **Qué hice:** revisé la landing dental de AgendaPro con ayuda del agente en el navegador. Desplegamos las preguntas frecuentes y seguimos el enlace "Precios" del menú.
- **Qué encontré:** de 5 afirmaciones, 3 estaban bien y 2 mal:
  - **Decía que AgendaPro no publica precios, y sí los publica** en `/ar/planes` (Individual $13.900, Básico $33.900, etc.). El agente había probado una URL inventada (`/ar/precios`, que da 404) en vez de seguir el enlace del menú.
  - **Decía que no menciona el odontograma, y sí lo menciona**, en una pregunta frecuente colapsada. El resumen automático de la página no leía ese contenido.
- **Decisión:** proponer 7 correcciones, que Elías aplicó con **Ajustar**.
- **Si hubiera dado Continuar:** en el resumen y en la matriz habría quedado la afirmación falsa "solo Turnito publica precios en pesos".
- **Evidencia:** `docs/discovery/verificacion-bruno.md`, commit `0b6eb4c`.

## B-10 — Hallazgo: página con instrucciones para IA

- **Fecha:** 2026-10-08.
- **Qué pasó:** la página de Clinicorp tenía un bloque de texto dirigido a asistentes de IA, y el agente no lo siguió.
- **Decisión:** dejarlo como hallazgo del informe: el contenido que lee un agente puede intentar manipularlo.

## B-11 — Continuar al cerrar la etapa 2

- **Fecha:** 2026-10-13.
- **Decisión:** con las 5 verificaciones y los ajustes aplicados, revisé el PR #3 y lo mergeé sin squash. Di **Continuar** en el orquestador (estado `kb`) con un commit aparte, en el PR #4, para que Belén arrancara la etapa 3.

## B-12 — Revisión y merge del change de Joaquín

- **Fecha:** 2026-10-15.
- **Qué hice:** antes de mergear el PR #12, cloné la rama en una carpeta aparte y seguí solo el README. Pasaron los 32 tests. Revisé que cada escenario del spec tuviera su test y que el código respetara las reglas duras (dominio sin FastAPI ni base de datos, sin `datetime.now()`, intervalos `[inicio, fin)`).
- **Decisión:** mergearlo con merge commit, sin squash, para que se vieran los commits de Joaquín por tarea.
- **Evidencia:** PR #12, commit `d7c23bb`.

## B-13 — Revisión final del repo

- **Fecha:** 2026-10-15.
- **Qué encontré:**
  - El estado del orquestador seguía en `step: "kb"`. Las etapas 3 a 5 se corrieron con las skills por separado y nadie lo fue avanzando.
  - `discovery.md` todavía repetía los dos errores de AgendaPro que habíamos corregido en el informe.
  - El `.gitignore` no ignoraba `.env` ni las bases SQLite.
- **Decisión:** completar el estado con lo que ya estaba hecho y pasarlo a `done`, corregir `discovery.md` (con una nota del cambio a SQLite, D-01) y agregar `.env` y `*.db` al `.gitignore`.
- **Evidencia:** PR #13, commits `bbd75b1`, `214b297` y `30329fb`.

## B-14 — Nombre del proyecto en Engram

- **Fecha:** 2026-10-15.
- **Qué pasó:** yo había propuesto `turnos-odontologia`, pero Engram toma el nombre del remote de git y detecta el proyecto como `turnosodontologia`.
- **Decisión:** usar `turnosodontologia`, porque a los cinco les da el mismo nombre sin configurar nada. Guardé 3 memorias: la verificación de AgendaPro, las reglas de negocio y la revisión final.

## B-15 — C-04 `profesionales`: validación en dominio puro y baja lógica (`RN-REC-03`)

- **Fecha:** 2026-10-28.
- **Qué hice:** ejecuté el ciclo completo de `C-04` (`explore`, `propose`, `apply` con TDD, `verify` y `archive`).
- **Decisión:** validar nombre y matrícula obligatorios en `validar_datos_profesional` dentro de `app/domain/`, mantener el alta y la edición (`PATCH`) restringidas a `administracion` (`403` para los demás roles) e implementar la desactivación mediante el campo `activo` en vez de borrado físico (`RN-REC-03`).
- **Qué otra opción había:** validar directamente en los esquemas de FastAPI o permitir borrado `DELETE` en SQLite.
- **Por qué:** las reglas duras exigen que la lógica viva en el dominio sin depender del framework y que ningún recurso referenciable por turnos históricos se elimine físicamente.
- **Evidencia:** PR #33, commits `3113761`, `693ceb0`, `6a95073` y `13fe888`, archivado en `openspec/changes/archive/2026-10-28-c-04-profesionales/`.

## B-16 — C-09 `bloqueos`: intervalo semiabierto `[inicio, fin)` y permisos de administración

- **Fecha:** 2026-10-28 a 2026-10-29.
- **Qué hice:** implementé `C-09` para registrar bloqueos horarios sobre profesionales o sillones.
- **Decisión:** validar en el dominio que el intervalo cumpla `inicio < fin` (`RN-REC-02`, rechazando con `422 DatoInvalido` si `inicio >= fin`) y que el motivo no sea vacío; indexar la tabla `bloqueo` por recurso y rango horario en SQLite; y restringir `POST /bloqueos` exclusivamente a `administracion` (`RN-ACC-02`).
- **Qué otra opción había:** permitir también a `recepcion` crear bloqueos o usar intervalos cerrados.
- **Por qué:** la matriz RBAC de la KB reserva los bloqueos a administración y toda la agenda del sistema opera con intervalos semiabiertos `[inicio, fin)`.
- **Evidencia:** PR #41, commits `1459d43`, `b9a0e29`, `c4e5d7c` y `64f3ced`, archivado en `openspec/changes/archive/2026-10-29-c-09-bloqueos/`.

## B-17 — C-12 `cancelar-turno`: ajustar el design para que el repositorio no llame al dominio y auditar en la misma transacción

- **Fecha:** 2026-10-30.
- **Qué pasó:** en la primera versión del `design.md` de `C-12`, la tarea 2.1 planteaba que `cancelar_turno` del repositorio invocara la validación del dominio.
- **Decisión:** ajustar `design.md` y `tasks.md` antes de implementar el repositorio para que la validación (`validar_cancelacion`, verificando estado `reservado` y horario futuro respecto a `ahora`, `RN-TUR-06` y `RN-TUR-09`) se ejecute antes desde la capa de aplicación/router, y que el repositorio SQLite solo actualice el estado a `cancelado` e inserte el registro en `auditoria_turno` dentro de la misma transacción (`RN-AUD-01`), liberando el hueco para nuevos turnos (`RN-TUR-08`).
- **Si hubiera dado Continuar:** habríamos acoplado `app/db/` con las reglas de negocio en lugar de mantener las responsabilidades separadas.
- **Evidencia:** commits `7dbb1e8`, `4184ab5`, `a4f686b`, `84516e3` y `a652a7e`, archivado en `openspec/changes/archive/2026-10-30-c-12-cancelar-turno/`.

## B-18 — TP Skills y MCP: autenticación OAuth con `gcloud` para Stitch en Antigravity

- **Fecha:** 2026-10-30.
- **Qué pasó:** al configurar el servidor MCP remoto de Stitch (`https://stitch.googleapis.com/mcp`) en Antigravity con una API key, listaba las herramientas pero fallaba con `401: API keys are not supported by this API` al ejecutar llamadas reales.
- **Decisión:** cambiar a autenticación OAuth usando `gcloud auth application-default login` y el encabezado `X-Goog-User-Project` en la configuración local fuera del repositorio (`~/.gemini/config/mcp_config.json`), comprobar la conexión con `list_projects` y generar la pantalla de bloqueo que sirvió de insumo para `C-18`.
- **Evidencia:** `docs/skills-mcp/aplicacion.md` (§3 y §5) y `docs/skills-mcp/evidencias/03-stitch-mcp-invocaciones.md`.

## B-19 — Auditoría de los 17 changes archivados: `.openspec.yaml` faltante en C-05

- **Fecha:** 2026-11-06.
- **Qué encontré:** al auditar los 17 changes archivados (`C-01` a `C-17`) contra `openspec validate --all --strict` y verificar la estructura de carpetas en `openspec/changes/archive/`, detecté que a `2026-10-28-c-05-sillones-prestaciones` le faltaba el archivo de metadatos `.openspec.yaml`.
- **Decisión:** abrir una rama específica y agregar el `.openspec.yaml` faltante para que los 17 archivos históricos tuvieran exactamente la misma estructura verificable.
- **Evidencia:** PR #58, commit `9fcff59`.

## B-20 — C-18 `frontend-minimo` (tareas 3.2 y 3.3): vistas de login y agenda con RBAC sin subir compilados

- **Fecha:** 2026-11-10.
- **Qué hice:** implementé `frontend/src/vistas/login.ts`, `frontend/src/vistas/agenda.ts` y el cableado de navegación en `frontend/src/app.ts`.
- **Decisión:** adaptar el menú y la carga de catálogos según el rol del token (`GET /pacientes` solo se invoca para `administracion` y `recepcion`; el `odontologo` ve `"Paciente #<id>"` sin nombre ni DNI para cumplir `RN-ACC-03`), mostrar el estado vacío cuando no hay eventos y no commitear los `.js` compilados en `app/static/` dentro de mi rama.
- **Por qué:** el diseño `D8` de `C-18` dejaba la compilación final en la tarea `3.6` para evitar conflictos de merge con las ramas paralelas de Hernán (`3.1`) y Joaquín (`3.4` y `3.5`).
- **Evidencia:** PR #61, commit `818d3d8`.

## B-21 — C-18 `frontend-minimo` (tarea 4.4 y fix de agenda): pruebas manuales de administración y limpieza del resumen tras error

- **Fecha:** 2026-11-11.
- **Qué hice:** levanté la API con el seed demo en local y probé desde el navegador los cinco escenarios del rol `administracion` (`admin_demo`): visibilidad de las tres vistas, alta de turno `201`, bloqueo con `turnos_afectados` superpuestos sin cancelar el turno, bloqueo sin turnos afectados y error `422` por intervalo inválido. Además, a partir de la observación de Joaquín en las pruebas de odontólogo, corregí `limpiarTablaAnteError` en `frontend/src/vistas/agenda.ts` y su compilado `app/static/vistas/agenda.js`.
- **Decisión:** limpiar también `#agenda-resumen-rango` cuando falla la consulta de agenda (por ejemplo, ante un `403`), para que no quede visible el nombre del profesional de la consulta previa.
- **Evidencia:** PR #70 (`4a81619`, `docs/evidencia/c-18-administracion-bruno/`) y PR #71 (`a09e5a0`).

---

## Uso del agente

- **Herramientas:** usé Claude Code y Antigravity para correr el orquestador y `discovery-research`, para buscar y leer las fuentes del informe, para la verificación en el navegador, para configurar el MCP de Stitch, para desarrollar con TDD los changes `C-04`, `C-09`, `C-12` y las tareas `3.2`, `3.3` y `4.4` de `C-18`, y para auditar el repositorio antes de la entrega.
- **Revisión propia:** las respuestas del checklist del Discovery, las decisiones de Continuar, Ajustar y Parar acá, el ajuste de arquitectura en `C-12` (para no llamar al dominio desde el repositorio) y las pruebas manuales en el navegador las tomé y verifiqué yo. Los Ajustar (B-05, B-09 y B-17) salieron de revisar lo que había generado el agente contra la consigna y las reglas duras de `AGENTS.md`.
- **Lo que me dejó:** tanto en el informe de Discovery (las dos afirmaciones falsas de AgendaPro) como en el `design.md` de `C-12` y en la autenticación de Stitch con API key, lo que proponía el agente parecía razonable en texto pero fallaba al contrastarlo con la página real, las reglas de arquitectura o el servidor en vivo. Desde ahí no di por buena ninguna salida sin probarla y verificarla yo mismo.
