# Bitácora de decisiones — Hernán Gonzalez

**Proyecto:** Sistema de gestión de turnos odontológicos (Metodología I, UTN Mendoza).
**Repositorio:** https://github.com/belcalvo93/turnosodontologia
**Rama:** `hernan`, `hernan-evidencia`

## Decisiones

| # | Etapa | Qué decidí | Qué otra opción había | Por qué | Dónde quedó |
|---|---|---|---|---|---|
| 1 | 2 | Verificar Doctoralia en la App Store y darla por "Sí (con precisión)" con una corrección menor. | Darla por confirmada sin más, o descartarla. | Abrí la ficha pública sin cuenta: coincidían desarrollador, planes y valoraciones. Detecté yo comparando los textos que el proveedor real era "Docplanner Health (proveedor: Docplanner Italy S.R.L.)", no solo "Docplanner", porque solemos quedarnos solo con el nombre comercial. | `docs/discovery/verificacion-hernan.md` |
| 2 | 6 | Proponer C-10 (`reglas-alta-turno`) porque pertenece al MVP, es dominio puro y solo depende de C-01 y C-02. | Otro change con más dependencias. | Al ser dominio puro se desarrolla y prueba sin DB ni HTTP, aislado del resto. | `openspec/changes/archive/2026-10-15-c-10-reglas-alta-turno/proposal.md` |
| 3 | 6 | Plantear la solución como backend Python 3.11 + PyTest, sin interfaz gráfica. | Otro stack. | Es el stack fijado en `AGENTS.md` y la KB; otro lenguaje duplicaba el toolchain. | `design.md` del change archivado |
| 4 | 6 | Redactar la spec con tres escenarios Dado / Cuando / Entonces y solo datos ficticios. | Menos escenarios o datos reales. | Cada escenario es un caso de test directo y los datos ficticios son regla del proyecto. | `specs/reglas-alta-turno/spec.md` del change archivado |
| 5 | 6 | Aceptar los tres ajustes de Belén al propose (PR #9) en vez de defender mi versión. | Aprobarlo como estaba. | El que más me dolió fue el de los escenarios de bloqueo y horarios, y fue el más justo: yo que manejo recepción sé que si no controlás los horarios se arma un quilombo bárbaro; se me pasó por distracción al documentar. Además faltaba la base técnica y había una inconsistencia en la prestación del ejemplo. | PR #9 |
| 6 | 6 | Quitar `ahora` de `validar_alta` y la mención a Java/JUnit del design. | Dejarlos. | `ahora` no se usaba en ninguna validación del alta (el futuro es de C-12/C-13) y Java metía ruido en un proyecto Python ya decidido. | Commit `4ef76af`, PR #10 |
| 7 | 6 | Guardar el resumen del explore en el repo además de Engram. | Solo Engram. | Engram no se ve desde GitHub; en el repo queda visible para el equipo y la defensa. | `explore.md` en el change archivado, PR #19 |
| 8 | 6 | Aceptar mover `explore.md` al archive y trabajar en rama nueva. | Reusar `hernan`. | La carpeta activa fantasma hacía que `openspec list` mostrara un change en progreso ya archivado; `hernan` tenía los artefactos viejos. | PR #22, rama `hernan-evidencia` |
| 9 | 7 | Guardar el explore en Engram y verificar la consulta antes del video. | Confiar en que estaba guardado. | "Reglas alta turno" devuelve la memoria; "AgendaPro" no devuelve nada, así que en el video hay que demostrar la que funciona. Engram solo se detecta abriendo Claude Code desde la carpeta del repo. | Memoria #17 de Engram |

## Uso de IA

Usé OpenCode (modelo Muse Spark) para ejecutar el ciclo OPSX del propose, generar borradores y revisar el repositorio. Las decisiones de la tabla las tomé yo: elegí el change, verifiqué mi fuente manualmente en el navegador, acepté los ajustes de Belén, pedí las correcciones del design y decidí guardar el explore en el repo. Esta bitácora partió de un borrador del agente que revisé y puse en mis palabras.
