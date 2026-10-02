# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **turnosodontologia** (módulo Python de gestión de turnos odontológicos, sin GUI ni deploy).
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

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
└── C-02 pacientes-profesionales
    ├── C-03 crear-turno-sin-solapamientos     ← PRIMER change Agenda (OPSX completo: explore → propose → apply → verify → archive)
    │   ├── C-04 confirmar-turno
    │   ├── C-05 reprogramar-turno
    │   ├── C-06 cancelar-turno ──┐
    │   ├── C-07 bloqueos-franja ─┼── C-08 sobreturno-explicito
    │   │                         └── C-09 lista-espera
    │   └── C-11 caja-minima (requiere C-04 + C-06)
    ├── C-10 odontograma-minimo (solo requiere C-02)
    └── C-12 trazabilidad-auditoria-persistencia (requiere C-05 + C-09 + C-11)
```

### Paralelismo por fase

> Cada "gate" es un punto de sincronización. Los changes dentro de un grupo pueden ejecutarse en paralelo.

```
GATE 0: ninguna
  → C-01 (solo)

GATE 1: C-01 ✓
  → C-02 (solo)

GATE 2: C-02 ✓
  → C-03 crear-turno-sin-solapamientos (solo)     ← PRIMER change Agenda, ciclo OPSX completo

GATE 3: C-03 ✓                          ← PRIMER FORK (5 paralelos)
  → C-04 confirmar-turno                [Agente A]
  → C-05 reprogramar-turno              [Agente B]
  → C-06 cancelar-turno                 [Agente A — tras C-04]
  → C-07 bloqueos-franja                [Agente B — tras C-05]
  → C-10 odontograma-minimo             [Agente C]

GATE 4: C-06 + C-07 ✓
  → C-08 sobreturno-explicito           [Agente B]
  → C-09 lista-espera                   [Agente A]

GATE 5: C-04 + C-06 ✓
  → C-11 caja-minima                    [Agente A — si C-09 ✓ puede ir en paralelo]

GATE 6: C-05 + C-09 + C-11 ✓
  → C-12 trazabilidad-auditoria-persistencia (solo)
```

### Camino crítico (6 changes — mínimo irreducible)

```
C-01 → C-02 → C-03 → C-04 → C-11 → C-12
```

(Reserva → confirmación → cobro → auditoría: el flujo 1 completo más caja y trazabilidad.)

### Plan óptimo con 3 agentes

```
Paso │ Agente A (Agenda core)          │ Agente B (Agenda extendida)       │ Agente C (Clínica/Caja/Aux)
─────┼─────────────────────────────────┼───────────────────────────────────┼────────────────────────────
  1  │ C-01 foundation-setup           │         —                         │         —
  2  │ C-02 pacientes-profesionales    │         —                         │         —
  3  │ C-03 crear-turno-sin-solapamientos (solo, OPSX completo) │ —        │         —
  4  │ C-04 confirmar-turno            │ C-05 reprogramar-turno            │ C-10 odontograma-minimo
  5  │ C-06 cancelar-turno             │ C-07 bloqueos-franja              │         —
  6  │ C-09 lista-espera               │ C-08 sobreturno-explicito         │         —
  7  │ C-11 caja-minima                │         —                         │         —
  8  │ C-12 trazabilidad-auditoria-persistencia │ —                        │         —
```

---

## FASE 0 — Cimientos

### [C-01] `foundation-setup`
- **Estado**: `[ ]` pendiente
- **Scope**: Scaffolding del módulo Python + puertos base, sin lógica de dominio
  - Estructura `domain/`, `application/`, `infrastructure/`, `tests/` según `08_arquitectura_propuesta.md`
  - `pyproject.toml` (Python ≥ 3.11, pytest 8.x, ruff opcional), config pytest
  - `domain/rules.py`: excepción base `DomainError` con campo `code` (`RN-XX-NN`), nunca `None` silencioso
  - `infrastructure/clock.py`: reloj inyectable (puerto) para tests deterministas
  - `infrastructure/memory_repo.py`: repositorio genérico en memoria (dict) + `infrastructure/audit.py` (append en memoria)
  - `.env.example`: `TURNOS_REPO=memory`, `TURNOS_DB_PATH=./data/turnos.db`
  - Tests: smoke de imports + reloj determinista
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/01_vision_y_objetivos.md` §Alcance v1.0
  - `knowledge-base/02_descripcion_general.md` §Stack tecnológico
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-01, §DD-02

---

