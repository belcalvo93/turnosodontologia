# Bitácora de decisiones — Belén Calvo

**Proyecto:** Sistema de gestión de turnos odontológicos (Metodología I, UTN Mendoza).  
**Repositorio:** https://github.com/belcalvo93/turnosodontologia  
**Rama:** `Belen-Calvo`, `belen-skills-mcp`, `belen-c18-apply`, `belen-docs-actualizar-decisiones`, `belen-readme-limitaciones`, `belen-docs-cierre-c18`, `belen-docs-skills-mcp-final`

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
| 14 | 6 | Elegir C-18 (`frontend-minimo`) para aplicar la skill y el MCP y llevarlo hasta implementado, verificado y archivado. | Dejarlo solo preparado, sin implementar. | La consigna cuenta como válidos los changes aplicados, verificados y archivados, y el profesor pidió mostrar el sistema funcionando. | Change archivado `2026-11-11-c-18-frontend-minimo`, PR #54 y #55 |
| 15 | 6 | Conectar el MCP de Stitch con OAuth (gcloud) en vez de seguir con la clave de API. | Seguir con la clave de API. | La clave solo permitía listar herramientas; las llamadas reales devolvían 401 "API keys are not supported by this API". | `docs/skills-mcp/aplicacion.md` sección 5 y `docs/skills-mcp/evidencias/03-stitch-mcp-invocaciones.md` |
| 16 | 6 | Crear la skill propia `revisor-escenarios-sdd` y usarla sobre el spec de C-18 antes del apply. | Revisar los escenarios a mano. | Encontró seis hallazgos con archivo y línea; los corregimos y el spec pasó de 15 a 17 escenarios. | `docs/skills-mcp/evidencias/04-revision-critica-c18-antes-despues.md`, commits `ca21a17` y `fa4f0ae` |
| 17 | 6 | Pedir una interfaz profesional, sin códigos RN en pantalla, y llamar "Sillón de atención" al recurso en vez de "Box". | Dejar "Sillón" sin explicación o usar "Box". | En la clínica que conozco, "box" es el lugar de admisión, no donde se atiende al paciente; el texto de ayuda lo aclara. | `app/static/index.html` y `app/static/styles.css` (tarea 1.2) |
| 18 | 6 | Dividir C-18 en un módulo por vista y repartir las tareas entre los cinco. | Hacerlo yo sola. | Permite trabajar en paralelo sin pisarnos los archivos, y que todos participen del change. | `design.md` (D8) y `tasks.md` del change archivado, PR #55 |
| 19 | 6 | Pedir cambios en el PR de Joaquín (3.4, 3.5 y 4.5) antes de mergearlo. | Aprobarlo tal cual. | Al probar la rama aparecieron tres detalles: errores de carga sin aviso, una función duplicada y la alerta de éxito. | PR #62 y #63 |
| 20 | 7 | Autorizar de forma explícita los cambios en archivos protegidos (`CHANGES.md`, `AGENTS.md`, `CLAUDE.md` y D-03 y D-07 de la KB). | Dejarlos desactualizados. | Esos archivos solo se tocan con autorización (regla dura 14) y estaban desactualizados respecto al código. | PR #57 y #73 |
| 21 | 7 | Dejar WhatsApp y el portal de reservas para pacientes como "Próximos pasos". | Implementarlos antes del 20/11. | Quedaron fuera del MVP por costo y por requerir proveedor oficial, y el profesor prioriza lo terminado, probado y archivado. | README, secciones "Limitaciones y supuestos" y "Próximos pasos" (PR #64) |

## Pendiente de decidir en el grupo

**Skills de terceros:** cuatro de las cinco skills vienen de `wshobson/agents`, no de Anthropic. Tenemos que decidir si las revisamos buscando comandos como `curl`, `sudo`, `rm -rf`, `eval` y URLs; si nos quedamos solamente con `fastapi` y `python-testing-patterns`; o si decidimos no usar ninguna.

## Uso de IA

Usé Opencode y Claude (chat y Claude Code) para que me guiara paso a paso, y me ayudara en la toma de decisiones explicandome las cosas cuando yo no entendia, tambien los use con Git y el instalador, y para revisar la knowledge-base y el propose de C-10.

Las decisiones de la tabla las tomé yo. También verifiqué mi fuente y escribí mi reflexión por mi cuenta.

Para C-18 usé Claude Code (implementación de las tareas 1.1 y 1.2 y ajustes de documentación) y Claude como guía paso a paso para armar los comandos y revisar los diffs. Revisé cada diff antes de commitear.

**Algo que corregí:** la IA dio por hecho que `verificacion-belen.md` había sido creado por una herramienta, cuando yo lo había escrito manualmente en VS Code. Este caso me recordó que no alcanza con confiar en lo que informa la IA: también tengo que comprobar qué hice realmente y qué quedó registrado en el repositorio.

Por otro lado Claude me armó la evidencia en una carpeta etapa-0 compartida. Yo noté que la Etapa 0 es por persona y pedí que quedara en `etapa-0-belen`

La IA propuso llamar "Box" al recurso donde se atiende al paciente. Lo corregí porque en la clínica que conozco "box" es el lugar de admisión; quedó como "Sillón de atención" con un texto de ayuda.
