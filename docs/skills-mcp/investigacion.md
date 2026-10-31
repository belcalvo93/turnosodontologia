# Ficha de investigación: skill propia y MCP para el sistema de turnos odontológico

Metodología I · UTN Mendoza · Equipo: Bruno Fiouchetta, Elías Tello, Belén Calvo, Hernán González, Joaquín Morán
Fecha: 2026-10-30 · Repositorio: https://github.com/belcalvo93/turnosodontologia

## 1. Necesidad detectada

Al preparar un change (explore, propose, specs, tasks) detectamos errores que se descubrían tarde: conteos de escenarios que no coinciden entre spec, tasks y verify; tests que agrupan varias reglas (la regla del proyecto es un test por RN-xx); y casos de borde faltantes (intervalos contiguos, recurso inexistente, rol sin permiso). Además, la API no tenía interfaz, así que no se podía ver funcionando. Por eso se agregó C-18 `frontend-minimo`: una interfaz mínima en TypeScript servida por la propia API (decisión D-09).

- **Skill:** automatiza la revisión de los specs de un change antes del apply.
- **MCP:** permite al agente generar y editar los diseños de pantalla a partir de la descripción del flujo (Stitch), como insumo del frontend de C-18.

## 2. Change elegido: C-18 `frontend-minimo`

Pendiente en `CHANGES.md` (FASE 5b). Sus dependencias (C-03, C-11, C-14, C-16) ya están en `main`. Cuatro pantallas (login, agenda de un profesional, crear turno y crear bloqueo con la lista `turnos_afectados`) que consumen solo endpoints existentes y respetan los roles. Está preparado (explore, proposal, design, specs con 15 escenarios, tasks) y **no está implementado**. La skill revisa los escenarios de su spec; Stitch genera el diseño de la pantalla de bloqueo, que `design.md` referencia.

## 3. Skill creadora y skill propia

- **Skill creadora:** `skill-creator`, oficial de Anthropic, en https://github.com/anthropics/skills (carpeta `skills/skill-creator`). Licencia Apache 2.0 (primera línea de su `LICENSE.txt`). Se copió a `.agents/skills/skill-creator/` desde el commit `ca45fc496a3436251f191354091d557da31c15b5`; su `SKILL.md` tiene el mismo hash que el del repositorio oficial en ese commit.
- **Compatibilidad:** OpenCode (documentación oficial) busca skills en `.opencode/skills/`, `.claude/skills/` y `.agents/skills/`. **Antigravity**: verificado en la práctica; al pedirle que leyera `AGENTS.md`, listó las skills de `.agents/skills/` incluida la propia. Cada skill es una carpeta con `SKILL.md` y frontmatter `name` y `description`.
- **Ubicación:** `.agents/skills/revisor-escenarios-sdd/SKILL.md`, dentro del repositorio, registrada en `.atl/skill-registry.md` y referenciada en `AGENTS.md` y `CLAUDE.md`.

| Aspecto | Diseño de `revisor-escenarios-sdd` |
|---|---|
| Propósito | Revisar los specs de un change antes del apply: ambigüedades, bordes faltantes y contraste con la base de conocimiento |
| Cuándo se activa | Al terminar un propose, o al pedir revisar escenarios de `specs/` |
| Entradas | Ruta del change (`openspec/changes/<nombre>/`) |
| Procedimiento | Contar escenarios reales; verificar formato Dado/Cuando/Entonces; cruzar cada escenario con su RN-xx; detectar reglas sin escenario; revisar bordes contra `errores-api`; comprobar que `tasks.md` dice cómo verificar cada escenario |
| Resultado | Tabla escenario → regla → verificación, y hallazgos con archivo y línea |
| Criterios de revisión | Mínimo 3 escenarios (esperado, error de negocio, borde); sin reglas nuevas sin justificar; todo hallazgo cita su fuente; solo lectura |

## 4. Comparación de servidores MCP y elección

Cambio de elección: el 29/10 se evaluó Context7 (documentación de librerías) frente a `mcp-server-sqlite` (descartado por estar archivado y permitir escritura). El 30/10 se rehízo la parte MCP: el docente indicó que se puede ampliar (Figma y Stitch como ejemplos) y se necesitaba un MCP útil para el frontend.

