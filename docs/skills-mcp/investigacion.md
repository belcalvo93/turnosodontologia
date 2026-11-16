# Ficha de investigación: skill propia y MCP para el sistema de turnos odontológico

Metodología I · UTN Mendoza · Equipo: Bruno Fiouchetta, Elías Tello, Belén Calvo, Hernán González, Joaquín Morán
Fecha: 2026-11-12 · Repositorio: https://github.com/belcalvo93/turnosodontologia

## 1. Necesidad detectada

Al preparar un change aparecían errores tardíos: conteos de escenarios distintos entre spec, tasks y verify; tests que agrupan varias reglas (va un test por RN-xx); y bordes faltantes (intervalos contiguos, recurso inexistente, rol sin permiso). Además, la API no tenía interfaz para verla funcionando.

- **Skill:** revisa los specs de un change al terminar el propose y antes del apply; recibe la ruta del change.
- **MCP:** genera y edita diseños de pantalla desde la descripción del flujo (Stitch), como insumo del frontend.

## 2. Change elegido: C-18 `frontend-minimo`

Interfaz mínima en TypeScript servida por la propia API (decisión D-09), con cuatro pantallas: login, agenda de un profesional, crear turno y crear bloqueo con la lista `turnos_afectados`. Sus dependencias (C-03, C-11, C-14, C-16) ya estaban en `main`. La skill revisó su spec antes del apply (de 15 a 17 escenarios) y Stitch generó la pantalla de bloqueo que `design.md` referencia. Completado en `CHANGES.md` (FASE 5b) y archivado; detalle en `docs/skills-mcp/aplicacion.md`.

## 3. Skill creadora y skill propia

- **Skill creadora:** `skill-creator`, oficial de Anthropic, en https://github.com/anthropics/skills (carpeta `skills/skill-creator`), licencia Apache 2.0. Se copió a `.agents/skills/skill-creator/` desde el commit `ca45fc496a3436251f191354091d557da31c15b5`; su `SKILL.md` tiene el mismo hash que el oficial en ese commit.
- **Compatibilidad:** OpenCode (documentación oficial) busca skills en `.opencode/skills/`, `.claude/skills/` y `.agents/skills/`. Antigravity, verificado en la práctica: al leer `AGENTS.md` listó las skills, incluida la propia.
- **Ubicación:** `.agents/skills/revisor-escenarios-sdd/SKILL.md`, registrada en `.atl/skill-registry.md`, `AGENTS.md` y `CLAUDE.md`.

| Aspecto | Diseño de `revisor-escenarios-sdd` |
|---|---|
| Procedimiento | Contar escenarios; verificar Dado/Cuando/Entonces; cruzar cada escenario con su RN-xx; detectar reglas sin escenario; revisar bordes contra `errores-api`; comprobar que `tasks.md` verifica cada escenario |
| Resultado | Tabla escenario → regla → verificación, y hallazgos con archivo y línea |
| Criterios | Mínimo 3 escenarios (esperado, error de negocio, borde); sin reglas nuevas sin justificar; todo hallazgo cita su fuente; solo lectura |

## 4. Comparación de servidores MCP y elección

El 29/10 se evaluó Context7 frente a `mcp-server-sqlite` (descartado: archivado y permite escritura). El 30/10 se rehízo la elección: el docente permitió ampliar (Figma, Stitch) y hacía falta un MCP útil para el frontend.

| | Stitch (Google) | Figma |
|---|---|---|
| Propósito | Generar y editar pantallas desde texto | Leer diseños de Figma, generar código y escribir en el lienzo |
| Tipo y URL | Remoto: `https://stitch.googleapis.com/mcp` | Remoto: `https://mcp.figma.com/mcp` |
| Capacidades | 12 herramientas: proyectos, pantallas (`generate_screen_from_text`, `edit_screens`, `generate_variants`) y 4 de sistemas de diseño | `get_design_context`, entre otras (lista completa no verificada) |
| Clientes documentados | Cursor, Antigravity, VS Code, Claude Code, Gemini CLI | VS Code |
| Costo | No figura en la documentación consultada | Planes Starter y superiores; gratuito no confirmado |

**Elección: Stitch.** No exige diseños previos (Figma sí) ni desarrollar un servidor, y su resultado alimenta C-18. Cliente: **Antigravity**. Figma se autentica con su inicio de sesión.

- **Requisitos:** cuenta de Google, `gcloud` y un proyecto de Google Cloud con la API de Stitch habilitada.
- **Autenticación y configuración:** la clave de API devolvió `401: API keys are not supported by this API`, así que se usa OAuth con `gcloud` (token de ~1 hora). Stitch no figura en el Marketplace de Antigravity: se agrega a mano en su configuración global, fuera del repositorio. Pasos y ejemplo sin secretos: `README.md`.
- **Comprobar la conexión:** pedir al agente `list_projects`; una respuesta sin error de autenticación (aunque sea vacía) la confirma. Para probar una operación real, usar `create_project` y luego `generate_screen_from_text` con datos ficticios.
- **Qué puede modificar:** proyectos y pantallas de la cuenta de Stitch; no toca el repositorio ni la base de datos.
- **Límites y riesgos:** los prompts salen a Google: solo datos ficticios y el contrato público de la API, nunca datos de pacientes; credenciales fuera del repositorio, del informe y del video.
- **Pendiente de verificar:** costo y cuotas de Stitch; compatibilidad con OpenCode (no figura entre sus clientes documentados).

## 5. Fuentes

Consultadas el 2026-10-30:
- Stitch, documentación de MCP (botón Docs de https://stitch.withgoogle.com): clientes, claves de API y OAuth con gcloud.
- Foro de Google AI, reportes de autenticación en Stitch MCP: https://discuss.ai.google.dev/t/mcp-generate-screen-from-text-rejects-all-credentials-api-key-and-oauth-both-fail-management-tools-work/174160
- Figma, servidor MCP: https://help.figma.com/hc/en-us/articles/39890361040535-VS-Code-and-Figma-Set-up-the-MCP-server

Consultadas el 2026-10-29:
- Context7: https://context7.com/docs/installation
- OpenCode, MCP y skills: https://opencode.ai/docs/mcp-servers/ y https://opencode.ai/docs/skills/
- `mcp-server-sqlite`: https://pypi.org/project/mcp-server-sqlite/
- Anthropic, repositorio de skills: https://github.com/anthropics/skills (solo la fuente del autor)
