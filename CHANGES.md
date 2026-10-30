# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **turnosodontologia** (API de turnos para consultorios odontológicos).
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**
>
> Fuente: `knowledge-base/` y `docs/discovery/informe-discovery.md` (sección D.3). El MVP cubre **solo** los 9 ítems de D.3 "Imprescindible". Lo de "Diferenciador" y "Etapas posteriores" está en la FASE 6, separada y sin código C-NN.
>
> **Este documento no elige el change a implementar.** Esa decisión corresponde a la etapa 6 y la toma otro integrante del equipo.

---

## Cómo usar este documento

1. Identificar el change a implementar (verificar que sus dependencias están en `openspec/changes/archive/`).
2. Leer los docs de la knowledge-base indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Al terminar el change, archivarlo con `/opsx:archive <nombre-del-change>`.
5. Marcar el checkbox `[x]` en este archivo.

---

## Árbol de dependencias

```
C-01 foundation-setup
  │
  ├── C-02 dominio-base                          ← Python puro, sin DB ni HTTP
  │     └── C-10 reglas-alta-turno               ← paralelo con toda la FASE 2
  │
  └── C-03 auth-login-roles                      ← desbloquea todos los recursos protegidos
        │
        ├── C-04 profesionales
        │     ├── C-07 gestion-usuarios
        │     ├── C-08 horarios-atencion         ← + C-02
        │     └── C-09 bloqueos                  ← + C-02 + C-05
        │
        ├── C-05 sillones-prestaciones
        │
        └── C-06 pacientes
                                                 
C-06 + C-08 + C-09 + C-10
  └── C-11 crear-turno                           ← CUELLO DE BOTELLA (turno + auditoría)
        ├── C-12 cancelar-turno
        ├── C-13 reprogramar-turno
        ├── C-14 agenda
        └── C-16 bloqueos-turnos-afectados       ← requiere decidir SE-09 antes

C-12 + C-13
  └── C-15 consulta-auditoria

C-07 + C-14 + C-15 + C-16
  └── C-17 seed-y-flujo-e2e                      ← cierre del MVP
```

### Paralelismo por fase

> Cada "gate" es un punto de sincronización. Los changes dentro de un grupo pueden ejecutarse en paralelo.

```
GATE 0: ninguna
  → C-01 foundation-setup                [Agente A]

GATE 1: C-01 ✓
  → C-02 dominio-base                    [Agente A]
  → C-03 auth-login-roles                [Agente B]

GATE 2: C-02 ✓
  → C-10 reglas-alta-turno               [Agente A]

GATE 3: C-03 ✓                           ← FORK (3 paralelos)
  → C-04 profesionales                   [Agente B]
  → C-05 sillones-prestaciones           [Agente C]
  → C-06 pacientes                       [Agente C — después de C-05]

GATE 4: C-04 ✓                           ← FORK (3 paralelos)
  → C-07 gestion-usuarios                [Agente C]
  → C-08 horarios-atencion               [Agente A — si C-02 ✓]
  → C-09 bloqueos                        [Agente B — si C-02 ✓ y C-05 ✓]

GATE 5: C-06 ✓ + C-08 ✓ + C-09 ✓ + C-10 ✓
  → C-11 crear-turno                     [Agente A]  (solo: todo el MVP pasa por acá)

GATE 6: C-11 ✓                           ← FORK (4 paralelos)
  → C-12 cancelar-turno                  [Agente A]
  → C-13 reprogramar-turno               [Agente B]
  → C-14 agenda                          [Agente C]
  → C-16 bloqueos-turnos-afectados       [Agente B — después de C-13, si SE-09 decidida]

GATE 7: C-12 ✓ + C-13 ✓
  → C-15 consulta-auditoria              [Agente A]

GATE 8: C-07 ✓ + C-14 ✓ + C-15 ✓ + C-16 ✓
  → C-17 seed-y-flujo-e2e                [Agente A]
```

### Camino crítico (8 changes — mínimo irreducible)

```
C-01 → C-03 → C-04 → C-09 → C-11 → C-12* → C-15 → C-17
```

