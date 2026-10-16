# Bitácora de decisiones — Belén Calvo

**Proyecto:** Sistema de gestión de turnos odontológicos (Metodología I, UTN Mendoza).  
**Repositorio:** https://github.com/belcalvo93/turnosodontologia  
**Rama:** `Belen-Calvo`

## Decisiones

| # | Etapa | Qué decidí | Qué otra opción había | Por qué | Dónde quedó |
|---|---|---|---|---|---|
| 1 | 0 | Desactivar Smart App Control de Windows. | Dejarlo activo y no poder correr el instalador. | Me bloqueaba el `.exe` de Active Stack con el error "Permission denied". Sabía que después no se puede reactivar sin reinstalar Windows y aun así lo desactivé. | `docs/evidencia/etapa-0-belen/` |
| 2 | 0 | Instalar Active Stack en modo Full con permisos balanceados. | Lite o Custom. | Es el modo que pide la consigna y deja todos los harnesses disponibles. | `belen-04-modo-full.png`, `belen-05-permisos.png` |
| 3 | 0 | Usar Claude Code en vez de OpenCode. | Seguir intentando que funcionara OpenCode. | OpenCode no funcionaba correctamente: npm bloqueaba el postinstall y lo resolví con `--allow-scripts`. Además, la aplicación de escritorio pedía una API key paga. Claude Code funcionó enseguida. | — |
| 4 | 0 | No pagar ninguna API key para OpenCode. | Contratar un proveedor. | No necesitaba pagar una API key para cumplir la consigna y la versión de terminal ya funcionaba. | — |
| 5 | 2 | Marcar mi fuente (centro de ayuda de Dentalink, la #3) como **Parcial**. | Confirmada o No confirmada. | Una parte de lo que dice el Discovery sí está en la fuente y otra parte no pude comprobarla. | `docs/discovery/verificacion-belen.md` |
| 6 | 1 | Ignorar las memorias viejas de Engram (#10 y #11) y no borrarlas. | Borrarlas. | Eran de un intento anterior, no las necesitábamos y no había razón para borrarlas. | — |
| 7 | 3 | Definir un stack provisional (D-01): Python 3.11+, FastAPI, pytest y SQLite, con el dominio separado del framework. | Usar otros lenguajes y frameworks. | Lo definimos en el grupo: SQLite alcanza para el MVP y el dominio se puede probar sin depender del framework. | `knowledge-base/` |
| 8 | 3 | No aprobar la knowledge-base a la primera y pedir ajustes. | Aprobarla tal como estaba. | Faltaban los feriados (SE-24) y la fila del endpoint `usuarios` en el documento 02. Además, el error 409 era diferente en los documentos 06 y 07. | `knowledge-base/` (commit `53f9349`) |
| 9 | 4 | No ejecutar el plan viejo de kb-creator que reapareció en modo Plan. | Ejecutarlo. | Era de una sesión anterior y habría regenerado la KB que ya estaba aprobada. | — |
| 10 | 4 | Dejar los 17 changes (C-01 a C-17) en el roadmap (`CHANGES.md`) sin preseleccionar ninguno. | Elegir el primero directamente en el roadmap. | La consigna pide elegirlo y justificarlo en el propose. | `CHANGES.md` |
| 11 | 6 | Pedir ajustes al propose de C-10 de Hernán (PR #9). | Aprobarlo. | Faltaba la base técnica en las tareas, los escenarios de fuera de horario y de bloqueo en la spec, y había una inconsistencia entre la limpieza de 45 minutos y la de 30 minutos. | PR #9, `openspec/changes/archive/2026-10-15-c-10-reglas-alta-turno/` |
| 12 | 6 | Probar el repositorio desde cero con un clon limpio. | Confiar en que el cambio estaba archivado y funcionaba. | Cloné el repositorio, instalé las dependencias con `requirements.txt` y ejecuté `pytest tests/domain/ -v`. Los 32 tests pasaron correctamente. | — |
| 13 | 0 | Guardar mi evidencia en `docs/evidencia/etapa-0-belen/`. | Usar una carpeta `etapa-0` compartida. | La Etapa 0 la realiza cada integrante por separado, así que guardar las capturas en una carpeta propia evita mezclarlas con las de los demás. | `docs/evidencia/etapa-0-belen/` |

## Pendiente de decidir en el grupo

**Skills de terceros:** cuatro de las cinco skills vienen de `wshobson/agents`, no de Anthropic. Tenemos que decidir si las revisamos buscando comandos como `curl`, `sudo`, `rm -rf`, `eval` y URLs; si nos quedamos solamente con `fastapi` y `python-testing-patterns`; o si decidimos no usar ninguna.

## Uso de IA

Usé Opencode y Claude (chat y Claude Code) para que me guiara paso a paso, y me ayudara en la toma de decisiones explicandome las cosas cuando yo no entendia, tambien los use con Git y el instalador, y para revisar la knowledge-base y el propose de C-10.

Las decisiones de la tabla las tomé yo. También verifiqué mi fuente y escribí mi reflexión por mi cuenta.

**Algo que corregí:** la IA dio por hecho que `verificacion-belen.md` había sido creado por una herramienta, cuando yo lo había escrito manualmente en VS Code. Este caso me recordó que no alcanza con confiar en lo que informa la IA: también tengo que comprobar qué hice realmente y qué quedó registrado en el repositorio.

Por otro lado Claude me armó la evidencia en una carpeta etapa-0 compartida. Yo noté que la Etapa 0 es por persona y pedí que quedara en `etapa-0-belen`
