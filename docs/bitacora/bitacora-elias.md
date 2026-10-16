# Bitácora de decisiones — Elías Tello

**Etapas a cargo:** etapa 2 (verificación de fuentes, Ajustar y PDF del informe) y etapa 5 (skills, registro y reglas del agente).

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

---

## Uso del agente

- **Herramientas:** usé Claude Code y OpenCode para ejecutar las skills, generar borradores y revisar el repositorio.
- **Revisión propia:** todas las decisiones de arriba las revisé y aprobé yo. Los Ajustar E-03, E-06 y E-07 salieron de revisar lo que generó el agente.
