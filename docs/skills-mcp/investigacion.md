# Ficha de investigación: skill propia y MCP para el sistema de turnos odontológico

Metodología I · UTN Mendoza · Equipo: Bruno Fiouchetta, Elías Tello, Belén Calvo, Hernán González, Joaquín Morán
Fecha: 2026-10-29 · Repositorio: https://github.com/belcalvo93/turnosodontologia

## 1. Necesidad detectada

Al preparar un change (explore, propose, specs, tasks) detectamos errores que se descubrían tarde: conteos de escenarios que no coinciden entre spec, tasks y verify; tests que agrupan varias reglas (la regla del proyecto es un test por RN-xx); y casos de borde faltantes (intervalos contiguos, recurso inexistente, rol sin permiso). También hace falta consultar documentación vigente del stack (FastAPI, Pydantic) sin depender de la memoria del agente.

- **Skill:** automatiza la revisión de los specs de un change antes del apply.
- **MCP:** da al agente acceso a documentación actualizada del stack al redactar el diseño.

## 2. Change elegido: C-16 `bloqueos-turnos-afectados`

Pendiente en `CHANGES.md`. Sus dependencias (C-09 y C-11) ya están en `main`, así que se puede preparar sin funcionalidades inexistentes. Extiende `POST /bloqueos` para devolver `turnos_afectados` (turnos reservados que se solapan con el bloqueo) sin cancelarlos (decisión SE-09 tomada el 2026-10-29 por la responsable del change). Tiene explore, proposal, design, specs y tasks; no está implementado. La skill revisa los escenarios de su spec y el MCP consulta documentación para su diseño.

## 3. Skill creadora y skill propia

- **Skill creadora:** `skill-creator`, oficial de Anthropic, en https://github.com/anthropics/skills (carpeta `skills/skill-creator`). Licencia Apache 2.0 (primera línea de su `LICENSE.txt`). Se copió a `.agents/skills/skill-creator/` desde el commit `ca45fc496a3436251f191354091d557da31c15b5`. El `SKILL.md` versionado tiene el mismo hash que el del repositorio oficial en ese commit, y la copia global que ya tenía OpenCode es idéntica (`diff` sin diferencias).
- **Compatibilidad con OpenCode** (documentación oficial): busca skills en `.opencode/skills/`, `.claude/skills/` y `.agents/skills/` (proyecto) y sus equivalentes globales. Cada skill es una carpeta con `SKILL.md` y frontmatter `name` (igual al nombre de la carpeta) y `description`. El agente carga la skill con su herramienta `skill`. Compatibilidad con Antigravity: no evaluada (el equipo trabaja con OpenCode).
- **Ubicación:** `.agents/skills/revisor-escenarios-sdd/SKILL.md`, dentro del repositorio, registrada en `.atl/skill-registry.md` y referenciada en `AGENTS.md` y `CLAUDE.md`.

| Aspecto | Diseño de `revisor-escenarios-sdd` |
|---|---|
| Propósito | Revisar los specs de un change antes del apply: ambigüedades, bordes faltantes y contraste con la base de conocimiento |
| Cuándo se activa | Al terminar un propose, o al pedir revisar escenarios de `specs/` |
| Entradas | Ruta del change (`openspec/changes/<nombre>/`) |
| Procedimiento | Contar escenarios reales; verificar formato Dado/Cuando/Entonces; cruzar cada escenario con su RN-xx en la KB; detectar reglas sin escenario; revisar bordes contra `errores-api`; comprobar que `tasks.md` dice cómo verificar cada escenario |
| Resultado | Tabla escenario → regla → verificación, y hallazgos con archivo y línea |
| Criterios de revisión | Mínimo 3 escenarios (esperado, error de negocio, borde); sin reglas nuevas sin justificar; todo hallazgo cita su fuente; solo lectura |

## 4. Comparación de servidores MCP y elección

| | Context7 | `mcp-server-sqlite` (referencia) |
|---|---|---|
| Propósito | Documentación actualizada de librerías | Consultas sobre una base SQLite |
| Tipo | Remoto (`https://mcp.context7.com/mcp`), requiere internet | Local (`uvx mcp-server-sqlite --db-path <ruta>`) |
| Capacidades | `context7_resolve-library-id` y `context7_query-docs` | `read_query`, `write_query`, `create_table`, `list_tables`, `describe-table`, `append_insight` |
| Compatibilidad con OpenCode | Sí (guía oficial; v1 desde 1.18.29 y v2) | No evaluada |
| Credenciales y costo | Sin clave en nuestra configuración; cuenta gratuita y API key opcionales. Plan Free USD 0 con 1.000 llamadas incluidas; Pro USD 10 por usuario/mes | Sin credenciales ni costo |
| Mantenimiento | Activo (a confirmar) | **Archivado** (sin actualizaciones desde 10/07/2025) |
| Riesgos | Sale a internet: no enviar datos del proyecto | Puede escribir y crear tablas; sin parches de seguridad |

**Elección: Context7.** Se descarta SQLite por estar archivado y exponer escritura. Context7 aporta a C-16 al verificar contra la documentación oficial de FastAPI cómo se serializa un modelo de respuesta heredado (tarea 3.3).

- **Estado de la instalación:** Active Stack ya lo trae configurado en la configuración global de OpenCode (`~/.config/opencode/opencode.json`): `"context7": {"type": "remote", "url": "https://mcp.context7.com/mcp", "enabled": true}`. Sin clave. Para reproducirlo en otra máquina: agregar ese bloque bajo `mcp` en su `opencode.json` (o seguir la guía oficial: `npx ctx7 setup --opencode`).
- **Comprobar la conexión:** `opencode mcp list` muestra `context7 connected`; `opencode mcp debug context7` diagnostica problemas de conexión.
- **Qué puede consultar o modificar:** solo documentación pública de librerías; no modifica nada del repositorio ni de la base.
- **Límites:** no incluir en las consultas datos de pacientes ni credenciales; el proyecto usa solo datos ficticios.
- **Pendiente:** confirmar con el docente que vale un MCP que ya viene preinstalado con Active Stack; si no, se elegirá otro.

## 5. Archivos de la fundación a actualizar

`.atl/skill-registry.md` y `AGENTS.md`/`CLAUDE.md` (skill: hecho; MCP: propósito, momento de uso y límites, pendiente); `README.md` (requisitos, configuración sin secretos y comprobación del MCP); `docs/skills-mcp/` (ficha, informe y evidencias).

## 6. Fuentes (consultadas el 2026-10-29)

- Context7, instalación: https://context7.com/docs/installation y para OpenCode: https://context7.com/docs/clients/opencode
- Context7, precios: https://context7.com (sección Pricing)
- OpenCode, servidores MCP: https://opencode.ai/docs/mcp-servers/ y skills: https://opencode.ai/docs/skills/
- `mcp-server-sqlite`: https://pypi.org/project/mcp-server-sqlite/
- Anthropic, repositorio de skills: https://github.com/anthropics/skills (solo la fuente del autor; se descartan copias de terceros)
