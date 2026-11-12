# Verify — C-18 frontend-minimo

Verificación de cierre de `C-18` que hice sobre `main` (`1b22440`). — Elías Tello

## Resultado de la suite completa

### 1. Verificación de tipos TypeScript (`tsc`)

```
npx tsc --noEmit
(sin salida, código de retorno 0)
```

### 2. Suite de lógica del frontend (`node --test`)

```
npm test
ℹ tests 15
ℹ suites 7
ℹ pass 15
ℹ fail 0
```

- **15 tests en 7 suites** (`frontend/tests/logica.test.mjs`) en verde: `normalizarFechaLocal` (2), `filtrarActivos` (2), `formatearPacienteId` (2), `interpretarErrorApi` (3), `decodificarPayloadJwt` (2), `auth en sessionStorage y RBAC` (1) y `cliente fetch API` (3).
- Tras la ejecución se descartaron los cambios de finales de línea en `app/static/` con `git checkout -- app/static` y `git clean -fd app/static`.

### 3. Suite completa de Python (`pytest`)

```
.venv\Scripts\python.exe -m pytest -q
789 passed, 1 warning
```

- Línea de base de `main` al iniciar `C-18` (tras `C-17`): **785 tests** (`785 passed, 1 warning`).
- Tests nuevos de `C-18` en `pytest`: **4**
  - `tests/api/test_frontend_estatico.py`: **4** (`GET /` → `200` `text/html` con los 4 contenedores literales y excluido del esquema OpenAPI; `GET /static/styles.css` → `200`; `GET /static/app.js` → `200`; `GET /ruta-que-no-existe` → `404` JSON `no_encontrado`, `RN-GLO-01`).
- Total esperado y obtenido en `pytest`: **785 + 4 = 789** (más los **15** tests de `node --test` en `frontend/tests/logica.test.mjs`).
- `tests/api/test_errores.py` (20 tests preexistentes) sigue en verde **sin modificaciones**.
- El único warning es el `StarletteDeprecationWarning` de `fastapi.testclient` (`httpx` → `httpx2`), preexistente.

## Validación OpenSpec

```
openspec validate --all --strict
Totals: 18 passed, 0 failed (18 items)
```

## Trazabilidad escenario → test o evidencia (5 requirements y 17 escenarios de `frontend-minimo`)

