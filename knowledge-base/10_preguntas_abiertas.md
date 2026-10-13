# Preguntas Abiertas

Este archivo separa con claridad dos orígenes:

- **IF-xx — Hallazgo del informe**: figura textualmente en `docs/discovery/informe-discovery.md` (se cita la sección). Antes de rotular un ítem así se verificó con búsqueda en el informe.
- **SE-xx — Supuesto del equipo**: riesgo, supuesto o pregunta que **no** figura en el informe; lo plantea el equipo al armar la KB. No debe citarse como hallazgo del informe.

Prioridad: alta (bloquea el primer change), media (hay que decidirlo durante la implementación), baja (puede esperar a una etapa posterior).

## Inconsistencias detectadas

### IN-01 — Stack: base de datos y despliegue
**Estado del proyecto (`discovery` de nivel superior) dice**: stack Python, FastAPI, JWT, SQLAlchemy, PostgreSQL y Docker.
**Decisión provisional del equipo dice**: Python + FastAPI + pytest + SQLite (D-01).
**El informe**: no define stack técnico.
**Impacto**: cambia la configuración del entorno (Docker o no), el soporte de concurrencia y la forma de acceder a datos.
**Resolución propuesta**: seguir con SQLite como decisión provisional (D-01), con criterios de revisión escritos; JWT queda como candidato (D-03); ORM a definir (D-07).

### IN-02 — Reglas del estado que no están en el informe
**El `discovery` de nivel superior del estado incluye**: sin solapamiento por paciente, intervalos semiabiertos, sin sobreturnos, y "anticipación mínima" como opcional.
**El informe**: no trae textualmente las tres primeras; la anticipación mínima aparece solo como diferenciador (D.3).
**Impacto**: podrían presentarse como hallazgos del informe sin serlo.
**Resolución propuesta**: tratarlas como Supuesto del equipo (SE-03, SE-10, SE-04, SE-08), tal como figura en [05](05_reglas_de_negocio.md).

