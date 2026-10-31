# Informe de aplicación: skill propia y MCP en el sistema de turnos odontológico

Metodología I · UTN Mendoza · Equipo: Bruno Fiouchetta, Elías Tello, Belén Calvo, Hernán González, Joaquín Morán
Repositorio: https://github.com/belcalvo93/turnosodontologia · Fecha: 2026-10-30

## 1. Qué se integró

- **Skill propia `revisor-escenarios-sdd`** (`.agents/skills/revisor-escenarios-sdd/SKILL.md`), creada con la skill `skill-creator` de Anthropic, registrada en `.atl/skill-registry.md` y referenciada en `AGENTS.md` y `CLAUDE.md`. Revisa los escenarios de un change antes del apply y no modifica archivos.
- **MCP de Stitch** (Google), servidor remoto `https://stitch.googleapis.com/mcp`, usado desde Antigravity. Es una integración con un servicio externo, no una skill: genera y edita diseños de pantalla. Está documentado en `README.md` y en la sección MCP de `AGENTS.md` y `CLAUDE.md`.

## 2. Change preparado: C-18 `frontend-minimo`

C-18 agrega una interfaz mínima en TypeScript, servida por la propia API, con cuatro pantallas: login, agenda de un profesional, crear turno y crear bloqueo con la lista `turnos_afectados` (decisión D-09). Consume solo endpoints existentes y respeta los roles. **Quedó preparado y no implementado**: `proposal.md`, `design.md`, `specs/frontend-minimo/spec.md` (5 requirements y 15 escenarios, cada requirement con camino esperado, error de negocio y caso de borde) y `tasks.md` (15 tareas con verificación), en `openspec/changes/c-18-frontend-minimo/`. En `CHANGES.md` sigue como pendiente (`[ ]`).

## 3. Cómo se usaron la skill y el MCP

1. **Stitch (MCP).** Se probó la conexión con `list_projects` (respuesta vacía, sin error de autenticación), se creó el proyecto con `create_project` y se generó la pantalla de bloqueo con `generate_screen_from_text`. Al redactar `design.md`, el agente leyó esa pantalla con `get_screen` y la referenció (proyecto `6865582647500750696`, pantalla `c0d0c78ded4b46778fd80bf0604d9ee2`). Evidencia: `docs/skills-mcp/evidencias/03-stitch-mcp-invocaciones.md` y la captura `03-stitch-pantalla-generada.png`.
2. **Skill.** Tras el propose, se ejecutó `revisor-escenarios-sdd` sobre el change. Entregó una tabla de trazabilidad (escenario, regla RN-xx, verificación) y seis hallazgos con archivo y línea. Evidencia: `docs/skills-mcp/evidencias/04-revision-critica-c18-antes-despues.md`.

## 4. Revisión crítica: lo que no se aceptó tal cual

**Del diseño de Stitch.** La pantalla mostraba el aviso "se detectaron 3 turnos" antes de registrar el bloqueo, pero con C-16 la API devuelve `turnos_afectados` recién en la respuesta del `POST /bloqueos`; la interfaz muestra el aviso y la tabla después de registrar. Además, "Notificar a todos", "Exportar lista" y el menú Pacientes/Reportes/Configuración no tienen endpoint y se descartaron como fuera de alcance.

**De la skill: defecto corregido (antes / después).**

| | Antes (`29051fa`) | Después (`23414dd`) |
|---|---|---|
| Hallazgo H-01 (severidad alta) | Cinco escenarios del spec (login con credenciales inválidas, sesión vencida, agenda vacía, 422 al crear turno y 422 al crear bloqueo) no tenían tarea de verificación | La tarea 4.4 de `tasks.md` verifica cada uno, citado por su nombre exacto y con el código de error esperado |
| Cambio | — | Solo `tasks.md`: 1 línea nueva y 2 reformuladas (3 inserciones y 2 borrados en el diff) |
| Nueva pasada de la skill | Hallazgo presente | "H-01 quedó resuelto": los 15 escenarios tienen verificación (3 con pytest y 12 con la tarea 4.4) |

Quedan abiertos, a propósito, H-02 a H-06 (por ejemplo, falta un escenario del odontólogo viendo su propia agenda); se revisan antes de `/opsx:apply`.

## 5. Problemas encontrados y cómo se resolvieron

- La clave de API de Stitch permitía listar herramientas pero las llamadas reales devolvían `401: API keys are not supported by this API`. Se pasó a OAuth con `gcloud`, con las cabeceras `Authorization: Bearer` y `X-Goog-User-Project`; no deben enviarse clave y token a la vez.
- El comando `gcloud beta services mcp enable` ya no existe; la API se habilita con `gcloud services enable stitch.googleapis.com`.
- Stitch no aparece en el Marketplace de Antigravity: se agregó a mano en la configuración global de MCP, fuera del repositorio.
- El token dura aproximadamente una hora y debe renovarse.

## 6. Límites y riesgos

- No hay credenciales en el repositorio, el informe ni las evidencias; el token vive solo en la configuración local de cada integrante.
- Stitch recibe únicamente descripciones con datos ficticios y el contrato público de la API; nunca datos de pacientes.
- La skill es de solo lectura: informa hallazgos y la decisión de corregir es humana.
- Pendiente de verificar: costo y cuotas de Stitch, y compatibilidad con OpenCode (no figura entre sus clientes documentados).
