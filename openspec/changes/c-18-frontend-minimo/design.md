# Design — C-18 frontend-minimo

## Context

`C-01` a `C-17` implementan y verifican todos los endpoints del MVP en FastAPI. `C-18` (`D-09` en `knowledge-base/09_decisiones_y_supuestos.md`) agrega un frontend mínimo en TypeScript sin framework, servido desde la misma aplicación FastAPI, que cubre exactamente cuatro flujos: login, consulta de agenda de un profesional, creación de turno y creación de bloqueo horario con visualización de `turnos_afectados`. Ver `proposal.md` para la motivación y el alcance general.

## Goals / Non-Goals

**Goals:**
- Compilar TypeScript estricto con `tsc` puro (sin Vite ni bundlers adicionales) hacia módulos ES en `app/static/`.
- Versionar los archivos estáticos compilados (`.html`, `.css`, `.js`) en `app/static/` para que `pytest` y `uvicorn` funcionen sin requerir Node.js en tiempo de ejecución.
- Servir `index.html` en `GET /` y los assets en `/static/*` sin alterar el contrato `404` JSON (`errores-api`, `RN-GLO-01`) de las rutas de API inexistentes.
- Consumir exclusivamente los endpoints existentes en `app/api/` respetando la matriz RBAC (`03_actores_y_roles.md`) y mostrando directamente los mensajes de error en español de la API.
- Adoptar el lenguaje visual del diseño de referencia de Stitch (`projects/6865582647500750696/screens/c0d0c78ded4b46778fd80bf0604d9ee2`), descartando explícitamente los elementos de UI sin endpoint en el MVP.

**Non-Goals:**
- Modificar `app/domain/`, `app/db/` o los routers existentes en `app/api/`.
- Agregar claims al JWT o cambiar permisos de `GET /pacientes` o `GET /usuarios`.
- Ejecutar acciones de reprogramación o cancelación desde la lista de `turnos_afectados` o desde la agenda.
- Crear una carpeta `design-system/` o abrir un gate adicional de mockups (`AGENTS.md` define el proyecto como backend + extensión mínima `C-18` con diseño ya provisto en Stitch).

## Decisions

### D1 — Compilación con `tsc` puro y archivos estáticos versionados en `app/static/`

- **Elección:** Código fuente en `frontend/src/` (`app.ts`, `api.ts`, `auth.ts`, `types.ts`) compilado mediante `tsc` (`target: "ES2022"`, `module: "ES2022"`, `strict: true`, `outDir: "app/static"`) a archivos `.js` nativos cargados en `app/static/index.html` con `<script type="module" src="/static/app.js"></script>`.
- **Versionado:** Los archivos generados en `app/static/` se versionan en git. Node.js (`package.json` con `typescript` como única `devDependency`) solo se usa al desarrollar o validar tipos con `npx tsc --noEmit`.
- **Alternativas descartadas:** Vite / Webpack / esbuild (suman dependencias y configuración innecesarias para 4 pantallas sin dependencias externas).

### D2 — Montaje en FastAPI (`GET /` + `/static`) sin pisar el 404 JSON de la API

- **Elección:** En `app/main.py`:
  1. Se monta `StaticFiles` únicamente en el subprefijo `/static`:
     `aplicacion.mount("/static", StaticFiles(directory=RUTA_STATIC), name="static")`.
  2. Se define una ruta explícita `GET /` (`include_in_schema=False`) que devuelve `FileResponse(RUTA_STATIC / "index.html")`.
- **Justificación:** Si se montara `StaticFiles(..., html=True)` en `"/"`, cualquier petición a una ruta de API inexistente (por ejemplo `GET /no-existe`) sería interceptada por `StaticFiles` y devolvería un `404` en texto/HTML en lugar del JSON `{"codigo": "no_encontrado", "mensaje": "El recurso solicitado no existe."}` exigido por `openspec/specs/errores-api/spec.md` (`RN-GLO-01`). Con `/static` aislado y `GET /` puntual, todas las demás rutas caen en `_manejar_error_http` de `app/api/errores.py`.
- **Mismo origen (sin CORS):** Al servirse la UI y la API desde el mismo origen (`http://localhost:8000`), las peticiones usan rutas relativas (`fetch("/auth/login")`, `fetch("/turnos")`, etc.) y no requieren `CORSMiddleware`.

