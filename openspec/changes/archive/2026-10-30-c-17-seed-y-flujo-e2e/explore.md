# Explore — C-17 seed-y-flujo-e2e

Relevamiento previo al propose. **No implementa nada**: fija el estado actual, la brecha, la trazabilidad RN → test, los riesgos y las decisiones cerradas por el equipo.

> Contexto verificado (2026-10-30): rama `elias-c17-seed-y-flujo-e2e` creada desde `main` (`94b475e`, PR #50 de C-16 mergeado). `git status` limpio. Suite: **759 passed**. `openspec list` → sin changes activos. `C-07` `C-14` `C-15` (PR #47) y `C-16` están archivados y mergeados: **las cuatro dependencias de C-17 están cerradas y no queda nada pendiente de C-07 ni de C-15**. No hay C-18 en el roadmap: C-17 es el último change del MVP.

## 1. Alcance declarado en el roadmap

`CHANGES.md` (`[C-17] seed-y-flujo-e2e`, líneas 437-452):

- `app/db/seed.py` con los datos ficticios de KB 04 (2 profesionales, 2 sillones, 3 prestaciones, horarios L-V, 2 pacientes, 3 usuarios demo); contraseñas **solo** desde variables de entorno.
- Test de API extremo a extremo: login recepción → crear turno → reprogramar → cancelar → login administración → consultar auditoría.
- Test de revisión de fixtures: DNI con sufijo `"(ficticio)"` (RN-PAC-03); ningún secreto versionado.
- Cada RN de KB 05 mapeada a al menos un test (tabla de trazabilidad en el README **o** en el change).
- README con cómo levantar la API y correr los tests.

Dependencias `C-07`, `C-14`, `C-15`, `C-16` · Governance **BAJO** · Posición: onda 8, último change, sin sucesores.

**Ampliación aprobada por el equipo:** C-17 también agrega el test que falta de `RN-REC-03` (que el histórico de turnos se conserva cuando se desactiva un recurso), porque es el único hueco de comportamiento que quedó abierto en todo el MVP.

## 2. Qué existe hoy

| Pieza | Estado | Evidencia |
|---|---|---|
| `sembrar_admin_demo(conexion, password_hash)` idempotente (`ON CONFLICT(username) DO NOTHING`) | **Existe** | `app/db/seed.py:21-26` |
| Disparo del seed en el `lifespan` (solo `development` + `SEED_ADMIN_PASSWORD`) | **Existe** | `app/main.py:40-49` |
| `Config.seed_admin_password` (una sola variable de seed) | **Existe** | `app/config.py:40,56` |
| Tests del seed actual (unidad + arranque + contraseña no persistida) | **Existen (11)** | `tests/api/test_seed.py` |
| Recurso `profesional` / `sillon` / `prestacion` / `paciente` / `horario_atencion` (repositorios + API) | **Existen** | `app/db/repositorio_*.py`, `app/api/*.py` |
| `POST /auth/login` → `{access_token, token_type}` | **Existe** | `app/api/auth.py`, `tests/api/test_auth.py` |
| `POST /turnos` (201, `estado: reservado`, fin por prestación) | **Existe** | `app/api/turnos.py` |
| `POST /turnos/{id}/reprogramar` | **Existe (C-13)** | `app/api/turnos.py` |
| `POST /turnos/{id}/cancelar` | **Existe (C-12)** | `app/api/turnos.py` |
| `GET /auditoria?turno_id=` (solo administración) | **Existe (C-15)** | `app/api/auditoria.py` |
| `GET /agenda/profesionales/{id}` y `/agenda/sillones/{id}` | **Existe (C-14)** | `app/api/agenda.py` |
| `POST /bloqueos` con turnos afectados | **Existe (C-16)** | `app/api/bloqueos.py` |
| Fixtures `cliente`, `config`, `reloj`, `RelojFijo`, `usuario`, `token_de` | **Existen** | `tests/conftest.py` |
| Seed del catálogo demo (profesionales, sillones, prestaciones, horarios, pacientes) | **No existe** | `app/db/seed.py` solo crea `admin_demo` |
| Usuarios `recepcion_demo` / `odontologo_demo` | **No existen** | idem |
| Test E2E del flujo completo | **No existe** | ningún test cruza login + alta + reprogramación + cancelación + auditoría |
| Test de RN-PAC-03 (fixtures ficticias) | **No existe** | solo convención manual (203 usos del sufijo, sin guardia) |
| Test de RN-REC-03 (el histórico se conserva) | **No existe** | solo se prueba el rechazo del recurso inactivo, no la conservación |
| Tabla de trazabilidad RN → test | **No existe** | no está en README ni en `docs/` |
| README al día | **No** | ver §5 |
| `.env.example` con las variables del seed demo | **Parcial** | solo `SEED_ADMIN_PASSWORD` (`.env.example:16`) |

## 3. Trazabilidad RN → test (el núcleo del relevamiento)

Método: extraje las 31 reglas de `knowledge-base/05_reglas_de_negocio.md`, busqué las citas explícitas `RN-xx-NN` en la suite y después verifiqué una por una contra el nombre y el cuerpo del test, porque muchas reglas están cubiertas sin citar su código.

| RN | Regla (resumen) | Test que la cubre | Estado |
|---|---|---|---|
| PRO-01 | Turno fuera del horario del profesional se rechaza | `domain/test_reglas_turno.py::test_franja_turno_que_empieza_antes_de_la_apertura_lanza_fuera_de_horario` (+ `_excede_el_cierre_`, `_dia_sin_horario_`) | OK |
| PRO-02 | El turno debe caber entero en una franja (no cruzar el corte) | `domain/test_reglas_turno.py::test_franja_turno_que_cruza_el_corte_entre_manana_y_tarde_lanza_fuera_de_horario` | OK |
| REC-01 | Duración entera > 0; nombre único de sillón/prestación | `api/test_prestaciones.py::test_post_prestaciones_con_duracion_cero_responde_422`, `::test_post_prestaciones_con_nombre_duplicado_responde_409` | OK |
| REC-02 | Bloqueo con `inicio < fin` y motivo | `api/test_bloqueos.py::test_post_bloqueos_con_inicio_mayor_o_igual_que_fin_responde_422` + `domain/test_bloqueos.py` | OK |
| REC-03 | Recursos desactivados no aceptan turnos nuevos; el histórico se conserva | `api/test_turnos.py::test_post_turnos_con_recurso_inactivo_responde_422_y_no_escribe` | **PARCIAL**: falta "los turnos históricos se conservan" → **C-17 la completa** (§10 escenario 8) |
| TUR-01 | `fin = inicio + duracion_minutos` | `domain/test_reglas_turno.py::test_fin_se_calcula_con_prestacion_de_45_minutos` (+ 30) y `api/test_turnos.py::test_post_turnos_con_limpieza_de_45_minutos_calcula_fin_10_45` | OK |
| TUR-02 | Todo turno tiene sillón | `api/test_turnos.py::test_post_turnos_sin_sillon_id_responde_422_con_detalle_del_campo` | OK |
| TUR-03 | Sin solapamiento por profesional ni por sillón | `domain/test_reglas_turno.py::test_solapamiento_del_profesional_lanza_conflicto_agenda`, `::test_solapamiento_del_sillon_...` | OK |
| TUR-04 | Intervalos semiabiertos; contiguos válidos | `domain/test_intervalos.py::test_turnos_contiguos_no_solapan`, `test_reglas_turno.py::test_contiguo_mismo_profesional_y_sillon_se_acepta`, `api/test_turnos.py::test_post_turnos_contiguos_antes_y_despues_se_aceptan` | OK |
| TUR-05 | Fuera de horario o dentro de bloqueo se rechaza | `domain/test_reglas_turno.py::test_bloqueo_de_sillon_rechaza_turno_en_ese_sillon` (+ 4 de bloqueos) | OK |
| TUR-06 | Cancelar libera el horario | `api/test_cancelar_turno.py::test_tras_cancelar_se_puede_reservar_el_mismo_hueco_201` | OK |
| TUR-07 | Reprogramar es operación propia y conserva el historial | `api/test_reprogramar_turno.py::test_reprogramar_recepcion_mueve_el_turno_200_conservando_el_id`, `::test_reprogramar_registra_auditoria_reprogramar_con_antes_y_despues` | OK |
| TUR-08 | El propio turno no se auto-conflictúa; cancelados no bloquean | `domain/test_reglas_turno.py::test_excluir_turno_id_ignora_el_propio_turno`, `::test_cancelado_que_se_superpone_no_genera_conflicto` | OK |
| TUR-09 | Solo turnos futuros se cancelan/reprograman | `domain/test_cancelar_turno.py` (4 tests con reloj) + `api/test_cancelar_turno.py::test_turno_pasado_409_y_sigue_reservado` | OK |
| TUR-10 | Un turno cancelado no se vuelve a cancelar/reprogramar | `api/test_cancelar_turno.py::test_segunda_cancelacion_409_sin_nueva_auditoria` | OK |
| TUR-11 | Sin sobreturnos: ningún rol fuerza un solapamiento | `api/test_turnos.py::test_post_turnos_administracion_tampoco_puede_superponer_un_turno` | OK |
| TUR-12 | Un paciente no tiene dos turnos activos superpuestos | `domain/test_reglas_turno.py::test_solapamiento_del_paciente_lanza_conflicto_agenda` | OK |
| TUR-13 | Sin margen de limpieza obligatorio | mismo test que TUR-04 | **IMPLÍCITA** (no hay regla nueva que codificar) |
| TUR-14 | Turno nuevo nace `reservado` | `api/test_turnos.py::test_post_turnos_recepcion_crea_turno_reservado_201` | OK |
| PAC-01 | Datos mínimos + obra social opcional | `api/test_pacientes.py::test_post_pacientes_alta_valida_con_obra_social`, `::test_post_pacientes_alta_valida_sin_opcionales` | OK |
| PAC-02 | DNI único | `api/test_pacientes.py::test_post_pacientes_con_dni_duplicado_responde_409_sin_repetir_el_dni` | OK |
| PAC-03 | Solo datos ficticios, DNI con sufijo `(ficticio)` | **ninguno** | **FALTA** → **C-17 la agrega** |
| ACC-01 | Todo salvo login/health exige token | 401 en cada router: `api/test_turnos.py::test_post_turnos_sin_token_responde_401_no_autenticado`, `test_auditoria.py::test_sin_token_401_no_autenticado`, `test_pacientes.py::test_get_pacientes_sin_token_responde_401`, etc. | OK |
| ACC-02 | Permisos por rol → 403 | `api/test_prestaciones.py::test_recepcion_post_prestaciones_recibe_403`, `api/test_turnos.py::test_post_turnos_odontologo_responde_403_sin_permiso_y_no_escribe` | OK |
| ACC-03 | El odontólogo solo ve su propia agenda | `api/test_agenda.py::test_agenda_profesional_odontologo_ajeno_403`, `::test_agenda_sillon_odontologo_403` | OK |
| ACC-04 | Contraseñas solo como hash; secretos no versionados | `api/test_auth.py::test_la_contrasena_no_queda_en_la_base_ni_en_la_respuesta_del_login`, `api/test_seed.py::test_la_contrasena_del_seed_no_queda_en_el_archivo_de_la_base` | OK |
| AUD-01 | Crear/reprogramar/cancelar deja registro con quién, qué y cuándo | `api/test_auditoria.py::test_historial_de_tres_acciones_devuelve_tres_registros_en_orden` | OK |
| AUD-02 | Auditoría append-only, sin rutas de edición | `api/test_auditoria.py::test_patch_y_delete_sobre_auditoria_405_sin_cambios`, `api/test_turnos.py::test_no_hay_rutas_para_modificar_o_borrar_turnos_ni_auditoria` | OK |
| AUD-03 | Operación rechazada no cambia turno ni auditoría | `api/test_reprogramar_turno.py::test_reprogramar_sobre_otro_turno_del_profesional_409_conflicto_agenda` (usa `_assert_rechazo_sin_cambios`), `api/test_turnos.py::test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias` | OK |
| GLO-01 | Un JSON de error por código, en español | `api/test_errores.py` (401/403/404/405/422) + los 409 en `test_turnos.py`/`test_cancelar_turno.py` | OK |
| GLO-02 | Fuera del MVP no hay reglas | — | **NO APLICA** (declara una ausencia) |

**Balance: 27 con test explícito · 1 parcial (RN-REC-03, la completa C-17) · 1 implícita (RN-TUR-13) · 1 sin test (RN-PAC-03, la agrega C-17) · 1 no aplicable (RN-GLO-02).**

Conclusión: **la cobertura real ya es altísima**; lo que falta no es implementar reglas, es (a) los dos huecos detectados —RN-PAC-03 sin guardia y RN-REC-03 a medias—, (b) un artefacto durable que demuestre el mapeo, y (c) el flujo que atraviesa todas las reglas juntas de punta a punta. Eso es exactamente C-17.

## 4. Qué falta, capa por capa

### 4.1 Seed (`app/db/seed.py`)

Hoy solo `admin_demo`. Falta el catálogo de KB 04 §Seed data inicial:

| Entidad | Filas | Nota técnica |
|---|---|---|
| `profesional` | 2 | **Sin `UNIQUE`** en `(nombre, apellido, matricula)` → `ON CONFLICT` no sirve |
| `sillon` | 2 | `nombre` UNIQUE → `ON CONFLICT DO NOTHING` sirve |
| `prestacion` | 3 | `nombre` UNIQUE → idem |
| `horario_atencion` | **20** (2 profesionales × 5 días × 2 franjas) | **Sin `UNIQUE` ni índice único** → el riesgo de duplicar es real |
| `paciente` | 2 | `dni` UNIQUE → idem |
| `usuario` | 3 | `username` UNIQUE → idem; `odontologo_demo` necesita `profesional_id` |
| **Total** | **32 filas** | |

### 4.2 Disparo y configuración

- El `lifespan` ya llama al seed solo en `development` y solo si hay `SEED_ADMIN_PASSWORD`. Ese gate hay que extenderlo, no reemplazarlo.
- `Config` tiene una única variable de seed. Se necesitan las contraseñas de los tres usuarios demo (§6 D-02).
- `app/db/seed.py` **no puede importar `app/api/seguridad`** (regla dura 1: `db` no importa `api`), así que los hashes se siguen calculando en el `lifespan` y se pasan ya calculados. Ese contrato ya existe y hay que conservarlo.

### 4.3 Flujo E2E

No existe. Requiere: config de desarrollo (o llamada directa al seed), `RelojFijo` (el 2026-01-05 12:00 UTC es lunes 09:00 local, con lo cual el lunes 10:00 es futuro y cae dentro de la franja sembrada 09:00-13:00), y resolver ids desde la base (`paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`) sin depender de los endpoints de catálogo.

Alcance cerrado: **los 6 pasos del roadmap**, sin `GET /agenda` ni `POST /bloqueos`.

### 4.4 Trazabilidad

No existe como artefacto. La KB 05 ya tiene la columna "Verificación" regla por regla, pero nadie la contrasta con la suite. Va a `docs/trazabilidad-rn-test.md` (D-08), con un test que impida que se desactualice (D-09).

### 4.5 Spec delta

`openspec/specs/acceso-usuarios/spec.md:178` ya tiene el requirement **"Usuario administrador de desarrollo"**, con escenarios "Creación en development", "Arranque repetido idempotente", "Sin seed fuera de development" y "Sin seed si falta la contraseña". **C-17 no puede agregar el seed demo sin MODIFICAR ese requirement**: esa es la parte del propose que no es obvia. No hay delta de `errores-api` (no hay códigos nuevos) y no hay cambios de esquema.

### 4.6 README y `.env.example`

Ver §5.

## 5. README hoy vs. lo que debería decir

| Línea | Dice hoy | Realidad |
|---|---|---|
| 9 | "Implementados C-01, C-02, C-10 y C-03. La suite pasa en verde: `194 passed`" | 17 changes completos; **759 passed** (+ los de C-17) |
| 9-28 | Solo describe C-01/C-02/C-10/C-03 | Faltan C-04 a C-17 (recursos, turnos, cancelar, reprogramar, agenda, auditoría, bloqueos) |
| 78 | `SEED_ADMIN_PASSWORD` "contraseña del usuario `admin_demo`" | Con C-17 pasan a existir 3 usuarios demo |
| 137-142 | Sección "Usuario `admin_demo` en desarrollo" | Queda incompleta: falta `recepcion_demo` y `odontologo_demo` |
| 175-177 | "todavía no hay rutas protegidas en la API: las agregan los changes C-04 en adelante" | **Falso desde C-04**: hay 11 routers protegidos |
| 127-133 | `pytest tests` → "Resultado esperado: `194 passed`"; `GET /health` | El conteo está mal; falta el flujo de uso real |
| 210-236 | Estructura: `app/api/auth.py` solamente, `esquema.sql` = "tabla usuario" | Faltan `turnos.py`, `agenda.py`, `auditoria.py`, `repositorio_*.py`; `seed.py` describe solo `admin_demo` |
| 195-208 | Tabla de errores | **Está completa y correcta**: no hay que tocarla |

Lo que falta agregar: cómo correr el seed demo, el flujo curl/PowerShell de login → crear → reprogramar → cancelar → auditoría con los usuarios sembrados, el conteo real de la suite, el link a `docs/trazabilidad-rn-test.md`, la dependencia de `CLINIC_TIMEZONE` y la aclaración de que **no hace falta borrar `turnos.db`** para recibir los datos nuevos.

`.env.example` (16 líneas) solo tiene `SEED_ADMIN_PASSWORD`; faltan las variables nuevas.

## 6. Decisiones cerradas

| # | Decisión |
|---|---|
| D-01 | **Un módulo de seed con una entrada pública** `sembrar_demo(conexion, *, password_hash_admin, password_hash_recepcion, password_hash_odontologo) -> DatosDemo` que devuelve los ids, más funciones internas por grupo. `sembrar_admin_demo` **queda intacta** (sus 6 tests de unidad la fijan). |
| D-02 | **Tres variables de contraseña**: `SEED_ADMIN_PASSWORD` (existente), `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD`. Retrocompatible; no se reescribe el escenario "sin `SEED_ADMIN_PASSWORD` no se crea nada". |
| D-03 | **Gate del seed**: corre solo en `development` y solo si `SEED_ADMIN_PASSWORD` está definida (mismo gate de hoy). Dentro de ese gate, cada usuario se crea **solo si su propia contraseña está definida**; el catálogo demo se siembra siempre. |
| D-04 | **Idempotencia sin `UNIQUE`**: `INSERT … SELECT … WHERE NOT EXISTS` por clave natural (`nombre+apellido+matricula`; `profesional_id+dia_semana+hora_desde+hora_hasta`), todo dentro de un `transaccion()`. **No se agrega `UNIQUE` al esquema.** |
| D-05 | **No se siembran turnos.** Envejecen contra el reloj; el E2E crea los suyos. |
| D-06 | **El E2E arranca la app de verdad** con `APP_ENV=development` + variables de entorno y `RelojFijo`, como ya hace `tests/api/test_seed.py:118-134`; no llama al seed a mano. |
| D-07 | **Ubicación**: `tests/api/test_flujo_e2e.py`, un test principal de los 6 pasos y 2-3 de borde (hueco liberado reutilizable, `409` que no ensucia la auditoría). |
| D-08 | **La tabla de trazabilidad va a `docs/trazabilidad-rn-test.md`**, referenciada desde el README. El README se queda con el flujo E2E. |
| D-09 | **Test de trazabilidad**: lee `knowledge-base/05_reglas_de_negocio.md`, extrae los 31 códigos `RN-…` y verifica que cada uno figure en la tabla y que el test citado exista en disco (parseo con `ast`). |
| D-10 | **RN-PAC-03 se verifica sobre datos, no sobre código**: los DNI de los pacientes sembrados y de los creados por el E2E terminan en `"(ficticio)"`; y ninguna contraseña demo aparece en el archivo de la base. |
| D-11 | **Capability del delta**: `## MODIFIED` del requirement "Usuario administrador de desarrollo" en `acceso-usuarios` + `## ADDED` en la misma capability para catálogo demo, idempotencia, datos ficticios y contraseñas desde entorno; más un `## ADDED` en `base-tecnica` para la trazabilidad RN → test. **Sin capability nueva.** |
| D-12 | **Governance BAJO, sin `design.md` propio**: las decisiones D-01…D-12 se resuelven en el `proposal` y en `tasks.md`. |
| D-13 | **`odontologo_demo` se liga al profesional A** ("Odontólogo Ficticio A"). |
| D-14 | **`RN-REC-03` se completa en C-17**: desactivar un recurso con turnos y verificar que el turno sigue consultable. |
| D-15 | **El saneamiento documental queda fuera de C-17** (§7). |

## 7. Deuda técnica: fuera de C-17 (trabajo posterior)

Estas tres deudas **no son tareas de C-17**. Se resuelven en un único PR de saneamiento **después de archivar C-17**, sin `openspec new change`, con un commit `chore:`:

| # | Deuda | Diagnóstico real | Por qué fuera |
|---|---|---|---|
| 1 | `openspec validate --specs --strict` falla en `agenda` | No es "falta `## Purpose`": el spec entero está en español (`## Propósito`, `## Requisitos y Escenarios`, `### Requisito 1-5`, `#### Escenario 1-7`). Arreglarlo son ~14 líneas de encabezado, ninguna de contenido | Es deuda documental de C-14, no del seed. El gate que el proyecto usa en cada change es `openspec validate <change> --strict`, no `--specs` |
| 2 | `openspec validate --specs --strict` falla en `horarios-atencion` | No es un error: tiene `## Purpose` y `## Requirements`; el validador emite un **warning** porque el texto del primer requirement supera 500 caracteres (strict escala warnings a fallos) | Arreglarlo obliga a partir o reformular un requirement ya archivado: es una decisión de contenido, no de formato |
| 3 | `AccionAuditoria` duplicada (`app/domain/models.py:12` y `app/db/repositorio_turnos.py:18`) | Duplicación literal de un `Literal`; `repositorio_turnos.py` ya importa tipos de `app.domain.models`, así que borrar la línea local y sumarla al import es legal según la regla dura 1 | Refactor sin comportamiento observable y sin test que lo exija |

Consecuencia aceptada: al cerrar C-17, `openspec validate --specs --strict` seguirá en rojo por `agenda` y `horarios-atencion`. No bloquea el archive (el gate es por change).

## 8. Preguntas abiertas: resueltas por el equipo

| # | Pregunta | Resolución |
|---|---|---|
| 1 | RN-REC-03, segunda mitad ("los turnos históricos se conservan") | **Se agrega en C-17**: desactivar un recurso con turnos y verificar que el turno sigue consultable (D-14, §10 escenario 8) |
| 2 | ¿A qué profesional se liga `odontologo_demo`? | **Al profesional A** ("Odontólogo Ficticio A") (D-13) |
| 3 | ¿Se documenta la dependencia de `CLINIC_TIMEZONE`? | **Sí, en el README**: los horarios sembrados son hora local del consultorio |
| 4 | ¿Se documenta que una base existente recibe los datos nuevos? | **Sí, en el README**: no hace falta borrar `turnos.db`; el seed es aditivo e idempotente |
| 5 | ¿Dónde van el flujo y la tabla de trazabilidad? | **Flujo en el README; tabla en `docs/trazabilidad-rn-test.md`** (D-08) |
| 6 | ¿El E2E incluye `GET /agenda` y `POST /bloqueos`? | **No**: los 6 pasos del roadmap, alcance cerrado |
| 7 | ¿Saneamiento documental dentro o fuera? | **Fuera**, en un PR posterior (§7) |

No quedan preguntas abiertas bloqueantes para el propose.

## 9. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **`tests/api/test_seed.py` se rompe**: `:132` desempaca una tupla esperando **un** usuario y `:147` afirma `len == 1` | 2 tests rojos apenas se siembren los 3 usuarios | Previsto: C-17 actualiza esas dos aserciones en la misma tarea |
| **Horarios duplicados** en cada arranque (`horario_atencion` no tiene `UNIQUE`) | 20 → 40 → 60 filas | `WHERE NOT EXISTS` por clave natural (D-04) + test de doble arranque que cuenta 32 filas |
| **Profesionales duplicados** (`profesional` tampoco tiene `UNIQUE`) | 2 → 4 → 6 filas; y `odontologo_demo` apuntando a un id distinto en cada arranque | Misma mitigación; test explícito de idempotencia sobre las 6 tablas |
| **Arranque más lento** en development: 3 hashes Argon2 + 32 inserts en cada `uvicorn` | Molestia de DX | Medir; el `WHERE NOT EXISTS` evita writes, pero los hashes se calculan igual |
| **E2E dependiente de la hora** | Test flaky | `RelojFijo` (ya existe) y fecha derivada del lunes del reloj, nunca de `date.today()` |
| **E2E dependiente de la zona horaria** | Si el runner no está en `America/Argentina/Buenos_Aires`, el slot "10:00 local" puede caer fuera de la franja | El test fija `CLINIC_TIMEZONE` en su `Config`; no hereda el entorno |
| **Modificar un requirement ya archivado** (`acceso-usuarios`) | Delta mal armado → `validate` rojo o pérdida de escenarios | Copiar el requirement completo con sus 4 escenarios en `## MODIFIED` y **agregar** los nuevos; nunca reescribirlo de memoria |
| **Trazabilidad que se desactualiza** | El documento miente a los dos meses | El test de D-09 falla si una RN no está en la tabla o si el test citado no existe |
| **Escanear fixtures por regex** (RN-PAC-03) | Test frágil que falla por un comentario | Verificar sobre filas de la base (D-10), no sobre el código fuente |
| **README con ejemplos que no corren** | Mala impresión en la entrega | Los ejemplos se copian del E2E ya verde, con los mismos ids y claves |
| **Regresión de los 759 tests** | Estabilidad | C-17 solo agrega seed y tests, extiende el `lifespan`/`Config` y toca 2 aserciones de `test_seed.py` |
| **`.env.example` con valores reales** | Regla dura 9 | Solo placeholders `<definir-localmente>` + test de que la contraseña demo no queda en el archivo de la base |

## 10. Escenarios candidatos para el delta de spec

**Seed (capability `acceso-usuarios`, `## MODIFIED` + `## ADDED`)**

1. **Seed completo en development**: con las tres contraseñas definidas y base vacía, al arrancar existen 2 profesionales, 2 sillones, 3 prestaciones, 20 horarios (L-V × 09:00-13:00 y 14:00-18:00 × 2 profesionales), 2 pacientes y 3 usuarios demo activos.
2. **Idempotencia total**: un segundo arranque sobre la misma base deja exactamente las mismas 32 filas y los mismos `password_hash`.
3. **El `admin_demo` preexistente no se modifica**: se conserva su hash, su rol y su `activo` (comportamiento actual, extendido al resto).
4. **Sin `SEED_ADMIN_PASSWORD` no se siembra nada**: ni usuarios ni catálogo.
5. **Fuera de development no se siembra nada** (`test`, `production`).
6. **Contraseñas solo como hash**: la clave demo no aparece en ningún byte del archivo de la base y `password_hash` empieza con `$argon2id$`.
7. **`odontologo_demo` queda ligado al profesional A**; `recepcion_demo` y `admin_demo` sin `profesional_id`.
8. **Datos ficticios (RN-PAC-03)**: los dos pacientes demo tienen DNI terminado en `"(ficticio)"` y nombres rotulados como ficticios.
9. **RN-REC-03 completa**: un turno reservado sobre un recurso que luego se desactiva sigue consultable por `GET /turnos/{id}` (el histórico se conserva) y un turno nuevo sobre ese recurso responde `422`.

**Flujo E2E (verifica requirements ya existentes, sin requirement nuevo)**

10. **Login de recepción** con la clave sembrada → `200` con `access_token`.
11. **Alta de turno** con los recursos sembrados → `201`, `estado: "reservado"`, `fin = inicio + duración de la prestación`.
12. **Reprogramación** → `200`, mismo `turno_id`, `inicio` nuevo.
13. **Cancelación** → `200`, `estado: "cancelado"`, y el hueco liberado vuelve a ser reservable (RN-TUR-06 en el flujo real).
14. **Login de administración** → `200`.
15. **Auditoría del turno** → `200` con exactamente 3 registros `crear` → `reprogramar` → `cancelar`, con el `username` que operó y `antes: null` solo en el primero (RN-AUD-01).
16. **Un rechazo en el medio no ensucia la auditoría** (RN-AUD-03): forzar un `409` de reprogramación y verificar que sigue habiendo 3 registros.

**Trazabilidad (capability `base-tecnica`, `## ADDED`)**

17. **Toda RN de KB 05 está mapeada**: los 31 códigos aparecen en `docs/trazabilidad-rn-test.md` y cada test citado existe en la suite (falla si se agrega una regla sin test).

## 11. Próximo paso

C-17 no es un change de lógica: es el change de **cierre**. Lo que hay que construir es (1) un seed de 32 filas idempotente **sin `UNIQUE` en dos tablas**, (2) un E2E que arranque la app de verdad y recorra los 6 pasos del roadmap, (3) los dos tests que cierran los huecos —RN-PAC-03 y RN-REC-03— y (4) un artefacto de trazabilidad que no se pueda desactualizar sin que un test se ponga rojo.

Sigue `/opsx:propose c-17-seed-y-flujo-e2e` con las decisiones D-01…D-15 y los 17 escenarios candidatos de §10.