\* `C-12` y `C-13` tienen el mismo largo: cualquiera de los dos, si se demora, retrasa `C-15`.

La rama del dominio (`C-02 → C-10`) es más corta y no está en el camino crítico, pero `C-10` concentra la lógica más delicada del sistema: si se atrasa, frena `C-11` igual.

### Plan óptimo con 3 agentes

El MVP es solo backend (el frontend React es etapa posterior, D.3), así que no hay agente de frontend. Los agentes se reparten por dominio.

| Paso | Agente A (Dominio y turnos) | Agente B (Recursos y disponibilidad) | Agente C (Acceso y consultas) |
|------|-----------------------------|--------------------------------------|-------------------------------|
| 1 | C-01 foundation-setup | — | — |
| 2 | C-02 dominio-base | C-03 auth-login-roles | — |
| 3 | C-10 reglas-alta-turno | C-04 profesionales | C-05 sillones-prestaciones |
| 4 | C-08 horarios-atencion | C-09 bloqueos | C-06 pacientes |
| 5 | C-11 crear-turno | — | C-07 gestion-usuarios |
| 6 | C-12 cancelar-turno | C-13 reprogramar-turno | C-14 agenda |
| 7 | C-15 consulta-auditoria | C-16 bloqueos-turnos-afectados | — |
| 8 | C-17 seed-y-flujo-e2e | — | — |

### Riesgos del roadmap

| Riesgo | Origen en la KB | Changes afectados | Mitigación propuesta |
|--------|-----------------|-------------------|----------------------|
| `C-11` es cuello de botella: depende de 4 changes y bloquea 5 | Estructura del grafo | C-11 a C-17 | Mantener `C-11` chico: solo crear y consultar por id; cancelar y reprogramar van aparte |
| Comportamiento de turnos existentes al crear un bloqueo sin decidir | SE-09 (alta) | C-16 | No ejecutar `/opsx:propose` de `C-16` hasta que equipo/cátedra decida SE-09; `C-09` no depende de esa decisión |
| Concurrencia en reservas simultáneas | SE-06 (alta) | C-11, C-13 | Validar e insertar en una única transacción de escritura; test de API de doble reserva |
| Intervalos semiabiertos y "todo turno usa sillón" son supuestos | SE-10, SE-02 (alta) | C-02, C-10, C-11 | Están escritos como reglas (RN-TUR-04, RN-TUR-02) con tests; si cambian, el impacto queda en `C-02`/`C-10` |
| Matriz RBAC no validada con usuarios | SE-12 (alta) | C-03 y todos los routers | Centralizar el chequeo de rol en una dependencia de `C-03`; cada change declara su fila de la matriz de 03 |
| Mecanismo de token no decidido (JWT es candidato) | D-03, SE-17 | C-03 | Aislar emisión y validación del token en `app/api/auth.py` para poder cambiarlo sin tocar routers |
| Alcance de la auditoría (solo turnos vs también recursos) | IF-06 (alta) | C-11, C-12, C-13, C-15 | El MVP audita solo turnos (RN-AUD-01); ampliar sería un change nuevo |
| Stack provisional: SQLite en lugar de PostgreSQL/Docker | IN-01, SE-22, D-01 | C-01, C-11 | SQL parametrizado y acceso a datos concentrado en `app/db/`; revisar criterio de D-01 antes de `C-11` |
| Zona horaria y DST | SE-05 | C-02, C-10, C-12, C-13 | Reloj inyectado y fechas locales sin offset (convención de 04); `CLINIC_TIMEZONE` en config |
| Feriados de todo el consultorio se cargan recurso por recurso | SE-24 | C-09 | El MVP mantiene alcance profesional/sillón; un alcance "consultorio" sería un change posterior |
| Turno que cruza el corte de mediodía | SE-14 | C-08, C-10 | RN-PRO-02 con test de dominio explícito |
| Usuario odontólogo necesita `profesional_id`, pero auth va antes que profesionales | 04 §Usuario, SE | C-03, C-07 | `C-03` crea la columna nullable; `C-07` valida que exista el profesional al crear un odontólogo |