### [C-02] `pacientes-profesionales`
- **Estado**: `[ ]` pendiente
- **Scope**: Entidades base que todo lo demás referencia + seed mínimo
  - Modelos: `domain/paciente.py` (id, nombre, dni único no vacío, telefono ≥ 6 dígitos, email opcional), `domain/profesional.py` (id, nombre, matricula única, especialidades, sillon_id, horario_base semanal)
  - Value objects: `DNI`, `Matricula` con validación en el borde y código RN
  - Casos de uso alta/baja con RBAC lógico (secretaria CRUD, paciente R propio, sin login — rol como parámetro)
  - Repos en memoria para ambas entidades
  - Seed: 2 profesionales (general sillón A, ortodoncia sillón B, Lun–Vie 9–18) + 3 pacientes con DNI
  - Tests: DNI duplicado/vacío → RN-PA-01, matrícula duplicada → RN-PR-01
- **Dependencias**: C-01
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Paciente, §Profesional
  - `knowledge-base/05_reglas_de_negocio.md` §RN-PA-01, §RN-PR-01
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/08_arquitectura_propuesta.md` §Value objects

---

## FASE 1 — Agenda núcleo (PRIMER change con ciclo OPSX completo)

> `C-03` es el PRIMER change de la épica de Agenda y se implementa con el ciclo OPSX completo (explore → propose → apply → verify → archive). Está acotado a propósito: solo creación con anti-solapamiento. Confirmar, reprogramar, cancelar, bloqueos y sobreturnos son changes propios (C-04 a C-08) y NO entran aquí.

### [C-03] `crear-turno-sin-solapamientos`
- **Estado**: `[ ]` pendiente
- **Scope**: Crear un turno evitando solapamientos por profesional y por sillón — nada más
  - Modelo `domain/turno.py`: id, paciente_id, profesional_id, inicio (datetime), duracion_min, prestacion, estado=`solicitado`, origen=`reserva`
  - Caso de uso `application/agendar.py::solicitar_turno(paciente_id, profesional_id, inicio, duracion_min, prestacion, rol)` → Turno o error de dominio
  - Validaciones: RN-AG-01 (profesional sin dos turnos activos solapados), RN-AG-02 (sillón sin dos turnos activos solapados aunque cambie el profesional), RN-AG-03 (dentro del horario base), RN-AG-04 (duración > 0 y múltiplo de 5), RN-AG-07 (nace en `solicitado`), RN-AG-10 (paciente solo sus turnos)
  - Intervalo semiabierto `[inicio, inicio+duración)`; activos = `solicitado | confirmado` (incluye `origen=sobreturno` como ocupado); turnos adyacentes (fin == inicio) NO solapan
  - Si falla: error explícito con código RN-AG-0X y no se crea nada
  - AuditLog: evento `turno_creado` con actor_rol + timestamp (reloj inyectable)
  - Explícitamente FUERA de este change: confirmar (C-04), reprogramar (C-05), cancelar (C-06), bloqueos RN-AG-05 (C-07), sobreturno RN-AG-06 (C-08)
  - Tests `tests/test_rules_agenda.py`: solape parcial / exacto / contenido / adyacente-OK, mismo sillón distinto profesional, fuera de horario, duración inválida, estado inicial `solicitado`, entrada de audit escrita
- **Dependencias**: C-02
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-01, §RN-AG-02, §RN-AG-03, §RN-AG-04
  - `knowledge-base/06_funcionalidades.md` §US-001
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 (pasos 1–2)
  - `knowledge-base/04_modelo_de_datos.md` §Turno
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03

---

## FASE 2 — Transiciones de turno

> C-04, C-05 y C-06 son paralelos entre sí tras C-03 (los tres operan sobre el turno creado en C-03).

### [C-04] `confirmar-turno`
- **Estado**: `[ ]` pendiente
- **Scope**: Confirmación por secretaria con revalidación de solapamiento (US-002)
  - Caso de uso `application/confirmar.py::confirmar_turno(turno_id, rol)` — solo rol secretaria, solo estado `solicitado` (RN-AG-07; ver IN-01 en `10_preguntas_abiertas.md`)
  - Revalida RN-AG-01/02 al confirmar (el hueco pudo ocuparse entre solicitud y confirmación)
  - `notifier_stub.registrar_recordatorio(turno_id)` — puerto en memoria, sin envío real
  - AuditLog: evento `turno_confirmado` con actor secretaria
  - Tests: rol paciente rechazado, estado no-`solicitado` rechazado, solape aparecido entre solicitar y confirmar, recordatorio registrado
- **Dependencias**: C-03
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-002
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-07, §RN-AG-01, §RN-AG-02
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 (pasos 3–4)
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/10_preguntas_abiertas.md` §IN-01

---