| | Stitch (Google) | Figma |
|---|---|---|
| Propósito | Generar y editar pantallas de interfaz desde texto | Leer diseños de Figma, generar código y escribir en el lienzo |
| Tipo y URL | Remoto: `https://stitch.googleapis.com/mcp` | Remoto: `https://mcp.figma.com/mcp` |
| Capacidades | 12 herramientas: `create_project`, `get_project`, `list_projects`, `list_screens`, `get_screen`, `generate_screen_from_text`, `edit_screens`, `generate_variants` y 4 de sistemas de diseño | `get_design_context`, entre otras (lista completa no verificada) |
| Autenticación | Clave de API u OAuth con gcloud | Inicio de sesión de Figma |
| Clientes documentados | Cursor, Antigravity, VS Code, Claude Code, Gemini CLI | VS Code |
| Costo | No figura en la documentación consultada | Planes Starter y superiores; gratuito no confirmado |
| Riesgos | Credencial: no versionarla; los prompts salen a Google | Requiere diseños previos en Figma |

**Elección: Stitch.** No necesita diseños previos ni desarrollar un servidor, y su resultado alimenta C-18. Cliente usado: **Antigravity**.

- **Requisitos:** cuenta de Google, SDK de Google Cloud (`gcloud`) y un proyecto de Google Cloud con la API de Stitch habilitada.
- **Autenticación (verificado):** la clave de API creada en Stitch permitió listar herramientas, pero las llamadas reales devolvieron `401: API keys are not supported by this API`. Se usa OAuth: `gcloud auth login`, `gcloud auth application-default login`, `gcloud services enable stitch.googleapis.com --project=<ID>`. El token dura aproximadamente 1 hora y debe renovarse.
- **Configuración:** Stitch no figura en el Marketplace de Antigravity; se agrega a mano en su configuración global de MCP (`~/.gemini/config/mcp_config.json`, fuera del repositorio) con `serverUrl: https://stitch.googleapis.com/mcp` y las cabeceras `Authorization: Bearer <token>` y `X-Goog-User-Project: <ID del proyecto>`. Nunca se envían clave y token juntos. Ejemplo sin secretos: `docs/skills-mcp/` (README).
- **Comprobar la conexión:** pedir al agente que use `list_projects`; una respuesta sin error de autenticación (aunque sea vacía) confirma la conexión. Luego `create_project` y `generate_screen_from_text`.
- **Qué puede consultar o modificar:** crear y editar proyectos y pantallas de la cuenta de Stitch; no toca el repositorio ni la base de datos.
- **Límites:** solo datos ficticios y el contrato público de la API; ningún dato de pacientes; credenciales fuera del repositorio, del informe y del video.
- **Pendiente de verificar:** costo y cuotas de Stitch; compatibilidad con OpenCode (no figura entre sus clientes documentados).

## 5. Archivos de la fundación a actualizar

`.atl/skill-registry.md` y `AGENTS.md`/`CLAUDE.md` (skill: hecho; MCP: propósito, momento de uso y límites); `README.md` (requisitos, autenticación, configuración sin secretos, comprobación); `docs/skills-mcp/` (ficha, informe y evidencias 01 a 05).

## 6. Fuentes

Consultadas el 2026-10-30:
- Stitch, documentación de MCP (botón Docs de https://stitch.withgoogle.com): clientes, claves de API y OAuth con gcloud.
- Foro de Google AI, reportes de autenticación en Stitch MCP: https://discuss.ai.google.dev/t/mcp-generate-screen-from-text-rejects-all-credentials-api-key-and-oauth-both-fail-management-tools-work/174160
- Figma, servidor MCP: https://help.figma.com/hc/en-us/articles/39890361040535-VS-Code-and-Figma-Set-up-the-MCP-server

Consultadas el 2026-10-29:
- Context7: https://context7.com/docs/installation
- OpenCode, MCP y skills: https://opencode.ai/docs/mcp-servers/ y https://opencode.ai/docs/skills/
- `mcp-server-sqlite`: https://pypi.org/project/mcp-server-sqlite/
- Anthropic, repositorio de skills: https://github.com/anthropics/skills (solo la fuente del autor)