### Resumen

| Fase | Changes | Governance máximo |
|------|---------|-------------------|
| FASE 1 — Cimientos y acceso | C-01, C-02, C-03 | CRITICO |
| FASE 2 — Recursos, pacientes y disponibilidad | C-04 a C-09 | ALTO |
| FASE 3 — Ciclo de vida del turno | C-10 a C-13 | CRITICO |
| FASE 4 — Consultas y trazabilidad | C-14 a C-16 | ALTO |
| FASE 5 — Cierre del MVP | C-17 | BAJO |
| FASE 6 — Posterior al MVP | sin changes (fuera de alcance) | — |

---

## FASE 1 — Cimientos y acceso

> `C-02` y `C-03` son paralelos una vez completado `C-01`.

### [C-01] `foundation-setup`
- **Estado**: `[x]` completado
- **Scope**:
  - `pyproject.toml` / `requirements.txt` con FastAPI, uvicorn, pydantic, pytest y httpx (TestClient)
  - Estructura `app/{domain,api,db}/` y `tests/{domain,api}/` según 08
  - `app/config.py`: lectura de `APP_ENV`, `DATABASE_URL`, `CLINIC_TIMEZONE` desde variables de entorno
  - `.env.example` solo con placeholders; `.env` en `.gitignore`
  - `app/db/conexion.py`: conexión SQLite, `PRAGMA foreign_keys=ON`, helper de transacción (context manager con commit/rollback)
  - `app/db/esquema.sql` inicial vacío + aplicación del esquema al arrancar (cada change agrega sus tablas)
  - `app/main.py` con `GET /health` público
  - `tests/conftest.py`: SQLite temporal por test y `TestClient`
  - Tests: `GET /health` → 200; transacción hace rollback ante excepción
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Variables de entorno
  - `knowledge-base/09_decisiones_y_supuestos.md` §D-01
  - `knowledge-base/02_descripcion_general.md` §API REST
  - `knowledge-base/10_preguntas_abiertas.md` §IN-01

### [C-02] `dominio-base`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/domain/models.py`: dataclasses `Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo` (sin dependencias de FastAPI ni DB)
  - `app/domain/intervalos.py`: `solapan(a, b)` con intervalos semiabiertos `[inicio, fin)` (RN-TUR-04)
  - `app/domain/errores.py`: `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`, `TurnoNoModificable`, `DatoInvalido`
  - Reloj inyectable (`ahora: datetime` como parámetro) y `es_futuro(turno, ahora)` (RN-TUR-09)
  - Tests de dominio: contiguos válidos, solapamiento parcial, contención, mismo inicio; `es_futuro` con reloj fijo (antes, igual, después)
- **Dependencias**: `C-01`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados, §Testing
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TUR-04, §RN-TUR-09
  - `knowledge-base/04_modelo_de_datos.md` §Convenciones
  - `knowledge-base/10_preguntas_abiertas.md` §SE-05, §SE-10

### [C-03] `auth-login-roles`
- **Estado**: `[x]` completado
- **Scope**:
  - Tabla `usuario` (`id`, `username` único, `password_hash`, `rol`, `profesional_id` nullable, `activo`)
  - Hash con sal (bcrypt o argon2); nunca se guarda la contraseña (RN-ACC-04)
  - `POST /auth/login` → token con id de usuario y rol; credenciales inválidas → 401
  - `app/api/auth.py`: dependencia `usuario_actual` (401 sin token, inválido o vencido) y `requiere_rol(*roles)` (403)
  - Variables `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` en config y `.env.example` (placeholders)
  - Usuario `admin_demo` creado desde `SEED_ADMIN_PASSWORD` solo en desarrollo
  - Mapeo global de errores a JSON en español con código consistente (RN-GLO-01)
  - Tests: login ok/401, ruta protegida sin token 401, rol sin permiso 403, columna guarda hash y no texto plano
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC, §Rutas públicas
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Acceso, §RN-GLO-01
  - `knowledge-base/07_flujos_principales.md` §Flujo 1
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad
  - `knowledge-base/09_decisiones_y_supuestos.md` §D-03

