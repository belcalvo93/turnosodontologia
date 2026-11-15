# Bitácora de decisiones — Elías Tello

**Etapas a cargo:** etapa 2 (verificación de fuentes, Ajustar y PDF del informe) y etapa 5 (skills, registro y reglas del agente).

**Segunda etapa (implementación del MVP):** changes `C-07`, `C-15` y `C-17`, saneamiento de specs y, en `C-18`, las tareas 2.1, 2.2, 4.2, 4.3, la prueba de login y sesión de la 4.4, el verify y el archive.

---

## E-01 — Verificación de la fuente de precios de Turnito

- **Fecha:** 2026-10-09.
- **Qué verifiqué:** la fuente 2 del informe, la página de precios de Turnito.
- **Qué encontré:** los precios, los cupos de WhatsApp y las comisiones coincidían. Pero la URL citada era la raíz del sitio, que no tiene precios: estaban en `turnito.app/ar/planes/`. Además, el informe decía "IVA incluido", mientras que la página publica el precio sin IVA y el total con IVA.
- **Decisión:** dar la fuente por "Sí", corregir la URL y aclarar lo del IVA.
- **Evidencia:** `docs/discovery/verificacion-elias.md`, commits `dc909d3` y `954be20`.

## E-02 — Integrar la verificación de Belén (Dentalink)

- **Fecha:** 2026-10-09.
- **Decisión:** pasar la "duración variable" de Dentalink de "Comprobado" a "Comprobado en parte", porque solo se edita por cita y no por prestación.
- **Por qué:** el informe sobreestimaba la evidencia, y el MVP necesita duración por prestación.
- **Evidencia:** commit `b2327b2`.

## E-03 — Ajustar del informe con las 5 verificaciones

- **Fecha:** 2026-10-09.
- **Hallazgo principal (de Bruno):** el agente afirmó que AgendaPro no publicaba precios ni mencionaba el odontograma, y las dos cosas eran falsas. Había probado una URL inventada (`/ar/precios`, que dio 404) y no leyó las preguntas frecuentes colapsadas.
- **Decisiones:**
  - Corregir 7 celdas de AgendaPro.
  - Subir su puntaje de "Precio" de 2 a **4**, no a 5, por prudencia: tiene costos adicionales. Su total pasó de 3,35 a 3,45.
  - Corregir el resumen ejecutivo y C.3, porque ya no era cierto que "solo Turnito publica precios en pesos".
  - Agregar los hallazgos 7 y 8 sobre errores del agente.
- **Si hubiéramos dado "Continuar":** el informe habría quedado con una afirmación falsa en el resumen y en el análisis de vacíos del mercado.
- **Evidencia:** commit `dd3af88`.

## E-04 — PDF del informe

- **Fecha:** 2026-10-09.
- **Decisión:** generar el PDF desde el Markdown con portada propia, en formato horizontal por las tablas anchas.
- **Evidencia:** `docs/discovery/informe-discovery.pdf`.

## E-05 — Elección de skills (`find-skill`)

- **Fecha:** 2026-10-14.
- **Decisión:** instalar solo las 5 del Nivel 1 de las 16 recomendadas, y descartar `mattpocock/skills@tdd` por estar orientada a TypeScript.
- **Criterio:**
  - que encajen con el stack (Python, FastAPI, pytest, SQLite);
  - que el MVP es solo backend;
  - que aporten al Strict TDD;
  - preferir fuentes oficiales o muy usadas;
  - evitar skills que se superpongan.
- **Evidencia:** `docs/etapa-5-skills.md`, commit `95e9509`.

## E-06 — Ajustar del registro de skills

- **Fecha:** 2026-10-14.
- **Problema:** el registro generado tenía las mismas 3 reglas genéricas para las 11 skills, rutas absolutas de mi máquina y skills de fundación mezcladas.
- **Decisión:** reescribir las reglas compactas con contenido real de cada skill y ajustado a la KB. También pasé las rutas a relativas y quité las skills de fundación.
- **Si hubiéramos dado "Continuar":** los sub-agentes habrían recibido reglas vacías, y las rutas no funcionarían en otra computadora.
- **Evidencia:** `.atl/skill-registry.md`, commit `95e9509`.

## E-07 — Ajustar de `AGENTS.md` y `CLAUDE.md`

- **Fecha:** 2026-10-15.
- **Problemas:**
  - La regla 14 prohibía tocar `openspec/`, lo que habría bloqueado todo el ciclo OPSX de la etapa 6.
  - La regla 13 era una instrucción de sesión, no una regla de proyecto.
  - Una nota decía que el registro "no se versiona", y era falsa.
  - Al flujo le faltaban explore y verify.
- **Decisión:** corregir las 4 cosas antes de commitear. Agregué la regla propia del dominio: solo datos ficticios de pacientes (regla 10).
- **Evidencia:** commit `05131b6`, PR #6.

## E-08 — Skills incluidas en el repositorio

