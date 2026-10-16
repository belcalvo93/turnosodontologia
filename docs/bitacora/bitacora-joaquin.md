# Bitácora de decisiones — Joaquín Moran

**Proyecto:** Sistema de gestión de turnos odontológicos (Metodología I, UTN Mendoza).
**Repositorio:** https://github.com/belcalvo93/turnosodontologia
**Rama:** `joaquin`
**Etapas a cargo:** etapa 2 (verificación de la fuente 5) y etapa 6 (apply, verify y archive de C-10, y README).

## Decisiones

| # | Etapa | Qué decidí | Qué otra opción había | Por qué | Dónde quedó |
|---|---|---|---|---|---|
| 1 | 0 | Autenticar git con la cuenta `joaquinmo1`, que era la invitada como colaboradora. | Pedir una invitación nueva para la otra cuenta. | El push daba error 403 porque git usaba otra cuenta mía sin permisos. | — |
| 2 | 0 | Instalar Active Stack en modo Full con Claude Code y mantener los permisos en modo manual. | Usar el modo automático de permisos. | Quería ver y aprobar cada acción del agente para poder explicarla y frenarla si se desviaba del spec. | `docs/evidencia/etapa-0-joaquin/` |
| 3 | 0 | Instalar WSL para Docker y, cuando no arrancó por la virtualización desactivada, seguir sin Docker. | Activar la virtualización en la BIOS. | El stack del change (D-01) no necesita Docker. | — |
| 4 | 0 | Guardar mi evidencia en `docs/evidencia/etapa-0-joaquin/`. | Usar una carpeta compartida. | La Etapa 0 la hace cada integrante; así se sigue la misma convención que Belén y Elías. | `docs/evidencia/etapa-0-joaquin/` |
| 5 | 2 | Marcar la fuente 5 (tutoriales de AgendaPro) como "Sí, con precisiones". | Confirmada sin precisiones, o Parcial. | Los 2 manuales y los 7 videos estaban, pero "no hay tutoriales de agenda" era parcial: uno explica cómo configurar el período de reservas. También anoté que los videos son de 2015 y que la empresa es chilena. | `docs/discovery/verificacion-joaquin.md` |
| 6 | 3 | Proponer que el change use Python, FastAPI, pytest y SQLite, sin PostgreSQL ni Docker. | PostgreSQL y Docker, como decía el estado del orquestador. | Para que los tests corran solo con clonar, instalar y ejecutar pytest. El grupo lo dejó como D-01. | `knowledge-base/09_decisiones_y_supuestos.md` |
| 7 | 6 | Proponer acotar el change a C-10 (reglas de alta, dominio puro). | C-11 completo. | C-11 depende de otros 9 changes (login, profesionales, pacientes, horarios, bloqueos). | `proposal.md` del change |
| 8 | 6 | Agregar un `.gitignore` antes del apply. | Trabajar sin `.gitignore`. | El repo no tenía y se iban a subir `.venv` y la caché de pytest. | commit `0cb8d12` |
| 9 | 6 | Hacer el apply una tarea por vez y commitear yo cada tarea. | Dejar que el agente hiciera los commits o un solo commit al final. | El historial tenía que mostrar el proceso y los commits tenían que ser míos (regla 13 de AGENTS.md). | commits `5fe957f` a `591676a` |
| 10 | 6 | No agregar `DatoInvalido` por duración inválida. | Implementarlo porque lo mencionaba el design. | No estaba en el spec ni en las tareas, y RN-REC-01 ya valida la duración al crear la prestación (C-05). | Engram y `verify.md` |
| 11 | 6 | Aceptar que el agente corrigiera el caso `excluir_turno_id=None`, con un test que primero fallara. | Dejarlo como estaba porque los tests ya pasaban. | Con `None == None`, un turno sin id se salteaba y se podía aceptar un turno superpuesto. Es parte de RN-TUR-08. | commit `17b9f39` |
| 12 | 6 | Aceptar la prueba de mutación de la tarea 2.3, sin dar permiso permanente a `git checkout`. | Dar permiso permanente. | La prueba demostró que los tests detectan el error, pero no quería dejar al agente descartar cambios sin preguntar. | `verify.md` |
| 13 | 6 | Documentar el verify en `verify.md` dentro del change. | Mostrar solo una captura. | OpenSpec no tiene una fase de verificación propia en esta instalación y la consigna pide documentar el resultado. | `openspec/changes/archive/2026-10-15-c-10-reglas-alta-turno/verify.md` |
| 14 | 6 | Sincronizar el spec al archivar. | Archivar sin sincronizar. | La consigna pide que el estado del proyecto quede actualizado. | `openspec/specs/reglas-alta-turno/spec.md` |
| 15 | 6 | Corregir C-10 en `CHANGES.md` de "`[x]` pendiente" a "`[x]` completado". | Dejarlo como lo marcó el agente. | La casilla y la palabra se contradecían. | commit `e4eb5c1` |
| 16 | 6 | Rehacer el README con el clonado, los requisitos y el aviso de PowerShell. | Dejar el README de la tarea 0.1. | La consigna pide poder clonar y correr los tests siguiendo solo el README. Lo probé desde un clon nuevo: 32 passed. | commit `2d79a8d` |

## Uso de IA

Usé la IA como guía paso a paso para instalar el Active Stack, resolver los problemas de git (el error 403, las ramas y el PR) y entender cada etapa del apply. El agente escribió el código con Strict TDD, pero yo aprobé cada permiso y cada commit.