---

## FASE 2 — Recursos, pacientes y disponibilidad

> Con `C-03` listo, `C-04`, `C-05` y `C-06` son paralelos. Con `C-04` listo, `C-07`, `C-08` y `C-09` son paralelos.

### [C-04] `profesionales`
- **Estado**: `[x]` completado
- **Scope**:
  - Tabla `profesional` (`nombre`, `apellido`, `matricula` opcional, `activo`)
  - `GET/POST /profesionales`, `PATCH /profesionales/{id}` (incluye desactivar con `activo=false`)
  - Permisos: administración C L E B; recepción y odontólogo solo L (RN-ACC-02)
  - Tests: alta válida, nombre vacío → 422, recepción creando → 403, desactivado sigue listándose como inactivo
- **Dependencias**: `C-03`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Profesional
  - `knowledge-base/06_funcionalidades.md` §US-001
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/05_reglas_de_negocio.md` §RN-REC-03

### [C-05] `sillones-prestaciones`
- **Estado**: `[x]` completado
- **Scope**:
  - Tablas `sillon` (`nombre` único, `activo`) y `prestacion` (`nombre` único, `duracion_minutos > 0`, `activa`)
  - `GET/POST /sillones`, `PATCH /sillones/{id}`; `GET/POST /prestaciones`, `PATCH /prestaciones/{id}`
  - Permisos: administración C L E B; recepción y odontólogo solo L
  - Tests: nombre duplicado → 409, duración 0 o negativa → 422 (RN-REC-01), recepción creando → 403
- **Dependencias**: `C-03`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Sillon, §Prestacion
  - `knowledge-base/06_funcionalidades.md` §US-002, §US-003
  - `knowledge-base/05_reglas_de_negocio.md` §RN-REC-01, §RN-REC-03
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-06] `pacientes`
- **Estado**: `[x]` completado
- **Scope**:
  - Tabla `paciente` (`nombre`, `apellido`, `dni` único, `telefono`, `obra_social`, `nro_afiliado` opcionales)
  - `GET/POST /pacientes`, `PATCH /pacientes/{id}`; la obra social es solo un dato, sin liquidación (RN-PAC-01)
  - Permisos: administración y recepción C L E; odontólogo L (de sus turnos: se completa cuando existan turnos, ver SE-12)
  - Fixtures solo con datos ficticios, DNI con sufijo "(ficticio)" (RN-PAC-03)
  - Tests: alta con y sin obra social, DNI duplicado → 409 (RN-PAC-02), odontólogo creando → 403
- **Dependencias**: `C-03`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Paciente
  - `knowledge-base/06_funcionalidades.md` §US-011
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Pacientes
  - `knowledge-base/10_preguntas_abiertas.md` §IF-02, §SE-15

### [C-07] `gestion-usuarios`
- **Estado**: `[x]` completado
- **Scope**:
  - `GET/POST /usuarios`, `PATCH /usuarios/{id}` (rol, activo, reset de contraseña) solo para administración
  - Validación: rol odontólogo exige `profesional_id` existente y activo (SE); los demás roles lo dejan nulo
  - La respuesta nunca incluye `password_hash`
  - Tests: admin crea recepción y odontólogo vinculado, odontólogo sin profesional → 422, recepción usando la ruta → 403, usuario desactivado no puede loguear
- **Dependencias**: `C-03`, `C-04`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-013
  - `knowledge-base/04_modelo_de_datos.md` §Usuario
  - `knowledge-base/03_actores_y_roles.md` §RBAC
  - `knowledge-base/02_descripcion_general.md` §API REST

### [C-08] `horarios-atencion`
- **Estado**: `[x]` completado
- **Scope**:
  - Tabla `horario_atencion` (`profesional_id`, `dia_semana` 0-6, `hora_desde`, `hora_hasta`) con índice (`profesional_id`, `dia_semana`)
  - Dominio: validar `hora_desde < hora_hasta` y que las franjas del mismo día no se superpongan
  - `GET/POST /profesionales/{id}/horarios` (administración escribe; odontólogo lee los propios)
  - Tests de dominio: franja invertida inválida, dos franjas por día (mañana y tarde) válidas, franjas superpuestas inválidas; API: profesional inexistente → 422
- **Dependencias**: `C-02`, `C-04`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §HorarioAtencion
  - `knowledge-base/06_funcionalidades.md` §US-004
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PRO-01, §RN-PRO-02
  - `knowledge-base/10_preguntas_abiertas.md` §SE-14

### [C-09] `bloqueos`
- **Estado**: `[x]` completado
- **Scope**:
  - Tabla `bloqueo` (`alcance` profesional|sillón, `recurso_id`, `inicio`, `fin`, `motivo`) con índice (`alcance`, `recurso_id`, `inicio`)
  - Dominio: `inicio < fin` (RN-REC-02)
  - `GET/POST/DELETE /bloqueos` (administración C L B; recepción y odontólogo L)
  - Fuera de alcance de este change: listar turnos afectados por el bloqueo (va en `C-16`)
  - Tests: inicio >= fin → 422, recurso inexistente → 422, eliminar bloqueo, recepción creando → 403
- **Dependencias**: `C-02`, `C-04`, `C-05`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Bloqueo
  - `knowledge-base/06_funcionalidades.md` §US-005
  - `knowledge-base/07_flujos_principales.md` §Flujo 5
  - `knowledge-base/05_reglas_de_negocio.md` §RN-REC-02
  - `knowledge-base/10_preguntas_abiertas.md` §SE-09, §SE-24

---

## FASE 3 — Ciclo de vida del turno

> `C-10` se puede hacer en paralelo con toda la FASE 2 (solo necesita `C-02`). `C-12` y `C-13` son paralelos.

### [C-10] `reglas-alta-turno`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/domain/reglas_turno.py::validar_alta(...)`: recibe prestación, horarios, bloqueos y turnos activos ya cargados; devuelve el turno armado o lanza error de dominio
  - `fin = inicio + duracion_minutos` (RN-TUR-01)
  - Dentro de una única franja de atención (RN-PRO-01/02) → si no, `FueraDeHorario`
  - Sin superposición con bloqueos del profesional o del sillón (RN-TUR-05) → `DentroDeBloqueo`
  - Sin superposición por profesional, sillón (RN-TUR-03) ni paciente (RN-TUR-12); los cancelados no cuentan (RN-TUR-08) → `ConflictoAgenda`
  - Parámetro `excluir_turno_id` para reutilizar en reprogramación (RN-TUR-08)
  - Tests de dominio: un caso por cada ejemplo de "Verificación (dominio)" de RN-TUR-01, 03, 04, 05, 08, 12 y RN-PRO-01/02