### D3 — Manejo de JWT, sesión en `sessionStorage` y visibilidad RBAC

- **Elección:**
  - Al autenticarse en `POST /auth/login`, el cliente guarda `access_token` en `sessionStorage` (permite probar distintos roles en pestañas separadas sin pisar la sesión).
  - El cliente decodifica el payload Base64URL del JWT (`{sub, rol, iat, exp}`) para leer `rol` (`"administracion" | "recepcion" | "odontologo"`).
  - La barra de navegación y las secciones muestran únicamente las vistas permitidas por `rol`:
    - `administracion`: Agenda, Crear Turno, Crear Bloqueo.
    - `recepcion`: Agenda, Crear Turno.
    - `odontologo`: Agenda.
  - Todo `fetch` protegido envía `Authorization: Bearer <token>`. Si una respuesta devuelve `401` (`no_autenticado`), la UI borra `sessionStorage`, vuelve a la vista de Login y muestra `error.mensaje`.

### D4 — Limitación documentada para el rol `odontologo` (sin cambios de backend)

- **Contexto:** El JWT emitido en `app/api/seguridad.py` contiene `sub` (`usuario.id`) y `rol`, pero no incluye `profesional_id`. Además, `GET /usuarios` es exclusivo de `administracion` y `GET /pacientes` exige `administracion` o `recepcion` (`app/api/pacientes.py`).
- **Elección (confirmada):** No se modifica ningún endpoint ni el JWT:
  1. En la vista de Agenda, el usuario con rol `odontologo` cuenta con el selector de profesionales (`GET /profesionales` está permitido a todo usuario autenticado). Si selecciona su propio profesional (en el seed demo, `odontologo_demo` está vinculado al Profesional A), ve su agenda; si selecciona a otro profesional, la API responde `403` (`sin_permiso`) y la interfaz muestra el `mensaje` en español de la API (`"Tu rol no tiene permiso para esta operación."`).
  2. Como `odontologo` no tiene permiso para `GET /pacientes`, la interfaz no invoca `GET /pacientes` cuando `rol === "odontologo"` (o ignora silenciosamente el `403`) y formatea cada turno mostrando `"Paciente #<paciente_id>"`. Para `administracion` y `recepcion`, sí cruza `paciente_id` con el catálogo de `GET /pacientes` mostrando nombre, apellido y DNI ficticio.

### D5 — Normalización de fechas locales (`NaiveDatetime`) y errores en español

- **Fechas:** Los controles `<input type="datetime-local">` devuelven `YYYY-MM-DDTHH:MM`. El cliente los normaliza a `YYYY-MM-DDTHH:MM:00` sin sufijo `Z` ni offset, cumpliendo la convención de hora local del consultorio (`D-06` y `NaiveDatetime` en `app/api/turnos.py` y `app/api/agenda.py`).
- **Errores (`RN-GLO-01`):** El cliente parsea el cuerpo JSON `{codigo, mensaje, detalles?}` de cualquier respuesta con status `>= 400` y presenta `mensaje` (y `detalles` por campo cuando existen en un `422`) directamente en un contenedor de alerta visible, sin textos en inglés ni traducciones ad-hoc en el cliente.

### D6 — Referencia de diseño en Stitch y elementos descartados por alcance