### IN-03 — Usuarios del estado vs. odontólogo con agenda propia
**El estado dice**: usuarios administración, recepción y odontólogo.
**El informe**: fija los mismos tres roles (D.3 #8) sin permisos.
**Impacto**: ninguno en roles; los permisos son SE-12.
**Resolución propuesta**: validar la matriz de 03.

## A. Hallazgos del informe (No evidenciado / vacíos de mercado)

| ID | Pregunta / hallazgo | Fuente en el informe | Prioridad | Bloquea | Decisor |
|----|---------------------|----------------------|-----------|---------|---------|
| IF-01 | Facturación electrónica ARCA: ningún producto odontológico especializado la evidencia. ¿Se incorporará y cuándo? | C.3 punto 1; D.3 Etapas posteriores | Baja | Etapa posterior | Equipo / cátedra |
| IF-02 | Liquidación a obras sociales y prepagas: no evidenciada. ¿Para qué se usará el dato de obra social que el MVP guarda (futura liquidación, filtros, solo informativo)? Define cómo se modela hoy | C.3 punto 1; C.4 (último punto); D.3 #7 y Etapas posteriores | Media | Diseño de la entidad Paciente | Equipo / cátedra |
| IF-03 | Lista de espera: no evidenciada en ninguno de los 18 sistemas. ¿Se ofrece el hueco liberado automáticamente? | C.3 punto 3; C.4; D.3 Diferenciador | Baja | Siguiente iteración | Equipo |
| IF-04 | Sobreturnos: no evidenciados en ningún sistema. ¿El consultorio los necesita y quién puede autorizarlos? (el MVP asume que no, RN-TUR-11) | C.3 punto 3; A.2 | Media | RN-TUR-03/11 | Equipo / cátedra |
| IF-05 | Exportación de datos: no evidenciada en ningún sistema (Dentalink documenta solo importación). ¿Qué formato y quién exporta? | C.3 punto 4; A.8; D.3 Diferenciador | Baja | Siguiente iteración | Equipo |
| IF-06 | Auditoría: no evidenciada en ningún sistema. ¿Qué alcance (solo turnos o también pacientes y recursos), cuánto tiempo se retiene y quién la lee? El MVP audita turnos (quién, qué, cuándo) | C.3 punto 4; C.4; D.3 #9; A.8 | Alta | RN-AUD-01/02, permisos de lectura | Equipo / cátedra |
| IF-07 | Normativa: Ley 27.706 de historia clínica digital y Decreto 393/2023 (exigencia de trazabilidad), más Leyes 25.326 (datos personales) y 26.529 (derechos del paciente). ¿Aplican al agregar historia clínica o datos reales? ¿La auditoría del MVP prepara esa trazabilidad? | C.3 punto 6; A.9 (Medicloud); D.3 Etapas posteriores | Media | Alcance de datos reales y de historia clínica | Equipo / cátedra |
| IF-08 | Costo de WhatsApp (API oficial con cargos de Meta además de la plataforma): condiciona recordatorios | Resumen ejecutivo, hallazgo 4; A.10 (Wati) | Baja | Etapa posterior | Equipo |
| IF-09 | La evidencia de competidores es mayormente comercial (afirmaciones del proveedor). Las conclusiones del informe miden evidencia pública, no calidad real | Resumen ejecutivo, hallazgo 1; Nota metodológica | Baja | — | Equipo |
| IF-10 | Anticipación mínima configurable para cancelar o reprogramar figura como función del diferenciador (siguiente iteración); no hay regla de plazo en el MVP. (Qué valor por defecto o si existe plazo mínimo en el MVP es SE-08) | D.3 Diferenciador | Media | RN-TUR-09 | Equipo / cátedra |

## B. Supuestos y riesgos del equipo (NO figuran en el informe)

Cada ítem se buscó en el informe antes de rotularlo; ninguno aparece textualmente. Todos son **Supuesto del equipo**.

| ID | Supuesto / pregunta / riesgo | Prioridad | Bloquea | Decisor | Regla relacionada |
|----|------------------------------|-----------|---------|---------|-------------------|
| SE-01 | La necesidad de agenda por sillón no fue validada con usuarios reales (el informe la plantea como oportunidad, C.4, sin entrevistas) | Alta | Justificación del núcleo del MVP | Equipo / cátedra | RN-TUR-02/03 |
| SE-02 | Todo turno usa un sillón (sin turnos "sin sillón") | Alta | Modelo de Turno (sillon_id obligatorio) | Equipo / cátedra | RN-TUR-02 |
| SE-03 | Un paciente no puede tener dos turnos superpuestos (el informe no lo menciona) | Media | RN-TUR-12 | Equipo / cátedra | RN-TUR-12 |
| SE-04 | Sin sobreturnos, ni siquiera con permiso (el informe solo dice que no están evidenciados, IF-04) | Media | RN-TUR-11 | Equipo / cátedra | RN-TUR-11 |
| SE-05 | Zona horaria y cambios de horario (DST): se asumen horas locales del consultorio sin offset; Argentina hoy no usa horario de verano, pero un cambio normativo o un cliente en otra zona rompe el supuesto | Media | Tipo de dato de fechas | Equipo | D-06 |
| SE-06 | Concurrencia en reservas simultáneas: dos recepcionistas reservando el mismo hueco. SQLite serializa escrituras; hay que validar y escribir en una sola transacción | Alta | Diseño de repositorio y tests API | Equipo | RN-TUR-03 |
| SE-07 | Margen de limpieza o preparación entre turnos del mismo sillón: el MVP no lo impone (se incluye en la duración de la prestación) | Baja | RN-TUR-13 | Equipo / cátedra | RN-TUR-13 |
| SE-08 | Anticipación mínima para cancelar: el informe la lista como función de siguiente iteración (IF-10); la parte supuesta es que el MVP no impone ningún plazo más allá de "turno futuro" | Media | RN-TUR-09 | Equipo / cátedra | RN-TUR-09 |
| SE-09 | Turnos ya existentes cuando se crea un bloqueo que los cubre: ¿se cancelan, se listan para reprogramar, se rechaza el bloqueo? Propuesta del MVP: listar y no cancelar automáticamente | Alta | Flujo 5 de 07 | Equipo / cátedra | RN-TUR-05 |
| SE-10 | Intervalos semiabiertos `[inicio, fin)`: turnos contiguos son válidos (el informe no lo dice literalmente) | Alta | RN-TUR-04 | Equipo | RN-TUR-04 |
| SE-11 | Solo se cancelan o reprograman turnos futuros (el informe no define esta restricción) | Media | RN-TUR-09 | Equipo / cátedra | RN-TUR-09 |
| SE-12 | Matriz RBAC completa (el informe define solo los tres roles). Incluye: odontólogo ve solo su agenda; ¿puede el odontólogo bloquear su agenda o crear turnos propios? | Alta | Autorización de rutas | Equipo / cátedra | RN-ACC-02/03 |
| SE-13 | La auditoría es de solo agregado y se confirma en la misma transacción que el cambio | Media | RN-AUD-02/03 | Equipo | RN-AUD-02/03 |
| SE-14 | Un turno debe entrar completo en una franja de atención (no cruza el corte de mediodía) | Media | RN-PRO-02 | Equipo | RN-PRO-02 |
| SE-15 | DNI único por paciente (¿y pacientes extranjeros sin DNI?) | Baja | Esquema de Paciente | Equipo | RN-PAC-02 |
| SE-16 | Escala: una sede, varios odontólogos y sillones (multisede es etapa posterior en el informe, pero la escala objetivo del MVP no figura) | Media | D-01 (SQLite) | Equipo / cátedra | D-01 |
| SE-17 | Mecanismo de autenticación: JWT es candidato, no decidido (alternativas: sesión, token opaco) | Media | Seguridad del primer change | Equipo | D-03 |
| SE-18 | Todo profesional puede realizar cualquier prestación (no hay tabla de prestaciones habilitadas por profesional) | Media | Modelo de datos | Equipo / cátedra | RN-TUR-01 |
| SE-19 | Estados del turno en el MVP: solo reservado y cancelado (el informe menciona confirmado, atendido y ausente como oportunidad en C.4 pero no en D.3) | Media | Estado de Turno | Equipo | RN-TUR-14 |
| SE-20 | Acceso a datos: `sqlite3` estándar vs SQLAlchemy | Baja | Estructura de `app/db` | Equipo | D-07 |
| SE-21 | Reprogramar mantiene el mismo id de turno (alternativa: turno nuevo encadenado) | Baja | Modelo de auditoría | Equipo | RN-TUR-07, D-05 |
| SE-22 | Stack provisional: SQLite en lugar de PostgreSQL/Docker (ver IN-01). Revisar si hay concurrencia real o necesidad de despliegue compartido | Media | D-01 | Equipo / cátedra | D-01 |
| SE-23 | Fecha de entrega del trabajo práctico sin definir (consta en el estado del proyecto, no en el informe) | Baja | Planificación | Equipo | — |

## Resumen para decisiones del primer change

Las preguntas **alta** que conviene resolver antes de implementar: IF-06 (alcance de auditoría), SE-01, SE-02, SE-06, SE-09, SE-10 y SE-12.