- **Dependencias**: `C-02`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Turnos, §Dominio: Recursos y disponibilidad
  - `knowledge-base/08_arquitectura_propuesta.md` §Cómo se usa el dominio
  - `knowledge-base/07_flujos_principales.md` §Flujo 2
  - `knowledge-base/10_preguntas_abiertas.md` §SE-02, §SE-03, §SE-04, §SE-10

### [C-11] `crear-turno`
- **Estado**: `[x]` completado
- **Scope**:
  - Tablas `turno` (con índices por profesional, sillón y paciente + `inicio`) y `auditoria_turno` (solo inserción)
  - `POST /turnos` (administración y recepción): carga contexto, llama a `validar_alta`, inserta turno `reservado` + auditoría `crear` en una sola transacción
  - `GET /turnos/{id}` (autenticado)
  - Traducción de errores: conflicto, fuera de horario o bloqueo → 409; recurso inexistente o inactivo, sin `sillon_id` → 422 (RN-GLO-01, RN-REC-03, RN-TUR-02)
  - Tests de API: 201 con estado `reservado` (RN-TUR-14), 409 por profesional y por sillón, contiguos aceptados, 422 con sillón inactivo, odontólogo creando → 403, auditoría con usuario y fecha, doble reserva del mismo hueco → la segunda 409 (SE-06)
