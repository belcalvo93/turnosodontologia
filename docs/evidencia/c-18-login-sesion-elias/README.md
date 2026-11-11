# Evidencia de Verificación `C-18` — Elías Tello (login y sesión)

Prueba manual de la parte transversal de la tarea `4.4` ("Login y sesión"), sobre `main` (`0d4c82d`) después de la compilación final (`3.6`). No modifiqué código de la aplicación.

Levanté la API en local con `uvicorn app.main:app` en `http://127.0.0.1:8000/` (`APP_ENV=development`, seed demo de `C-17` y una base SQLite aparte, `demo-login.db`, que no se versiona) y probé desde el navegador.

## Tarea `4.4` — Login y sesión (transversal)

| # | Escenario verificado (`tasks.md §4.4`) | Cómo lo probé | Resultado observado | Evidencia |
|---|---|---|---|---|
| 1 | Credenciales inválidas muestran el mensaje 401 de la API (`RN-GLO-01`) | Ingresé con `admin_demo` y una contraseña incorrecta | `POST /auth/login` → `401` con `codigo` `credenciales_invalidas`. La pantalla muestra "No se pudo iniciar sesión / Usuario o contraseña incorrectos." y no se guarda nada en `sessionStorage` | [`01-login-credenciales-invalidas.jpg`](01-login-credenciales-invalidas.jpg) |
| 2 | Sesión vencida o token inválido redirige al login con mensaje en español (`RN-ACC-01`, `RN-GLO-01`) | Guardé en `sessionStorage` un token con formato JWT válido (rol `administracion`, sin vencer) pero con la firma adulterada, y recargué la página | La app intentó cargar la agenda: `GET /profesionales`, `/sillones`, `/prestaciones` y `/pacientes` → `401` con `codigo` `no_autenticado`. Volvió al login, borró la sesión de `sessionStorage` y mostró "Sesión finalizada / Se requiere un token de acceso válido." | [`02-sesion-token-adulterado.jpg`](02-sesion-token-adulterado.jpg) |

## Resultado

Los 2 escenarios de login y sesión dan ✅. La tarea `4.4` se marca en `tasks.md` cuando estén también las pruebas de los 3 roles: administración (Bruno), recepción (Hernán) y odontólogo (Joaquín).
