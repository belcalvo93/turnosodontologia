# Evidencia 05 — Revisión crítica con la skill `revisor-escenarios-sdd` (antes / después)

Skill propia: `.agents/skills/revisor-escenarios-sdd/SKILL.md` (solo lectura). Cliente: Antigravity.
Change revisado: `openspec/changes/c-18-frontend-minimo/` (proposal, design, spec con 15 escenarios, tasks).

## Prompt usado

> Usá la skill revisor-escenarios-sdd sobre openspec/changes/c-18-frontend-minimo/. Seguí su SKILL.md al pie de la letra: tabla de trazabilidad y hallazgos ordenados por severidad, con cita exacta de archivo y línea. No modifiques ningún archivo.

La skill respondió `Used skill: revisor-escenarios-sdd (solo lectura — ningún archivo fue creado ni modificado)`.

## Antes — defecto detectado (severidad ALTA)

**H-01 — falta de verificación.** Cinco escenarios del spec no tenían ninguna tarea que los verificara (ni en pytest ni en el checklist manual de `tasks.md`):

- *Credenciales inválidas muestran el mensaje 401 de la API* (`spec.md:41`)
- *Sesión vencida o token inválido redirige al login con mensaje en español* (`spec.md:47`)
- *Agenda sin turnos ni bloqueos en el rango seleccionado* (`spec.md:69`)
- *Envío con datos inválidos muestra el error 422 en español* (`spec.md:91`)
- *Intervalo de bloqueo inválido muestra el error 422 en español* (`spec.md:107`)

Por qué importa: de aplicar el change sin corregirlo, se habría podido dar por verificado sin probar ningún caso de error 401/422 ni el estado vacío.

Commit con el estado **antes**: `29051fa`.

## Corrección (cambio mínimo, solo `tasks.md`)

Se agregaron al checklist manual de la tarea 4.4 las verificaciones de esos cinco escenarios, citados por su nombre exacto del spec y con el código de error esperado (`401 credenciales_invalidas`, `401 no_autenticado`, `422 dato_invalido`). No se tocó el spec, el design ni el proposal. `openspec validate c-18-frontend-minimo --strict` siguió válido.

Commit con el estado **después**: `23414dd` (`git diff 29051fa 23414dd`: 1 archivo, 3 inserciones, 2 borrados).

## Después — nueva pasada de la skill

Resultado: *"[H-01] quedó RESUELTO"*. Los 15 escenarios tienen verificación: 3 con pytest + TestClient (tareas 2.1 y 4.2) y 12 con la tarea 4.4. Las cinco filas corregidas aparecen marcadas ✅ en la tabla de trazabilidad.

## Hallazgos que quedan abiertos (no se corrigieron a propósito)

H-02 (falta escenario del odontólogo viendo su propia agenda), H-03 (filtrado de recursos inactivos sin escenario), H-04 (ambigüedad de `detalles` en 422 de dominio), H-05 (citas RN-TUR-02 / RN-REC-03 faltantes), H-06 (identificadores DOM no fijados en el spec). Se revisan antes de `/opsx:apply`.

Capturas que acompañan esta evidencia: respuesta completa de la skill (antes) y respuesta de la segunda pasada (después).