- **Dependencias**: `C-06`, `C-08`, `C-09`, `C-10`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 2
  - `knowledge-base/04_modelo_de_datos.md` §Turno, §AuditoriaTurno
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Auditoría, §RN-GLO-01
  - `knowledge-base/06_funcionalidades.md` §US-006
  - `knowledge-base/10_preguntas_abiertas.md` §SE-06, §IF-06

### [C-12] `cancelar-turno`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `app/domain/reglas_turno.py::validar_cancelacion(turno, ahora)`: turno futuro (RN-TUR-09) y no cancelado (RN-TUR-10)
  - `POST /turnos/{id}/cancelar` (administración y recepción): estado `cancelado` + auditoría con antes/después en una transacción
  - Errores: inexistente → 404, pasado o en curso → 409, ya cancelado → 409
  - Tests: con reloj fijo (antes, igual, después); cancelar y volver a reservar el mismo hueco → 201 (RN-TUR-06); segunda cancelación → 409
- **Dependencias**: `C-11`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 3
  - `knowledge-base/06_funcionalidades.md` §US-007
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TUR-06, §RN-TUR-09, §RN-TUR-10, §RN-AUD-01
  - `knowledge-base/10_preguntas_abiertas.md` §SE-08, §SE-11

### [C-13] `reprogramar-turno`
- **Estado**: `[x]` completado
- **Scope**:
  - `app/domain/reglas_turno.py::validar_reprogramacion(...)`: futuro y activo, recalcula fin y reutiliza `validar_alta` excluyendo el propio id (RN-TUR-07/08)
  - `POST /turnos/{id}/reprogramar` con nuevo inicio y, opcional, nuevo profesional y/o sillón; mismo `turno_id`
  - Auditoría `reprogramar` con antes/después; si se rechaza, no cambia el turno ni se audita (RN-AUD-03)
  - Tests: mover sobre su propio horario anterior aceptado, horario ocupado → 409 sin nuevo registro de auditoría, cancelado o pasado → 409
- **Dependencias**: `C-11`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/06_funcionalidades.md` §US-008
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TUR-07, §RN-TUR-08, §RN-AUD-03
  - `knowledge-base/09_decisiones_y_supuestos.md` §D-05
  - `knowledge-base/10_preguntas_abiertas.md` §SE-21

---

## FASE 4 — Consultas y trazabilidad

> Con `C-11` listo, `C-14` y `C-16` corren en paralelo con `C-12`/`C-13`. `C-15` espera a `C-12` y `C-13`.

### [C-14] `agenda`
- **Estado**: `[x]` completado
- **Scope**:
  - `GET /agenda/profesionales/{id}?desde&hasta` y `GET /agenda/sillones/{id}?desde&hasta`
  - Devuelve turnos activos y bloqueos del rango, ordenados por inicio (sirve para vista diaria y semanal)
  - Odontólogo solo su propia agenda por `usuario.profesional_id` (RN-ACC-03); recepción y administración todas
  - Tests: orden por inicio, cancelados excluidos, bloqueos incluidos, desde > hasta → 422, odontólogo A pidiendo agenda de B → 403
- **Dependencias**: `C-11`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 6
  - `knowledge-base/06_funcionalidades.md` §US-009, §US-010
  - `knowledge-base/05_reglas_de_negocio.md` §RN-ACC-03
  - `knowledge-base/03_actores_y_roles.md` §RBAC

### [C-15] `consulta-auditoria`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `GET /auditoria?turno_id=` solo administración: registros en orden cronológico con usuario, acción, antes/después y fecha y hora
  - Sin rutas PUT/PATCH/DELETE de auditoría (RN-AUD-02)
  - Tests: crear + reprogramar + cancelar deja exactamente 3 registros en orden (RN-AUD-01), PATCH/DELETE → 405/404, recepción → 403
- **Dependencias**: `C-12`, `C-13`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 7
  - `knowledge-base/06_funcionalidades.md` §US-014
  - `knowledge-base/05_reglas_de_negocio.md` §Dominio: Auditoría
  - `knowledge-base/10_preguntas_abiertas.md` §IF-06, §SE-13

### [C-16] `bloqueos-turnos-afectados`
- **Estado**: `[ ]` pendiente — **requiere decidir SE-09 antes del propose**
- **Scope**:
  - Según la propuesta actual del MVP: `POST /bloqueos` devuelve, junto al bloqueo creado, la lista de turnos activos que quedan dentro del intervalo y recurso
  - No cancela ni modifica esos turnos (recepción los reprograma a mano)
  - Si equipo/cátedra decide otra opción en SE-09 (rechazar el bloqueo o cancelar automáticamente), este scope se reemplaza antes del propose
  - Tests: bloqueo sin turnos → lista vacía; bloqueo sobre 2 turnos activos y 1 cancelado → lista con 2; los turnos siguen en estado `reservado`
- **Dependencias**: `C-11`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/10_preguntas_abiertas.md` §SE-09
  - `knowledge-base/07_flujos_principales.md` §Flujo 5
  - `knowledge-base/06_funcionalidades.md` §US-005
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TUR-05