### [C-05] `reprogramar-turno`
- **Estado**: `[ ]` pendiente
- **Scope**: Mover un turno a nuevo horario con trazabilidad del original (US-003)
  - Caso de uso `application/reprogramar.py::reprogramar_turno(turno_id, nuevo_inicio, rol)` — paciente (propios) o secretaria
  - Solo estados `solicitado | confirmado` (RN-AG-08); valida nuevo hueco con RN-AG-01/02/03/04 (+ RN-AG-05 si C-07 archivado)
  - Original pasa a `reprogramado` con enlace `reemplazado_por=nuevo_id`; nuevo nace `solicitado` (o `confirmado` si rol secretaria y original confirmado — resuelve IN-01)
  - Si el nuevo hueco es inválido, el original queda intacto
  - AuditLog: `turno_reprogramado` (original) + `turno_creado` (nuevo, con enlace)
  - Tests: reprogramar cancelado/atendido rechazado, hueco inválido conserva original, enlace original↔nuevo, IN-01 documentada
- **Dependencias**: C-03
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-003
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-08
  - `knowledge-base/07_flujos_principales.md` §Flujo 2
  - `knowledge-base/04_modelo_de_datos.md` §Turno
  - `knowledge-base/10_preguntas_abiertas.md` §IN-01

---

### [C-06] `cancelar-turno`
- **Estado**: `[ ]` pendiente
- **Scope**: Cancelación con motivo que libera el hueco (US-004, sin lista de espera — eso es C-09)
  - Caso de uso `application/cancelar.py::cancelar_turno(turno_id, motivo, rol)` — paciente (propios) o secretaria
  - Motivo obligatorio no vacío; solo turnos activos (`solicitado | confirmado | sobreturno`) — RN-AG-09
  - Emite evento de dominio `hueco_liberado(turno_id, profesional_id, inicio, duracion)` para consumo de C-09; sin compatibles el hueco queda libre visible en disponibilidad
  - AuditLog: evento `turno_cancelado` con motivo + actor
  - Tests: sin motivo rechazado, cancelar ya-cancelado/reprogramado rechazado, evento emitido, audit con motivo
- **Dependencias**: C-03
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-09
  - `knowledge-base/07_flujos_principales.md` §Flujo 3 (paso 1)
  - `knowledge-base/04_modelo_de_datos.md` §Turno

---

## FASE 3 — Reglas de agenda extendida

### [C-07] `bloqueos-franja`
- **Estado**: `[ ]` pendiente
- **Scope**: Bloqueos de agenda que impiden agendar (US-005 + extensión de RN-AG-05 a C-03/C-05)
  - Modelo `domain/bloqueo.py`: id, profesional_id (null = toda la clínica), desde, hasta, motivo — valida `desde < hasta` (RN-AG-05)
  - Caso de uso `application/bloqueos.py::bloquear_franja(profesional_id, desde, hasta, motivo, rol)` — rol secretaria CRUD
  - Extiende `solicitar_turno` y `reprogramar_turno`: rechazan con RN-AG-05 sobre bloqueo vigente (global o del profesional)
  - Seed: 1 bloqueo de ejemplo (feriado global)
  - Tests: `desde >= hasta` rechazado, bloqueo global bloquea a todos, bloqueo por profesional solo al suyo, agendar sobre bloqueo → RN-AG-05
- **Dependencias**: C-03
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-005
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-05
  - `knowledge-base/04_modelo_de_datos.md` §BloqueoFranja
  - `knowledge-base/10_preguntas_abiertas.md` (tabla — SQLite vs memoria no afecta este change)

---

### [C-08] `sobreturno-explicito`
- **Estado**: `[ ]` pendiente
- **Scope**: Sobreturno marcado para urgencias con bypass controlado del anti-solape (US-006)
  - Caso de uso `application/agendar.py::agregar_sobreturno(...)` — exige flag explícito + rol secretaria (RN-AG-06); crea turno con `origen=sobreturno`
  - Bypass SOLO de RN-AG-01/02; mantiene RN-AG-03/04/05; el sobreturno cuenta como ocupado para futuros turnos normales
  - AuditLog: evento `turno_sobreturno_creado` con actor secretaria + justificación
  - Tests: paciente no puede crear sobreturno, sin flag se rechaza con RN-AG-06, sobreturno bloquea hueco posterior normal
- **Dependencias**: C-03, C-07
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-006
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-06
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03

---

## FASE 4 — Dominios adyacentes

> C-09, C-10 y C-11 son paralelos entre sí (dominios independientes). C-10 solo necesita C-02.

