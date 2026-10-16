# Bitácora de decisiones — Bruno Fiouchetta

**Etapas a cargo:** etapa 1 (fundación), etapa 2 (Discovery), convención de Engram, revisión final y entrega.

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

---

## Uso del agente

- **Herramientas:** usé Claude Code para correr el orquestador y `discovery-research`, para buscar y leer las fuentes del informe, para la verificación en el navegador, para Git y para revisar el PR #12 y el repo antes de entregar.
- **Revisión propia:** las respuestas del checklist del Discovery y las decisiones de Continuar, Ajustar y Parar acá las tomé yo. Los dos Ajustar (B-05 y B-09) salieron de revisar lo que había generado el agente.
- **Lo que me dejó:** las dos afirmaciones falsas de AgendaPro parecían razonables. Si no abría la página y seguía los enlaces, no me daba cuenta. Desde ahí no di por buena ninguna afirmación del informe que no estuviera en una URL que yo pudiera abrir.