---

## FASE 5 — Cierre del MVP

### [C-17] `seed-y-flujo-e2e`
- **Estado**: `[ ]` pendiente
- **Scope**:
  - `app/db/seed.py` con los datos ficticios de 04 (2 profesionales, 2 sillones, 3 prestaciones, horarios L-V, 2 pacientes, 3 usuarios demo); contraseñas solo desde variables de entorno
  - Test de API extremo a extremo: login recepción → crear turno → reprogramar → cancelar → login administración → consultar auditoría
  - Test de revisión de fixtures: DNI con sufijo "(ficticio)" (RN-PAC-03); ningún secreto versionado
  - Cada RN de 05 mapeada a al menos un test (tabla de trazabilidad en el README o en el change)
  - README con cómo levantar la API y correr los tests
- **Dependencias**: `C-07`, `C-14`, `C-15`, `C-16`
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial
  - `knowledge-base/05_reglas_de_negocio.md`
  - `knowledge-base/08_arquitectura_propuesta.md` §Testing, §Variables de entorno
  - `knowledge-base/01_vision_y_objetivos.md`

---

## FASE 6 — Posterior al MVP (fuera de alcance, sin changes asignados)

> **Nada de esta fase forma parte del MVP** ni tiene código C-NN. Son los ítems de D.3 "Diferenciador" y "Etapas posteriores" del informe. No se deben incluir en tareas de los changes C-01 a C-17 (RN-GLO-02). Si alguno se aprueba en el futuro, se planifica como change nuevo después de cerrar `C-17`.

| Ítem | Tipo (informe D.3) | Pregunta abierta | Nota |
|------|--------------------|------------------|------|
| Confirmación del turno por enlace | Diferenciador | — | Requiere estados confirmado/ausente (hoy fuera, RN-TUR-14) |
| Lista de espera con horarios liberados | Diferenciador | IF-03 | Se apoyaría en `C-12` (cancelar libera horario) |
| Anticipación mínima configurable | Diferenciador | IF-10, SE-08 | Extiende `validar_cancelacion` / `validar_reprogramacion` |
| Reserva online por enlace público | Diferenciador | — | El paciente pasaría a ser usuario |
| Exportación de datos | Diferenciador | IF-05 | — |
| Alcance de bloqueo "consultorio" (feriados generales) | Supuesto del equipo | SE-24 | No es D.3; extensión posible de `C-09` |
| Recordatorios por WhatsApp Business API | Etapa posterior | IF-08 | Costo por mensaje y proveedor oficial |
| Señas y pagos con Mercado Pago | Etapa posterior | — | — |
| Facturación electrónica ARCA | Etapa posterior | IF-01 | — |
| Liquidación a obras sociales y prepagas | Etapa posterior | IF-02 | El MVP solo guarda el dato en `paciente` |
| Historia clínica, odontograma y periodontograma | Etapa posterior | IF-07 | Ley 27.706, Decreto 393/2023 |
| Reportes, métricas, multisede, IA | Etapa posterior | SE-16 | — |
| Frontend React y aplicación móvil | Etapa posterior | — | El MVP es solo API |