### [C-09] `lista-espera`
- **Estado**: `[ ]` pendiente
- **Scope**: Lista de espera FIFO con oferta del primer hueco compatible (US-010)
  - Modelo `domain/lista_espera.py`: id, paciente_id, prestacion, preferencia_profesional opcional, creado_en, estado (`activa | ofrecida | cerrada`)
  - Casos de uso `application/lista_espera.py`: `anotarse(...)` (paciente), `ofrecer_hueco(...)` — primer activo compatible por `creado_en` (prestación + preferencia, RN-LE-01), `aceptar_oferta(...)` crea turno validado por todas las RN-AG (RN-LE-02), expiración pasa al siguiente
  - Consume `hueco_liberado` de C-06; `consultar_disponibilidad(...)` público sin rol requerido
  - Tests: orden FIFO entre compatibles, preferencia filtra, aceptar crea turno validado, oferta expirada → siguiente
- **Dependencias**: C-03, C-06
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-010
  - `knowledge-base/05_reglas_de_negocio.md` §RN-LE-01, §RN-LE-02
  - `knowledge-base/07_flujos_principales.md` §Flujo 3 (pasos 2–3)
  - `knowledge-base/04_modelo_de_datos.md` §ListaEspera
  - `knowledge-base/03_actores_y_roles.md` §Rutas públicas

---

### [C-10] `odontograma-minimo`
- **Estado**: `[ ]` pendiente
- **Scope**: Odontograma básico por paciente con piezas FDI (US-020)
  - Modelo `domain/odontograma.py::PiezaEstado`: paciente_id, pieza (dígito-dos FDI), estado (`sana | cariada | obturada | ausente | tratamiento`)
  - Valida RN-CL-01 (FDI 11–18, 21–28, 31–38, 41–48) y RN-CL-02 (paciente existente); 1 odontograma por paciente, N piezas
  - Caso de uso `registrar_estado_pieza(paciente_id, pieza, estado, rol=odontologo)` — sobrescribe estado previo de la pieza
  - Tests: pieza `19`/`99`/`1` rechazadas, paciente inexistente rechazado, actualización de pieza existente
- **Dependencias**: C-02
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CL-01, §RN-CL-02
  - `knowledge-base/04_modelo_de_datos.md` §PiezaEstado
  - `knowledge-base/01_vision_y_objetivos.md` §Fuera de alcance (qué NO entra)

---

### [C-11] `caja-minima`
- **Estado**: `[ ]` pendiente
- **Scope**: Cobros y señas asociados a turnos con stub de Mercado Pago (US-030)
  - Modelo `domain/cobro.py`: id, turno_id, monto > 0, medio (`efectivo | transferencia | mercado_pago_stub`), fecha, es_seña
  - Caso de uso `application/cobros.py::registrar_cobro(turno_id, monto, medio, es_seña, rol=secretaria)` — rechaza turno cancelado (RN-CA-01), monto ≤ 0 o medio inválido (RN-CA-02); la seña NO confirma el turno (RN-CA-03)
  - Puerto `CobrosPort` con `mercado_pago_stub` en memoria (DD-04)
  - Tests `tests/test_caja.py`: cobro sobre cancelado → RN-CA-01, monto 0/negativo, medio inválido, seña deja estado intacto
- **Dependencias**: C-04, C-06
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-030
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CA-01, §RN-CA-02, §RN-CA-03
  - `knowledge-base/07_flujos_principales.md` §Flujo 4
  - `knowledge-base/04_modelo_de_datos.md` §Cobro
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-04

---

## FASE 5 — Trazabilidad y persistencia

### [C-12] `trazabilidad-auditoria-persistencia`
- **Estado**: `[ ]` pendiente
- **Scope**: Consulta de audit log + adaptador SQLite + cierre E2E del sistema (US-040)
  - Caso de uso `consultar_historial(turno_id, rol)` — admin total, secretaria R, odontólogo R propio (US-040 CA-1: todo cambio de estado tiene entrada con actor + timestamp)
  - `infrastructure/sqlite_repo.py` (sqlite3 stdlib) + switch `TURNOS_REPO=memory|sqlite` vía `TURNOS_DB_PATH`; puertos (repositorio, reloj, notificador, cobros) sin tocar `domain/`
  - Seed: 1 turno confirmado de ejemplo (completa el seed de C-02/C-07)
  - Tests `tests/test_flujos.py` E2E: reserva→confirmación→cancelación→oferta lista de espera; seña no confirma; ruff limpio
  - `reports/` o README con cómo ejecutar el módulo + suite
- **Dependencias**: C-05, C-09, C-11
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-040
  - `knowledge-base/05_reglas_de_negocio.md` §Excepciones globales (audit + reloj)
  - `knowledge-base/08_arquitectura_propuesta.md` §Puertos y adaptadores, §Variables de entorno
  - `knowledge-base/07_flujos_principales.md` (todos los flujos — son los escenarios E2E)
  - `knowledge-base/02_descripcion_general.md` §API interna