Se consultó mediante `get_screen` de Stitch el diseño de referencia:
- **Proyecto Stitch:** `6865582647500750696`
- **Pantalla:** `projects/6865582647500750696/screens/c0d0c78ded4b46778fd80bf0604d9ee2`
- **Título:** *"Panel Administrativo - Gestión de Agenda | Turnos Odontología"* (`2560x2048`, `DESKTOP`)
- **Archivos de referencia en Stitch:** captura `projects/6865582647500750696/files/22d6e0cc9f5e43c290fdad1257d92aaf` y HTML `projects/6865582647500750696/files/f6f505b7bf6742eaaec4a62d29f611c1`.

**Qué se toma del diseño de Stitch:**
- Paleta clínica limpia (tonos azul/teal odontológico, fondos claros `#f8fafc`, tarjetas blancas con bordes suaves y sombras sutiles, badges semánticos para estados `reservado` y `bloqueo`, alerta ámbar/roja para conflictos y `turnos_afectados`).
- Disposición clara de formularios con selectores de alcance (`profesional` / `sillon`), selectores de recursos, rango `inicio` / `fin`, campo `motivo` y panel de resultados para la tabla de `turnos_afectados`.

**Elementos del diseño de Stitch que se DESCARTAN por falta de endpoint o por estar fuera de alcance:**

| Elemento en Stitch (`c0d0c78ded4b46778fd80bf0604d9ee2`) | Motivo de descarte | Referencia en KB / CHANGES |
|---|---|---|
| Botón **"Notificar a todos"** en `turnos_afectados` | No existe endpoint de notificaciones; recordatorios por WhatsApp/email son Etapa Posterior | `IF-08`, `KB 06` Parte 2, `FASE 6` |
| Botón **"Exportar lista"** en `turnos_afectados` | No existe endpoint de exportación; exportación de datos es Diferenciador fuera del MVP | `IF-05`, `KB 06` Parte 2, `FASE 6` |
| Acciones **"Reprogramar"** / **"Cancelar"** dentro de la tabla de `turnos_afectados` | Decisión explícita de alcance de `C-18`: la tabla de `turnos_afectados` es solo informativa | Decisión de alcance `C-18` (punto 5) |
| Menús de navegación **"Pacientes"**, **"Reportes"** y **"Configuración"** | `C-18` solo incluye las 4 vistas de `D-09` (login, agenda de profesional, crear turno, crear bloqueo); reportes es Etapa Posterior (`SE-16`) | `D-09`, `CHANGES.md §C-18`, `SE-16` |
| Feriados generales / bloqueo de alcance **"consultorio"** | `POST /bloqueos` solo admite `alcance` `"profesional"` o `"sillon"` | `SE-24`, `C-09`, `C-16` |

## UI Mockups

Decision: no (no design-system policy configured in `.active-orchestrator-state.json`; visual reference is directly provided by Stitch screen `projects/6865582647500750696/screens/c0d0c78ded4b46778fd80bf0604d9ee2` per `D-09` and user confirmation).

## Risks / Trade-offs

| Riesgo | Mitigación |
|---|---|
| Desincronización entre `frontend/src/*.ts` y `app/static/*.js` | Tarea explícita en `tasks.md` para compilar con `tsc` y verificar con `tsc --noEmit` + test en `pytest` que comprueba que `app/static/app.js` existe y se sirve con `200` |
| Montaje de `StaticFiles` interceptando rutas de API inexistentes y rompiendo tests de `404` JSON | Montar `StaticFiles` exclusivamente en `/static` y servir `index.html` solo en `GET /`; agregar test explícito en `pytest` para `GET /ruta-inexistente` → `404` JSON `no_encontrado` |
| `odontologo` no conoce su `profesional_id` desde el JWT ni puede listar `/pacientes` | Documentado como limitación conocida (D4): selector de profesional visible con muestra del `403` en español si elige otro, y renderizado de `"Paciente #<id>"` sin llamar a `GET /pacientes` |
| Formato de fecha de `<input type="datetime-local">` sin segundos o con zona horaria | Función utilitaria en TypeScript que formatea siempre a `YYYY-MM-DDTHH:MM:00` local antes de invocar `POST /turnos`, `POST /bloqueos` o `GET /agenda/profesionales/{id}` |