| # | Capability | Requirement | Escenario | Test / Evidencia |
|---|---|---|---|---|
| 1 | `frontend-minimo` | 1. Entrega de documentos y recursos estáticos sin alterar el 404 JSON | Carga inicial de la interfaz web en la raíz | `tests/api/test_frontend_estatico.py::test_get_raiz_responde_200_html_con_los_cuatro_contenedores_de_vista` |
| 2 | `frontend-minimo` | 1. Entrega de documentos y recursos estáticos sin alterar el 404 JSON | Carga de los recursos estáticos compilados bajo /static | `tests/api/test_frontend_estatico.py::test_get_static_styles_css_responde_200_con_hoja_de_estilos` + `tests/api/test_frontend_estatico.py::test_get_static_app_js_responde_200_con_javascript_compilado` |
| 3 | `frontend-minimo` | 1. Entrega de documentos y recursos estáticos sin alterar el 404 JSON | Una ruta de API inexistente conserva el 404 JSON en español (RN-GLO-01) | `tests/api/test_frontend_estatico.py::test_get_ruta_inexistente_conserva_404_json_en_espanol` |
| 4 | `frontend-minimo` | 2. Inicio de sesión y visibilidad por rol en la interfaz | Inicio de sesión válido adapta las vistas según el rol (RN-ACC-01, RN-ACC-02) | `frontend/tests/logica.test.mjs` (`auth en sessionStorage y RBAC` + `decodificarPayloadJwt`) + `docs/evidencia/c-18-recepcion-hernan/README.md` §2 fila 1 + `docs/evidencia/c-18-administracion-bruno/README.md` §1 fila 1 + `docs/evidencia/c-18-odontologo-joaquin/README.md` §1 fila 1 |
| 5 | `frontend-minimo` | 2. Inicio de sesión y visibilidad por rol en la interfaz | Credenciales inválidas muestran el mensaje 401 de la API (RN-GLO-01) | `frontend/tests/logica.test.mjs` (`cliente fetch API`: `"propaga 401 credenciales_invalidas en login sin invocar el manejador de sesión vencida"`) + `docs/evidencia/c-18-login-sesion-elias/README.md` fila 1 (`01-login-credenciales-invalidas.jpg`) |
| 6 | `frontend-minimo` | 2. Inicio de sesión y visibilidad por rol en la interfaz | Sesión vencida o token inválido redirige al login con mensaje en español (RN-ACC-01, RN-GLO-01) | `frontend/tests/logica.test.mjs` (`cliente fetch API`: `"limpia sessionStorage e invoca el manejador ante 401 no_autenticado"`) + `docs/evidencia/c-18-login-sesion-elias/README.md` fila 2 (`02-sesion-token-adulterado.jpg`) |
| 7 | `frontend-minimo` | 3. Consulta de agenda de un profesional | Consulta de agenda muestra turnos activos y bloqueos ordenados con datos ficticios (RN-PAC-03) | `docs/evidencia/c-18-recepcion-hernan/README.md` §2 fila 2 (`01-recepcion-agenda-con-paciente.png`) |
| 8 | `frontend-minimo` | 3. Consulta de agenda de un profesional | Odontólogo ve su propia agenda con "Paciente #<id>" sin error (RN-ACC-03) | `frontend/tests/logica.test.mjs` (`formatearPacienteId`) + `docs/evidencia/c-18-odontologo-joaquin/README.md` §1 fila 2 (`01-odontologo-agenda-propia.png`) |
| 9 | `frontend-minimo` | 3. Consulta de agenda de un profesional | Odontólogo que consulta la agenda de otro profesional ve el error 403 en español (RN-ACC-03, RN-GLO-01) | `frontend/tests/logica.test.mjs` (`interpretarErrorApi`) + `docs/evidencia/c-18-odontologo-joaquin/README.md` §1 fila 3 (`02-odontologo-agenda-otro-403.png`) |
| 10 | `frontend-minimo` | 3. Consulta de agenda de un profesional | Agenda sin turnos ni bloqueos en el rango seleccionado (caso de borde) | `docs/evidencia/c-18-recepcion-hernan/README.md` §2 fila 3 (`02-recepcion-agenda-vacia.png`) |
| 11 | `frontend-minimo` | 4. Creación de turno desde la interfaz | Alta exitosa de turno muestra confirmación con el horario calculado (RN-TUR-01, RN-TUR-02, RN-TUR-14) | `frontend/tests/logica.test.mjs` (`normalizarFechaLocal`) + `docs/evidencia/c-18-administracion-bruno/README.md` §1 fila 2 (`02-administracion-crear-turno-201.jpg`) |
| 12 | `frontend-minimo` | 4. Creación de turno desde la interfaz | Rechazo por solapamiento o fuera de horario muestra el error 409 en español (RN-TUR-03, RN-TUR-05, RN-GLO-01) | `frontend/tests/logica.test.mjs` (`interpretarErrorApi`) + `docs/evidencia/c-18-recepcion-hernan/README.md` §2 fila 5 (`03-recepcion-crear-turno-409.png`) |
| 13 | `frontend-minimo` | 4. Creación de turno desde la interfaz | Envío con datos inválidos muestra el error 422 en español (RN-GLO-01) | `frontend/tests/logica.test.mjs` (`interpretarErrorApi`: `"extrae la lista de detalles por campo cuando un error 422 los incluye"`) + `docs/evidencia/c-18-recepcion-hernan/README.md` §2 fila 6 (`04-recepcion-crear-turno-422.png`) |
| 14 | `frontend-minimo` | 4. Creación de turno desde la interfaz | Recurso inactivo no se ofrece en los selectores de crear turno (RN-REC-03) | `frontend/tests/logica.test.mjs` (`filtrarActivos`) + `docs/evidencia/c-18-recepcion-hernan/README.md` §2 fila 4 |
| 15 | `frontend-minimo` | 5. Creación de bloqueo horario con visualización de turnos afectados | Crear bloqueo con turnos reservados superpuestos muestra la tabla de turnos_afectados (RN-TUR-05, RN-TUR-08) | `docs/evidencia/c-18-administracion-bruno/README.md` §1 fila 3 (`03-administracion-bloqueo-turnos-afectados.jpg`) |
| 16 | `frontend-minimo` | 5. Creación de bloqueo horario con visualización de turnos afectados | Intervalo de bloqueo inválido muestra el error 422 en español (RN-REC-02, RN-GLO-01) | `frontend/tests/logica.test.mjs` (`interpretarErrorApi`) + `docs/evidencia/c-18-administracion-bruno/README.md` §1 fila 5 (`05-administracion-bloqueo-422.jpg`) |
| 17 | `frontend-minimo` | 5. Creación de bloqueo horario con visualización de turnos afectados | Crear bloqueo sin turnos superpuestos muestra aviso de lista vacía (caso de borde) | `docs/evidencia/c-18-administracion-bruno/README.md` §1 fila 4 (`04-administracion-bloqueo-sin-turnos-afectados.jpg`) |

## Confirmación de archivos protegidos

Verificado con `git diff --stat`:

```
git diff --stat -- README.md AGENTS.md CLAUDE.md knowledge-base/ CHANGES.md docs/discovery/ .active-orchestrator-state.json
(sin salida)
```

Ninguno de los archivos protegidos (`knowledge-base/`, `CHANGES.md`, `docs/discovery/` ni `.active-orchestrator-state.json`, además de `README.md`, `AGENTS.md` y `CLAUDE.md`) fue modificado.