- **Fecha:** 2026-10-15.
- **Motivo:** el profesor pidió que, al clonar el repo, las skills vinieran incluidas.
- **Decisión:** instalar las 5 skills a nivel proyecto, como copia, en `.agents/skills/` (OpenCode) y en `.claude/skills/` (Claude Code), más `skills-lock.json` para restaurarlas. Verifiqué que las licencias sean MIT.
- **Evidencia:** commit `d0e8fc4`, PR #7.

## E-09 — Evidencia de la etapa 0

- **Fecha:** 2026-10-15.
- **Decisión:** reinstalar Active Stack en modo Full para capturar las 7 pantallas, con permisos "balanceado".
- **Evidencia:** `docs/evidencia/etapa-0-elias/`, PR #16.

## E-10 — `C-07` gestión de usuarios

- **Fecha:** 2026-10-29.
- **Decisiones:**
  - Armar la respuesta de usuario campo por campo, sin serializar nunca el hash de la contraseña. Los tests de la API comprueban que `password_hash` y `password` no aparecen en ninguna respuesta.
  - Agregar el error `username_duplicado` con código `409` al mapeo global, en vez de devolver un error suelto en el router (regla 7).
  - No tocar el esquema: la tabla `usuario` de `C-03` ya tenía todo lo necesario.
- **Si no lo hubiéramos hecho así:** un `GET /usuarios` podía terminar exponiendo los hashes, y el username repetido habría salido como un error 500 sin mensaje en español.
- **Evidencia:** `openspec/changes/archive/2026-10-29-c-07-gestion-usuarios/`, PR #36.

## E-11 — `C-15` consulta de auditoría

- **Fecha:** 2026-10-30.
- **Decisiones:**
  - Esperar a que estuvieran mergeados `C-11`, `C-12` y `C-13` antes de empezar, porque son los que escriben en `auditoria_turno`. Así evité conflictos con los cambios de Joaquín, Bruno y Hernán.
  - Devolver `{turno_id, registros}` en lugar de una lista suelta. Lo consulté con el equipo y lo confirmamos.
  - Ordenar por fecha y desempatar por `id`, para que dos registros del mismo instante salgan siempre en el mismo orden.
  - Hacer solo lecturas, sin transacciones ni escrituras, porque la auditoría es solo de agregar (regla 6).
- **Evidencia:** `openspec/changes/archive/2026-10-30-c-15-consulta-auditoria/`, PR #47.

## E-12 — Cambio de OpenCode a Antigravity

- **Fecha:** 2026-10-30.
- **Motivo:** en medio de `C-17` se terminó el límite gratuito de OpenCode.
- **Decisión:** seguir desde el Ajustar de `C-17` con Antigravity, que ya tenía instalado Active Stack con las mismas skills y comandos `/opsx:*`. Antes de seguir, confirmé que estuviera abierto en la carpeta del repositorio.
- **Por qué:** no perder el ciclo OPSX a mitad de camino ni rehacer el explore y el propose.

## E-13 — `C-17` seed demo y flujo de punta a punta

- **Fecha:** 2026-10-30.
- **Decisiones:**
  - Conservar `sembrar_admin_demo` tal cual y crear `sembrar_demo`, que la reutiliza. Reescribirla rompía sus 6 tests.
  - Hacer el seed idempotente en SQL (`ON CONFLICT DO NOTHING` y `WHERE NOT EXISTS`), sin agregar `UNIQUE` al esquema, que estaba fuera del alcance del change.
  - Que el test de punta a punta levante la app de verdad, con el seed en el arranque, y no llame al seed a mano. Si no, no probaba lo que el change promete.
  - Armar la tabla de trazabilidad RN → test con un verificador que corre dentro de la suite: cada una de las 31 RN tiene que tener al menos un test (regla 11).
- **Evidencia:** `docs/trazabilidad-rn-test.md`, `openspec/changes/archive/2026-10-30-c-17-seed-y-flujo-e2e/`, PR #52.

## E-14 — Saneamiento de specs

- **Fecha:** 2026-10-30.
- **Problema:** los specs `agenda` y `horarios-atencion` no pasaban `openspec validate --strict`. Además, `AccionAuditoria` estaba definido dos veces: en el dominio y en el repositorio.
- **Decisión:** reescribir `agenda` con el formato de OpenSpec sin cambiar su contenido, acortar el primer requirement de `horarios-atencion` y dejar `AccionAuditoria` solo en el dominio.
- **Resultado:** 17 de 17 specs válidos.
- **Evidencia:** PR #53.

## E-15 — Configuración de Stitch (MCP)

- **Fecha:** 2026-10-31.
- **Decisiones:**
  - Usar el proyecto de Google Cloud `proyecto-tp-utn-oe` y autenticar con un token OAuth, no con la API key.
  - Guardar la configuración en la carpeta de Antigravity, fuera del repositorio, para que el token no se suba nunca.
