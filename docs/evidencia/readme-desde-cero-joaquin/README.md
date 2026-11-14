# Prueba del README desde cero — Joaquín Moran

Se siguió el `README.md` de `main` (`079dd1f`, con `C-18` ya archivado) al pie de la letra, en una carpeta nueva y vacía (`C:\Users\moran\prueba-readme`), en Windows con **PowerShell 5.1** y Python 3.13.7. Se usó PowerShell porque es la consola que el README indica para Windows.

| # | Paso del README | Comando | Resultado esperado | Resultado obtenido | Log |
|---|---|---|---|---|---|
| 1 | Instalación: clonar | `git clone https://github.com/belcalvo93/turnosodontologia.git` | El repo se clona sin pedir sesión | Clonado completo (2869 objetos), sin pedir sesión: el repo es público | [`01-clonar-e-instalar.txt`](01-clonar-e-instalar.txt) |
| 2 | Instalación: entorno virtual | `python -m venv .venv` y `.venv\Scripts\Activate.ps1` | El prompt muestra `(.venv)` | Activó sin el error de "ejecución de scripts deshabilitada", así que no hizo falta el `Set-ExecutionPolicy` que contempla el README | [`01-clonar-e-instalar.txt`](01-clonar-e-instalar.txt) |
| 3 | Instalación: dependencias | `pip install -r requirements.txt` | Se instalan sin errores | `Successfully installed` con todas las dependencias, incluidas `tzdata` y `pwdlib[argon2]` | [`01-clonar-e-instalar.txt`](01-clonar-e-instalar.txt) |
| 4 | Correr los tests | `pytest tests` | `789 passed` | `789 passed, 1 warning`. El warning es un aviso de deprecación de `httpx` en el `TestClient` de Starlette y no afecta | [`02-tests-y-configuracion.txt`](02-tests-y-configuracion.txt) |
| 5 | Variables de entorno | Bloque `# Windows (PowerShell)` de *Variables de entorno* | Las variables se cargan en la sesión | Se cargaron las 9 variables sin errores | [`02-tests-y-configuracion.txt`](02-tests-y-configuracion.txt) |
| 6 | Verificar la configuración | `python -c "from app.config import cargar_config; print(cargar_config().database_path)"` | `turnos.db` | `turnos.db` | [`02-tests-y-configuracion.txt`](02-tests-y-configuracion.txt) |
| 7 | Levantar la API | `uvicorn app.main:app` | `Uvicorn running on http://127.0.0.1:8000` | La API levantó con el seed demo | Verificado a mano |
| 8 | Salud | `http://127.0.0.1:8000/health` en el navegador | `{"status":"ok"}` | `{"status":"ok"}` | Verificado a mano |
| 9 | Frontend web (`C-18`) | `http://127.0.0.1:8000/` con los tres usuarios demo | Cada rol ve solo sus pantallas | `admin_demo`: Agenda, Crear turno y Crear bloqueo. `recepcion_demo`: Agenda y Crear turno. `odontologo_demo`: solo Agenda. No hizo falta Node.js | Verificado a mano |

**Resultado:** el README se puede seguir desde cero en Windows sin pasos extra ni correcciones.
