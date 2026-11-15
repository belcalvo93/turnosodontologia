# Informe de aplicación: skill propia y MCP en el sistema de turnos odontológico

Metodología I · UTN Mendoza · Equipo: Bruno Fiouchetta, Elías Tello, Belén Calvo, Hernán González, Joaquín Morán
Repositorio: https://github.com/belcalvo93/turnosodontologia · Fecha: 2026-11-12

## 1. Qué se integró

- **Skill propia `revisor-escenarios-sdd`** (`.agents/skills/revisor-escenarios-sdd/SKILL.md`), creada con la skill `skill-creator` de Anthropic, registrada en `.atl/skill-registry.md` y referenciada en `AGENTS.md` y `CLAUDE.md`. Revisa los escenarios de un change antes del apply y no modifica archivos.
- **MCP de Stitch** (Google), servidor remoto `https://stitch.googleapis.com/mcp`, usado desde Antigravity. Es una integración con un servicio externo, no una skill: genera y edita diseños de pantalla. Está documentado en `README.md` y en la sección MCP de `AGENTS.md` y `CLAUDE.md`.

## 2. Change aplicado: C-18 `frontend-minimo`

C-18 agrega una interfaz mínima en TypeScript, servida por la propia API, con cuatro pantallas: login, agenda de un profesional, crear turno y crear bloqueo con la lista `turnos_afectados` (decisión D-09). Consume solo endpoints existentes y respeta los roles. **Quedó implementado, verificado y archivado** (`openspec/changes/archive/2026-11-11-c-18-frontend-minimo/`): 5 requirements, 17 escenarios y 17 tareas, todas completadas. El `verify.md` traza cada escenario a un test o a una evidencia manual por rol (`docs/evidencia/c-18-*`); la suite pasa con 789 tests de pytest y 15 del frontend. En `CHANGES.md` figura como completado (`[x]`).

**Evidencias del frontend en funcionamiento (pruebas manuales por rol, tarea 4.4):**

- **Rol Administración (Bruno Fiouchetta)** — [`docs/evidencia/c-18-administracion-bruno/README.md`](../evidencia/c-18-administracion-bruno/README.md):
  - Login y acceso a las tres vistas (`RN-ACC-02`): [`01-administracion-login-vistas.jpg`](../evidencia/c-18-administracion-bruno/01-administracion-login-vistas.jpg)
  - Alta de turno válida (`201`) con horario calculado por prestación (`RN-TUR-01`, `RN-TUR-02`): [`02-administracion-crear-turno-201.jpg`](../evidencia/c-18-administracion-bruno/02-administracion-crear-turno-201.jpg)
  - Bloqueo superpuesto mostrando la tabla `turnos_afectados` sin cancelar el turno (`RN-TUR-05`, `RN-TUR-08`): [`03-administracion-bloqueo-turnos-afectados.jpg`](../evidencia/c-18-administracion-bruno/03-administracion-bloqueo-turnos-afectados.jpg)
  - Bloqueo sin turnos afectados, mostrando el estado vacío (`turnos_afectados = []`): [`04-administracion-bloqueo-sin-turnos-afectados.jpg`](../evidencia/c-18-administracion-bruno/04-administracion-bloqueo-sin-turnos-afectados.jpg)
  - Bloqueo con intervalo inválido (`inicio >= fin`) rechazado con `422` en español (`RN-REC-02`, `RN-GLO-01`): [`05-administracion-bloqueo-422.jpg`](../evidencia/c-18-administracion-bruno/05-administracion-bloqueo-422.jpg)
- **Rol Recepción (Hernán González)** — [`docs/evidencia/c-18-recepcion-hernan/README.md`](../evidencia/c-18-recepcion-hernan/README.md):
  - Login con barra adaptada (sin bloqueo) y consulta de agenda con datos ficticios (`RN-ACC-02`, `RN-PAC-03`): [`01-recepcion-agenda-con-paciente.png`](../evidencia/c-18-recepcion-hernan/01-recepcion-agenda-con-paciente.png)
  - Agenda sin turnos ni bloqueos en el período consultado (`items = []`): [`02-recepcion-agenda-vacia.png`](../evidencia/c-18-recepcion-hernan/02-recepcion-agenda-vacia.png)
  - Rechazo `409` al intentar crear turno en horario bloqueado o solapado (`RN-TUR-03`, `RN-TUR-05`): [`03-recepcion-crear-turno-409.png`](../evidencia/c-18-recepcion-hernan/03-recepcion-crear-turno-409.png)
  - Rechazo `422` al enviar datos inválidos en el alta de turno (`RN-GLO-01`): [`04-recepcion-crear-turno-422.png`](../evidencia/c-18-recepcion-hernan/04-recepcion-crear-turno-422.png)
