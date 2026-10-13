# Arquitectura Propuesta

Arquitectura deliberadamente simple. Stack provisional (D-01): Python + FastAPI + pytest + SQLite. No hay puertos/adaptadores, ni capa de casos de uso separada, ni frameworks de inyección de dependencias. La única separación que importa: **el dominio no conoce el framework ni la base de datos**.

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|--------|--------------|---------|
| Dominio separado del framework | `app/domain/` | Las reglas de solapamiento se testean sin DB ni HTTP |
| Funciones puras con datos explícitos | `app/domain/` | El dominio recibe listas de turnos, horarios y bloqueos ya cargados y devuelve el resultado o un error; no consulta nada |
| Reloj inyectado | `app/domain/` y `app/api/` | Las reglas de "turno futuro" (RN-TUR-09) se testean sin depender de la hora real |
| Routers finos | `app/api/` | Traducen HTTP a dominio y a persistencia |
| Transacción única por operación de turno | `app/db/` | Validar y escribir turno + auditoría juntos (RN-AUD-03, SE-06) |
| Auditoría append-only | `app/db/` | Trazabilidad (RN-AUD-02) |

## Estructura de directorios

```
turnosodontologia/
├── app/
│   ├── main.py                 # crea la app FastAPI y monta los routers
│   ├── config.py               # lee variables de entorno
│   ├── domain/                 # Python puro: sin FastAPI, sin DB
│   │   ├── models.py           # Turno, Prestacion, HorarioAtencion, Bloqueo (dataclasses)
│   │   ├── intervalos.py       # solapan(a, b) con intervalos [inicio, fin)
│   │   ├── reglas_turno.py     # validar_alta / validar_reprogramacion / validar_cancelacion
│   │   └── errores.py          # errores de dominio (ConflictoAgenda, FueraDeHorario, ...)
│   ├── api/                    # routers FastAPI
│   │   ├── auth.py             # login + dependencia de usuario actual / rol
│   │   ├── recursos.py         # profesionales, sillones, prestaciones, horarios, bloqueos
│   │   ├── pacientes.py
│   │   ├── turnos.py           # crear / cancelar / reprogramar
│   │   ├── agenda.py
│   │   └── auditoria.py
│   └── db/                     # persistencia SQLite
│       ├── conexion.py         # conexión y transacciones
│       ├── esquema.sql         # tablas e índices
│       ├── repositorio.py      # funciones de lectura/escritura
│       └── seed.py             # datos ficticios de desarrollo
├── tests/
│   ├── domain/                 # unitarios, sin DB ni HTTP
│   ├── api/                    # con TestClient y SQLite temporal
│   └── conftest.py
├── knowledge-base/
├── docs/
├── .env.example                # solo placeholders
└── pyproject.toml / requirements.txt
```

Regla de dependencia: `api` -> `domain` y `db`; `db` -> `domain` (solo tipos); `domain` -> nada del proyecto fuera de sí.

## Cómo se usa el dominio (idea, sin ceremonia)

```
router (api/turnos.py)
  1. valida permisos y esquema de entrada
  2. abre transacción en db
  3. carga contexto (prestación, horarios, bloqueos, turnos cercanos)
  4. llama a domain.reglas_turno.validar_alta(...)  -> lanza error de dominio o devuelve el turno armado
  5. guarda turno + auditoría y confirma
  6. traduce errores de dominio a 409/422
```

## Testing (pytest)

- `tests/domain/`: casos de borde de intervalos (contiguos, solapamiento parcial, contención), horarios, bloqueos, turno futuro con reloj fijo. Sin DB ni HTTP.
- `tests/api/`: roles (401/403), flujos de crear/cancelar/reprogramar, auditoría, concurrencia básica. SQLite en memoria o archivo temporal.
- Cada regla RN-xx de [05](05_reglas_de_negocio.md) mapea a al menos un test.
- Todos los datos de test son ficticios.

## Seguridad

- Autenticación: token firmado emitido en `/auth/login` (JWT es el candidato; decisión pendiente D-03).
- Autorización: dependencia de FastAPI por ruta contra la matriz de [03](03_actores_y_roles.md).
- Validación de input: modelos Pydantic en la frontera de la API; las reglas de negocio las valida el dominio.
- Secrets management: solo variables de entorno; `.env` fuera del repositorio; `.env.example` con placeholders. Contraseñas con hash (algoritmo estándar con sal, ej. bcrypt/argon2, SE).
- SQL: consultas parametrizadas, nunca concatenación de strings.
- Auditoría append-only (RN-AUD-02).
- Datos de pacientes: en el MVP son ficticios; si se pasa a datos reales aplican Ley 25.326 y la normativa de salud (ver IF-07 en 10).

## Variables de entorno

Solo placeholders; no se versionan valores reales.

| Variable | Descripción | Ejemplo | Sensible |
|----------|-------------|---------|----------|
| `APP_ENV` | Entorno de ejecución | `development` | N |
| `DATABASE_URL` | Ruta de la base SQLite | `sqlite:///./turnos.db` | N |
| `JWT_SECRET` | Clave de firma de tokens (si se usa JWT) | `<cambiar-por-un-valor-largo-y-aleatorio>` | Y |
| `JWT_ALGORITHM` | Algoritmo de firma | `HS256` | N |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del token | `60` | N |
| `CLINIC_TIMEZONE` | Zona horaria del consultorio | `America/Argentina/Buenos_Aires` | N |
| `SEED_ADMIN_PASSWORD` | Contraseña inicial del usuario demo (solo desarrollo) | `<definir-localmente>` | Y |
