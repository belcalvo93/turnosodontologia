# Proposal — C-18 frontend-minimo

## Why

El MVP de la API (`C-01` a `C-17`) está completo y verificado, pero solo es operable mediante clientes HTTP o tests automatizados. De acuerdo con la decisión `D-09` (`knowledge-base/09_decisiones_y_supuestos.md`), necesitamos una interfaz web mínima en TypeScript sin framework, compilada a archivos estáticos y servida por el mismo proceso FastAPI, que permita demostrar visualmente los flujos principales del consultorio (login por rol, consulta de agenda de un profesional, alta de turno y alta de bloqueo con reporte de `turnos_afectados`) tomando el estilo de referencia generado con Stitch (`projects/6865582647500750696/screens/c0d0c78ded4b46778fd80bf0604d9ee2`).

## What Changes

- **Frontend en TypeScript puro (`tsc`, sin Vite ni bundlers):** código fuente en `frontend/src/` con `tsconfig.json` y `package.json` en la raíz (Node.js solo en desarrollo para compilar y verificar tipos con `tsc --noEmit`).
- **Archivos estáticos versionados en `app/static/`:** `index.html`, `styles.css` y el JavaScript compilado por `tsc` se versionan en `app/static/` para que levantar la API con `uvicorn` y ejecutar `pytest` no requieran Node.js instalado.
- **Montaje en FastAPI (`app/main.py`):**
  - Se monta `StaticFiles` bajo `/static` (`aplicacion.mount("/static", StaticFiles(directory=...), name="static")`).
  - Se expone `GET /` devolviendo `FileResponse` con `app/static/index.html`.
  - Se preserva intacto el manejador global de errores JSON en español (`errores-api`, `RN-GLO-01`): cualquier ruta inexistente fuera de `/static` sigue respondiendo `404` JSON `{"codigo": "no_encontrado", "mensaje": "El recurso solicitado no existe."}`.
- **Cuatro pantallas / vistas en una SPA liviana (`index.html` + `app/static/*.js`):**
  1. **Login (`POST /auth/login`):** ingreso de `username` y `password`, almacenamiento del JWT en `sessionStorage`, decodificación del payload (`sub`, `rol`, `exp`) y adaptación de la interfaz según el rol (`RN-ACC-01`, `RN-ACC-02`).
  2. **Agenda de un profesional (`GET /agenda/profesionales/{id}?desde=&hasta=`):** selector de profesional y rango de fechas, listado cronológico de turnos activos y bloqueos (`US-009`), enriqueciendo nombres con `GET /profesionales`, `GET /sillones`, `GET /prestaciones` y `GET /pacientes` (cuando el rol tiene permiso).
  3. **Crear turno (`POST /turnos`):** formulario visible para `administracion` y `recepcion` (`US-006`) con selectores de recursos activos (`GET /pacientes`, `GET /profesionales`, `GET /sillones`, `GET /prestaciones`) e `inicio` en hora local (`NaiveDatetime`), mostrando errores de negocio en español (`409 conflicto_agenda`, `fuera_de_horario`, `dentro_de_bloqueo`, `422 dato_invalido`).
  4. **Crear bloqueo con `turnos_afectados` (`POST /bloqueos`):** formulario visible solo para `administracion` (`US-005`, `C-16`) que envía `alcance`, `recurso_id`, `inicio`, `fin` y `motivo`, y al recibir `201` renderiza la tabla de `turnos_afectados` devuelta por la API.

**Fuera de alcance:**
- Modificar cualquier endpoint, modelo, regla de dominio o repositorio de `C-01` a `C-17`.
- Agregar claims al JWT o cambiar permisos de `GET /pacientes` / `GET /usuarios` para el rol `odontologo` (se documenta como limitación conocida: `odontologo` elige en el selector de profesionales, ve el `403` en español de la API si consulta a otro colega, y visualiza a los pacientes como `"Paciente #<id>"`).
- Reprogramar (`POST /turnos/{id}/reprogramar`) o cancelar (`POST /turnos/{id}/cancelar`) turnos desde la tabla de `turnos_afectados` o desde la agenda.
- Elementos del diseño de Stitch (`projects/6865582647500750696/screens/c0d0c78ded4b46778fd80bf0604d9ee2`) sin endpoint de respaldo o fuera del alcance de `C-18`: botones `"Notificar a todos"`, `"Exportar lista"`, acciones `"Reprogramar"` / `"Cancelar"` en la tabla de conflictos, selector de feriados globales de consultorio (`SE-24`) y menús de `Pacientes`, `Reportes` y `Configuración`.

## Capabilities

### New Capabilities
- `frontend-minimo`: entrega de la interfaz web estática desde FastAPI (`GET /` y `/static/*`) sin alterar el contrato `404` JSON de la API, e interacción por rol con los endpoints existentes de login, agenda de profesional, alta de turno y alta de bloqueo con visualización de `turnos_afectados`.

### Modified Capabilities

Ninguna. Los contratos de `acceso-usuarios`, `agenda`, `turnos`, `bloqueos` y `errores-api` no cambian.

## Impact

- **Archivos nuevos:**
  - `app/static/index.html`, `app/static/styles.css` y módulos JS compilados en `app/static/`
  - `frontend/src/*.ts` (código fuente TypeScript), `tsconfig.json`, `package.json`
  - `tests/api/test_frontend_estatico.py` (tests de `GET /`, `/static/*` y preservación del `404` JSON en rutas inexistentes)
- **Archivos modificados:**
  - `app/main.py`: ruta `GET /` para `index.html` y montaje de `/static` con `StaticFiles`.
- **Sin cambios:** `app/domain/*`, `app/db/*`, `app/api/*` (routers y manejadores de errores), `knowledge-base/`, `CHANGES.md`.
- **Governance:** MEDIO.
- **Dependencias:** `C-03`, `C-11`, `C-14`, `C-16` y `C-17` (todos completados y archivados).