- **Problemas que encontré:** la primera vez quedó el texto de ejemplo en lugar del token, y después faltaba el prefijo `Bearer` en el encabezado `Authorization`. Con eso corregido, `list_projects` respondió `{}`, sin error.
- **Gotcha:** el token dura una hora. Si Stitch responde "Unauthorized", hay que generar uno nuevo.

## E-16 — `C-18` montaje del frontend en FastAPI (tareas 2.1 y 2.2)

- **Fecha:** 2026-11-05.
- **Decisiones:**
  - Montar los archivos estáticos en `/static` y servir `index.html` con una ruta `GET /` aparte, oculta del OpenAPI.
  - Escribir primero los 4 tests (rojo) y después el código (verde), incluido un test que comprueba que una ruta inexistente sigue devolviendo el 404 en JSON y en español.
  - Commitear solo `app.js`, como pedía el plan. El resto de los compilados era para la 3.6.
- **Si hubiéramos montado en `/`:** los archivos estáticos habrían tapado el 404 en JSON de la API (RN-GLO-01).
- **Evidencia:** `tests/api/test_frontend_estatico.py`, PR #56.

## E-17 — `C-18` verificación y prueba de login y sesión (tareas 4.2, 4.3 y 4.4)

- **Fecha:** 2026-11-11.
- **Decisiones:**
  - En la 4.2, descartar los `.js` que `npm test` recompila, porque solo cambian los finales de línea de Windows. Comprobé que el código compilado era idéntico al de la 3.6.
  - En la 4.3, revisar las reglas duras con búsquedas en el código y anotar cada comando y su resultado.
  - Tomar el caso "Login y sesión" de la 4.4, que no tenía responsable, y no hacer los roles asignados a mis compañeros.
  - Probar la sesión vencida con un token de formato válido y firma adulterada, y levantar la app con una base aparte (`demo-login.db`), sin usar contraseñas reales.
  - Revisar el PR de Bruno (3.2 y 3.3) con 2 sugerencias: un `catch` vacío que escondía errores y una fecha fija en la agenda. La primera quedó resuelta en el PR #63. Después revisé y mergeé las pruebas de administración (#70) y odontólogo (#69).
- **Evidencia:** `docs/evidencia/c-18-verificacion-elias/`, `docs/evidencia/c-18-login-sesion-elias/`, PRs #66 y #67.

## E-18 — `C-18` verify y archive

- **Fecha:** 2026-11-12.
- **Decisiones:**
  - Esperar a tener las 4 partes de la 4.4 en `main` antes de cerrar el change.
  - En `verify.md`, vincular cada uno de los 17 escenarios a un test automático o a la fila de la evidencia manual que lo cubre.
  - Cuando el PR #66 entró en conflicto con la 4.1 de Hernán en `tasks.md`, resolverlo con un merge de `main`, sin rebase, dejando marcadas las tres tareas.
- **Resultado:** `C-18` archivado, spec nuevo `frontend-minimo` y 18 de 18 specs válidos.
- **Evidencia:** `openspec/changes/archive/2026-11-11-c-18-frontend-minimo/verify.md`, PR #72.

## E-19 — Revisión de `C-19` y de la documentación de cierre

- **Fecha:** 2026-11-15.
- **Contexto:** `C-19` corrige specs y tests de mi `C-17`, a partir de la revisión de escenarios con `revisor-escenarios-sdd`. Además quedaban abiertos los PRs de la auditoría de documentación, las evidencias del frontend de Bruno y la bitácora de Joaquín.
- **Decisiones:**
  - Revisar `C-19` yo, porque toca mi change. Confirmé que el spec ahora coincide con el seed (los dos profesionales con matrícula ficticia), que los tests nuevos cubren los escenarios agregados y que la suite da 795 en verde y 18 de 18 specs válidos.
  - Mergear `C-19` antes que la auditoría, porque el PR de la auditoría incluía su commit. Así el diff de la auditoría quedó en 9 archivos.
  - En la auditoría, comparar con el código lo que el README dice sobre `JWT_SECRET` y el error 500 antes de aprobar.
  - En la prueba del README de Joaquín, comprobar que los logs solo mostraran los valores de ejemplo y no secretos reales.
- **Evidencia:** PRs #78, #79, #76 y #77.

---

## Uso del agente

- **Herramientas:** usé Claude Code y OpenCode para ejecutar las skills, generar borradores y revisar el repositorio. Desde el Ajustar de `C-17` usé Antigravity para los ciclos OPSX (E-12).
- **Revisión propia:** todas las decisiones de arriba las revisé y aprobé yo. Los Ajustar E-03, E-06 y E-07 salieron de revisar lo que generó el agente.
- **Segunda etapa:** el agente ejecutó los ciclos OPSX con Strict TDD y armó borradores de evidencias y PRs. Yo revisé cada resultado antes de commitear: comparé los números de tests con mis propias corridas, controlé que no se tocaran archivos protegidos ni el trabajo de mis compañeros y decidí qué tareas tomar, en qué orden mergear y cómo resolver los conflictos.
