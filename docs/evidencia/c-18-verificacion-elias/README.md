# Evidencia de Verificación `C-18` — Elías Tello

Verificación asignada sobre `main` (`0d4c82d`) tras la compilación final (`3.6`). Ejecuté las pruebas automatizadas del frontend y del backend (`4.2`) y la auditoría estática de reglas duras de `AGENTS.md` (`4.3`) sin modificar código de la aplicación.

## 1. Tarea `4.2` — Ejecución de la suite completa (`npm test`, `pytest` y `openspec validate`)

> Nota: luego de correr `npm test` descarté los cambios de finales de línea en `app/static/` con `git checkout -- app/static` y `git clean -fd app/static` para no tocar los compilados versionados en `3.6`.

| # | Comando ejecutado | Resultado observado | Totales |
|---|---|---|---|
| 1 | `npm test` (`npm run build && node --test frontend/tests/logica.test.mjs`) | Compilación `tsc` sin errores y las 7 suites de lógica pura, sesión en `sessionStorage` y cliente `fetch` en verde | **15 passed, 0 failed** (7 suites) |
| 2 | `.venv/Scripts/python -m pytest -q` | Suite completa del proyecto (dominio, repositorios, API, flujo E2E, trazabilidad RN-xx y entrega de frontend estático) en verde | **789 passed, 0 failed** |
| 3 | `.venv/Scripts/python -m pytest tests/api/test_frontend_estatico.py -v` | En verde los 4 escenarios de entrega estática y preservación de errores JSON: `test_get_raiz_responde_200_html_con_los_cuatro_contenedores_de_vista` (`GET /` → `200`), `test_get_static_styles_css_responde_200_con_hoja_de_estilos` (`GET /static/styles.css` → `200`), `test_get_static_app_js_responde_200_con_javascript_compilado` (`GET /static/app.js` → `200`) y `test_get_ruta_inexistente_conserva_404_json_en_espanol` (`GET /ruta-que-no-existe` → `404` JSON `no_encontrado`, `RN-GLO-01`) | **4 passed, 0 failed** |
| 4 | `openspec validate --all --strict` | Validación estricta de los 17 specs canónicos y del change `c-18-frontend-minimo` sin errores | **18 passed, 0 failed** (18 items) |

## 2. Tarea `4.3` — Validación de reglas duras de `AGENTS.md`

| # | Regla verificada | Comando ejecutado | Detalle observado | Resultado |
|---|---|---|---|---|
| 1 | **Regla 1:** `app/domain/` no importa `fastapi`, `sqlite3`, `app.db` ni `app.api` | `git grep -n -E "(fastapi\|sqlite3\|app\.db\|app\.api)" -- app/domain/` | Sin coincidencias (código de salida `1`). El dominio se mantiene 100 % en Python puro (además validado por `tests/domain/test_estructura.py`). | ✅ |
| 2 | **Regla 2 (`RN-TUR-09`):** `app/domain/` no llama `datetime.now()`, `date.today()` ni `utcnow()` | `git grep -n -E "(datetime\.now\|date\.today\|utcnow)" -- app/domain/` | Sin coincidencias (código de salida `1`). El reloj se recibe siempre por parámetro (`ahora`). | ✅ |
| 3 | **Regla 4:** Sin SQL armado con f-strings, `%` ni concatenación de entradas en `app/db/` | `git grep -n -E "\.format\(\| % \| \+ " -- app/db/` y `git grep -n -E "\{.*\}" -- app/db/*.py` y `git grep -n "execute(" -- app/db/` | Solo aparece `hasta = desde + timedelta(days=1)` en `repositorio_turnos.py:233` (suma de fechas) y `SELECT {COLUMNAS_TURNO}` en `repositorio_agenda.py:16,33` (constante `Final` de nombres de columna fija al importar el módulo). Las 54 llamadas a `conexion.execute(...)` usan consultas parametrizadas con `?`. | ✅ |
| 4 | **Regla 6 (`RN-AUD-02`):** Sin `UPDATE` ni `DELETE` sobre `auditoria_turno` (append-only) | `git grep -n -i -E "(UPDATE\|DELETE).*auditoria_turno" -- app/` | Solo aparecen los dos triggers defensivos del esquema (`BEFORE UPDATE ON auditoria_turno` y `BEFORE DELETE ON auditoria_turno` con `RAISE(ABORT, ...)` en `app/db/esquema.sql:122,128`). Ningún repositorio ejecuta `UPDATE` ni `DELETE` sobre `auditoria_turno`. | ✅ |
| 5 | **Regla 10 (`RN-PAC-03`):** Todos los DNI del seed (`app/db/seed.py`) terminan en `"(ficticio)"` | `git grep -n "dni" -- app/db/seed.py` | Los dos pacientes del seed demo declaran `dni="00000001 (ficticio)"` (`app/db/seed.py:215`) y `dni="00000002 (ficticio)"` (`app/db/seed.py:222`). | ✅ |
| 6 | **Regla 9 (`RN-ACC-04`):** Sin `.env` versionado ni secretos/contraseñas en texto plano en `app/` o `frontend/` | `git ls-files .env .env.*` y `git grep -n -i -E "(JWT_SECRET\|PASSWORD\|TOKEN).*=" -- app/ frontend/src/` | `git ls-files` devuelve únicamente `.env.example` (`.env` está ignorado). `JWT_SECRET` y `SEED_*_PASSWORD` se leen de variables de entorno en `app/config.py`, las contraseñas se almacenan con hash (`hashear`), y en `frontend/src/` no hay credenciales ni tokens escritos en el código. | ✅ |
| 7 | **Frontend (`D3`, `RN-PAC-03`):** El frontend no usa `localStorage` para el token (usa `sessionStorage`) ni persiste datos de pacientes fuera de la API | `git grep -n "localStorage" -- frontend/ app/static/` y `git grep -n "setItem" -- frontend/src/` | `localStorage` no tiene apariciones (código de salida `1`). `setItem` solo se invoca en `frontend/src/auth.ts:52,54` sobre `sessionStorage` para `access_token` y `username`; los pacientes se obtienen en memoria desde `GET /pacientes` cuando el rol lo permite. | ✅ |
