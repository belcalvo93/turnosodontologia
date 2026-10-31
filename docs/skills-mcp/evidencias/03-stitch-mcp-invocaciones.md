# Evidencia 03 — Invocaciones reales del MCP de Stitch

Fecha: 2026-10-30. Cliente: Antigravity (IDE de Google). Servidor: Stitch MCP remoto (`https://stitch.googleapis.com/mcp`).
Autenticación: OAuth con `gcloud` (token de ~1 hora + cabecera `X-Goog-User-Project`). No se versiona ninguna credencial.

## Invocaciones registradas

| # | Herramienta MCP | Para qué se usó | Resultado |
|---|-----------------|-----------------|-----------|
| 1 | `stitch/list_projects` | Verificar conexión y autenticación | Respuesta `{}` (cuenta sin proyectos todavía): conexión OK |
| 2 | `stitch/create_project` | Crear el proyecto "Turnos Odontología - Frontend mínimo" | Proyecto `6865582647500750696` |
| 3 | `stitch/generate_screen_from_text` | Generar la pantalla de bloqueo de agenda + tabla "Turnos afectados" (C-16/C-18) | Pantalla `c0d0c78ded4b46778fd80bf0604d9ee2`, sistema de diseño "Clinical Precision" |
| 4 | `stitch/get_screen` | Leer la pantalla generada al redactar `design.md` del change C-18 | Referencia incluida en `openspec/changes/c-18-frontend-minimo/design.md` |

Capturas que acompañan esta evidencia: respuesta de `list_projects`; invocaciones 2 y 3 en Antigravity; la pantalla dentro de Stitch.

## Revisión crítica del resultado (no se aceptó el diseño tal cual)

El diseño generado se contrastó contra lo que la API realmente ofrece:

- El aviso "Se detectaron 3 turnos…" aparecía **antes** de registrar el bloqueo. Con C-16, `turnos_afectados` se devuelve recién en la respuesta del `POST /bloqueos`: no hay vista previa. En la implementación el aviso y la tabla se muestran después de registrar.
- Elementos sin endpoint (se descartan, fuera de alcance de C-18): "Notificar a todos", "Exportar lista" y el menú Pacientes / Reportes / Configuración.

## Problemas reales resueltos durante la conexión

1. **La clave de API no alcanzó.** `tools/list` respondía 200, pero `list_projects` devolvía 401: *"API keys are not supported by this API. Expected OAuth2 access token…"*. Se pasó a OAuth (`gcloud auth login`, `gcloud auth application-default login`, `gcloud services enable stitch.googleapis.com`).
2. **Cambio de comando en gcloud.** `gcloud beta services mcp enable` ya no existe (`Invalid choice: 'mcp'`); se usó `gcloud services enable stitch.googleapis.com`.
3. **Stitch no figura en el Marketplace de Antigravity**: se agregó a mano en la configuración global de MCP de Antigravity, fuera del repositorio.
4. **Una sola forma de autenticación por request.** Con clave y token juntos Stitch rechaza (*"Expected only one form of authentication"*); por eso, al pasar a OAuth se quitó la cabecera `X-Goog-Api-Key`.
5. El token vence a la hora: hay que regenerarlo y actualizar la configuración cuando Stitch responde `Unauthorized`.
