# Informe de aplicación: skill propia y MCP en el sistema de turnos odontológico

Metodología I · UTN Mendoza · Equipo: Bruno Fiouchetta, Elías Tello, Belén Calvo, Hernán González, Joaquín Morán
Repositorio: https://github.com/belcalvo93/turnosodontologia · Fecha: 2026-11-12

## 1. Qué se integró

- **Skill propia `revisor-escenarios-sdd`** (`.agents/skills/revisor-escenarios-sdd/SKILL.md`), creada con `skill-creator` de Anthropic y registrada en `.atl/skill-registry.md`, `AGENTS.md` y `CLAUDE.md`. Revisa los escenarios de un change antes del apply, sin modificar archivos.
- **MCP de Stitch** (Google), servidor remoto `https://stitch.googleapis.com/mcp`, usado desde Antigravity. Genera y edita diseños de pantalla. Documentado en `README.md`, `AGENTS.md` y `CLAUDE.md`.

## 2. Change aplicado: C-18 `frontend-minimo`

Interfaz mínima en TypeScript, servida por la propia API (decisión D-09), con cuatro pantallas: login, agenda de un profesional, crear turno y crear bloqueo con la lista `turnos_afectados`. Consume solo endpoints existentes y respeta los roles. **Quedó implementado, verificado y archivado** (`openspec/changes/archive/2026-11-11-c-18-frontend-minimo/`): 5 requirements, 17 escenarios y 17 tareas completadas; la suite pasa con 789 tests de pytest y 15 del frontend. En `CHANGES.md` figura `[x]`.

**Evidencia:** pruebas manuales por rol (tarea 4.4) en `docs/evidencia/c-18-*` (README de cada rol) y trazabilidad por escenario en `openspec/changes/archive/2026-11-11-c-18-frontend-minimo/verify.md`.

## 3. Cómo se usaron la skill y el MCP

1. **Stitch (MCP).** Se probó la conexión con `list_projects` (respuesta vacía, sin error de autenticación), se creó el proyecto con `create_project` y la pantalla de bloqueo con `generate_screen_from_text`. Al redactar `design.md`, el agente la leyó con `get_screen` y la referenció (proyecto `6865582647500750696`, pantalla `c0d0c78ded4b46778fd80bf0604d9ee2`). La maquetación de C-18 (`index.html` y `styles.css`) tomó de ahí la paleta y la estructura. Evidencia: `docs/skills-mcp/evidencias/03-stitch-mcp-invocaciones.md` y `03-stitch-pantalla-generada.png`.
2. **Skill.** Tras el propose, `revisor-escenarios-sdd` entregó una tabla de trazabilidad (escenario, regla RN-xx, verificación) y seis hallazgos con archivo y línea. Evidencia: `docs/skills-mcp/evidencias/04-revision-critica-c18-antes-despues.md`.

## 4. Revisión crítica: lo que no se aceptó tal cual

**Del diseño de Stitch.** La pantalla mostraba el aviso "se detectaron 3 turnos" antes de registrar el bloqueo, pero con C-16 la API devuelve `turnos_afectados` recién en la respuesta del `POST /bloqueos`; la interfaz los muestra después de registrar. "Notificar a todos", "Exportar lista" y el menú Pacientes/Reportes/Configuración no tienen endpoint y se descartaron.

**De la skill: H-01, antes y después.** Antes (`29051fa`), cinco escenarios del spec (login con credenciales inválidas, sesión vencida, agenda vacía, 422 al crear turno y 422 al crear bloqueo) no tenían tarea de verificación. Después (`23414dd`), la tarea 4.4 de `tasks.md` verifica cada uno con su código de error esperado (solo cambió `tasks.md`: 3 inserciones y 2 borrados), y una nueva pasada de la skill informó "H-01 quedó resuelto": los 15 escenarios tienen verificación (3 con pytest y 12 con la tarea 4.4).

H-02 a H-06 (por ejemplo, faltaba el escenario del odontólogo viendo su propia agenda) se corrigieron antes de `/opsx:apply`: el spec pasó de 15 a 17 escenarios (commit `ca21a17`) y se agregaron pruebas automáticas de la lógica del frontend (commit `fa4f0ae`).

## 5. Problemas encontrados y cómo se resolvieron

- La clave de API de Stitch listaba herramientas, pero las llamadas reales devolvían `401: API keys are not supported by this API`. Se pasó a OAuth con `gcloud` (cabeceras `Authorization: Bearer` y `X-Goog-User-Project`, sin enviar clave y token a la vez); el token dura cerca de una hora y se renueva.
- `gcloud beta services mcp enable` ya no existe; la API se habilita con `gcloud services enable stitch.googleapis.com`.
- Stitch no aparece en el Marketplace de Antigravity: se agregó a mano en la configuración global, fuera del repositorio.

## 6. Límites y riesgos

- Sin credenciales en el repositorio, el informe ni las evidencias; el token vive en la configuración local de cada integrante.
- Stitch recibe solo datos ficticios y el contrato público de la API; nunca datos de pacientes.
- La skill es de solo lectura: la decisión de corregir es humana.
- Pendiente de verificar: costo y cuotas de Stitch, y compatibilidad con OpenCode (no figura entre sus clientes documentados).