- **Rol Odontólogo (Joaquín Morán)** — [`docs/evidencia/c-18-odontologo-joaquin/README.md`](../evidencia/c-18-odontologo-joaquin/README.md):
  - Login con vista exclusiva de agenda y visualización de su propia agenda con `"Paciente #1"` (`RN-ACC-02`, `RN-ACC-03`): [`01-odontologo-agenda-propia.png`](../evidencia/c-18-odontologo-joaquin/01-odontologo-agenda-propia.png)
  - Rechazo `403` en español al consultar la agenda de otro profesional (`RN-ACC-03`, `RN-GLO-01`): [`02-odontologo-agenda-otro-403.png`](../evidencia/c-18-odontologo-joaquin/02-odontologo-agenda-otro-403.png)
- **Login y sesión transversal (Elías Tello)** — [`docs/evidencia/c-18-login-sesion-elias/README.md`](../evidencia/c-18-login-sesion-elias/README.md) y verificación de suites [`docs/evidencia/c-18-verificacion-elias/README.md`](../evidencia/c-18-verificacion-elias/README.md):
  - Login con credenciales incorrectas rechazado con `401` (`RN-GLO-01`): [`01-login-credenciales-invalidas.jpg`](../evidencia/c-18-login-sesion-elias/01-login-credenciales-invalidas.jpg)
  - Token adulterado o vencido que limpia `sessionStorage` y redirige al login con aviso en español (`RN-ACC-01`, `RN-GLO-01`): [`02-sesion-token-adulterado.jpg`](../evidencia/c-18-login-sesion-elias/02-sesion-token-adulterado.jpg)

## 3. Cómo se usaron la skill y el MCP

1. **Stitch (MCP).** Se probó la conexión con `list_projects` (respuesta vacía, sin error de autenticación), se creó el proyecto con `create_project` y se generó la pantalla de bloqueo con `generate_screen_from_text`. Al redactar `design.md`, el agente leyó esa pantalla con `get_screen` y la referenció (proyecto `6865582647500750696`, pantalla `c0d0c78ded4b46778fd80bf0604d9ee2`). Evidencia: `docs/skills-mcp/evidencias/03-stitch-mcp-invocaciones.md` y la captura `03-stitch-pantalla-generada.png`. La maquetación de C-18 (`index.html` y `styles.css`) tomó de esa pantalla la paleta y la estructura.
2. **Skill.** Tras el propose, se ejecutó `revisor-escenarios-sdd` sobre el change. Entregó una tabla de trazabilidad (escenario, regla RN-xx, verificación) y seis hallazgos con archivo y línea. Evidencia: `docs/skills-mcp/evidencias/04-revision-critica-c18-antes-despues.md`.

## 4. Revisión crítica: lo que no se aceptó tal cual

**Del diseño de Stitch.** La pantalla mostraba el aviso "se detectaron 3 turnos" antes de registrar el bloqueo, pero con C-16 la API devuelve `turnos_afectados` recién en la respuesta del `POST /bloqueos`; la interfaz muestra el aviso y la tabla después de registrar. Además, "Notificar a todos", "Exportar lista" y el menú Pacientes/Reportes/Configuración no tienen endpoint y se descartaron como fuera de alcance.

**De la skill: defecto corregido (antes / después).**

| | Antes (`29051fa`) | Después (`23414dd`) |
|---|---|---|
| Hallazgo H-01 (severidad alta) | Cinco escenarios del spec (login con credenciales inválidas, sesión vencida, agenda vacía, 422 al crear turno y 422 al crear bloqueo) no tenían tarea de verificación | La tarea 4.4 de `tasks.md` verifica cada uno, citado por su nombre exacto y con el código de error esperado |
| Cambio | — | Solo `tasks.md`: 1 línea nueva y 2 reformuladas (3 inserciones y 2 borrados en el diff) |
| Nueva pasada de la skill | Hallazgo presente | "H-01 quedó resuelto": los 15 escenarios tienen verificación (3 con pytest y 12 con la tarea 4.4) |

H-02 a H-06 (por ejemplo, faltaba un escenario del odontólogo viendo su propia agenda) se corrigieron antes de `/opsx:apply`: el spec pasó de 15 a 17 escenarios (commit `ca21a17`) y se agregaron al plan pruebas automáticas de la lógica del frontend (commit `fa4f0ae`). Esos 17 escenarios son los que se verificaron al archivar.

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
