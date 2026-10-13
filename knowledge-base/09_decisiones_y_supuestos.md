# Decisiones y Supuestos

Las decisiones del equipo se registran como **DD** o con ID **D-xx**. Las que dependen de validación se marcan **PROVISIONAL**. Los supuestos (SU) remiten a su pregunta en [10_preguntas_abiertas.md](10_preguntas_abiertas.md) (SE-xx = Supuesto del equipo; IF-xx = hallazgo del informe).

## Decisiones documentadas

### D-01 — Stack: Python + FastAPI + pytest + SQLite (PROVISIONAL)
**Decisión**: Backend en Python con FastAPI, tests con pytest y persistencia en SQLite. Estado: **PROVISIONAL**.
**Contexto**: el informe no define stack técnico. Es un trabajo práctico universitario (UTN, Metodología I) de un solo consultorio, y el alcance del primer change es el backend. El `discovery` de nivel superior del archivo de estado menciona PostgreSQL, Docker y JWT; el equipo decidió SQLite provisionalmente (ver IN-01 en 10).
**Alternativas consideradas**: PostgreSQL + Docker; SQLite; otros lenguajes/frameworks no considerados.
**Justificación**: SQLite no requiere servidor ni contenedores, permite tests rápidos y reproducibles y alcanza para la escala supuesta (una sede, varios odontólogos y sillones; SE-16). FastAPI da validación y documentación OpenAPI con poco código; pytest es el estándar de testing en Python.
**Consecuencias / trade-offs aceptados**: un solo escritor a la vez (suficiente para el alcance; ver SE-06); sin restricciones de exclusión por rango en la base (el control de solapamiento vive en el dominio y en una transacción); migración posterior a otro motor requiere cuidar el SQL.
**Cuándo revisar**: pasar a PostgreSQL si aparece concurrencia real de varios usuarios o varias sedes, si hace falta una restricción de exclusión por rango a nivel de base, o si el despliegue requiere un servidor de base de datos compartido.

### D-02 — Arquitectura simple con dominio separado del framework
**Decisión**: cuatro carpetas: `app/domain` (Python puro), `app/api` (FastAPI), `app/db` (SQLite) y `tests`. Sin puertos/adaptadores, sin capa de casos de uso, sin DI frameworks.
**Contexto**: el núcleo del producto son reglas de solapamiento que deben ser verificables con tests.
**Alternativas consideradas**: arquitectura hexagonal completa; todo en los routers.
**Justificación**: la separación mínima permite tests de dominio sin DB ni HTTP, que es lo que el informe resalta como "reglas de negocio verificables" (C.4), sin ceremonia innecesaria para un MVP.
**Trade-offs aceptados**: los routers orquestan (cargar contexto, llamar al dominio, guardar); si crece la lógica de orquestación, se evalúa extraerla más adelante.

### D-03 — Mecanismo de autenticación: pendiente (JWT candidato)
**Decisión**: PROVISIONAL. Se asume token firmado con JWT, con rol en el token. No está decidido (ver SE-17).
**Contexto**: el informe exige autenticación y roles (D.3 #8) pero no el mecanismo.
**Alternativas consideradas**: JWT; sesiones con cookie; token opaco guardado en DB.
**Justificación**: JWT es el candidato por simplicidad en una API sin estado.
**Trade-offs aceptados**: revocación más difícil; se mitiga con duración corta.

### D-04 — MVP acotado a D.3 ítems 1 a 9
**Decisión**: el MVP es exactamente la sección D.3 "Imprescindible (MVP)", ítems 1 a 9. Todo lo de "Diferenciador" y "Etapas posteriores" queda fuera.
**Contexto**: criterio del equipo para el trabajo práctico.
**Justificación**: el informe recomienda ese núcleo; el resto depende de costos o integraciones externas (WhatsApp, Mercado Pago, ARCA).
**Trade-offs aceptados**: sin reserva online ni recordatorios; el paciente no es usuario del sistema.

### D-05 — Reprogramar conserva el mismo turno (mismo id) y lo registra en la auditoría
**Decisión**: reprogramar actualiza el turno existente y deja un registro antes/después en la auditoría, en lugar de crear uno nuevo.
**Contexto**: el informe pide reprogramación como operación propia, no "cancelar y crear" (C.4), conservando el historial (D.3 #5).
**Alternativas consideradas**: turno nuevo vinculado al anterior (encadenado).
**Justificación**: mantiene un identificador estable y un historial lineal. Es una elección del equipo (SE-21).

### D-06 — Fechas como hora local del consultorio, intervalos semiabiertos
**Decisión**: fechas y horas locales del consultorio sin offset; intervalos `[inicio, fin)`.
**Justificación**: simplicidad y permitir turnos contiguos. Ambos son supuestos (SE-05 y SE-10).

### D-07 — Persistencia sin ORM (propuesta)
**Decisión**: PROVISIONAL. Usar el módulo `sqlite3` de la biblioteca estándar con SQL parametrizado, o SQLAlchemy si el equipo lo prefiere (SE-20).
**Justificación**: menos dependencias y control explícito de transacciones; el `discovery` de nivel superior mencionaba SQLAlchemy.

### D-08 — Datos ficticios
**Decisión**: toda semilla, ejemplo y test usa datos ficticios rotulados.
**Contexto**: informe D.3 #7. Sin secretos en el repositorio.

## Supuestos inferidos

Detalle completo y prioridades en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

### SU-01 — Todo turno usa un sillón
**Supuesto**: cada turno ocupa un sillón/box (SE-02).
**Origen**: Supuesto del equipo; el informe habla de doble recurso (C.4) pero no afirma que sea universal.
**Riesgo si es falso**: consultas o tratamientos sin sillón no se podrían cargar.
**Cómo validar**: preguntar a un consultorio real o a la cátedra.

### SU-02 — La necesidad de agenda por sillón es real
**Supuesto**: los consultorios necesitan controlar el sillón como recurso (SE-01).
**Origen**: Supuesto del equipo; el informe lo plantea como oportunidad (C.4) sin validación con usuarios.
**Riesgo si es falso**: complejidad sin beneficio.
**Cómo validar**: entrevista breve a un odontólogo o recepcionista.

### SU-03 — Un paciente no puede tener dos turnos a la vez
**Supuesto**: RN-TUR-12 (SE-03).
**Origen**: Supuesto del equipo.
**Riesgo si es falso**: se rechazarían turnos legítimos (por ejemplo, tratamiento en dos boxes seguidos).
**Cómo validar**: confirmar con la cátedra o el cliente.

### SU-04 — Sin sobreturnos
**Supuesto**: RN-TUR-11 (SE-04).
**Origen**: Supuesto del equipo; el informe no evidencia sobreturnos en ningún sistema (C.3.3).
**Riesgo si es falso**: recepción no podría encajar urgencias.
**Cómo validar**: preguntar si el consultorio sobrecarga la agenda.

### SU-05 — Intervalos semiabiertos y contiguos válidos
**Supuesto**: RN-TUR-04 (SE-10).
**Origen**: Supuesto del equipo.
**Riesgo si es falso**: hace falta margen entre turnos (SE-07).
**Cómo validar**: confirmar con el cliente.

### SU-06 — Una sede, varios odontólogos y sillones
**Supuesto**: escala del MVP (SE-16).
**Origen**: Supuesto del equipo; multisede es etapa posterior en el informe.
**Riesgo si es falso**: SQLite deja de ser suficiente (revisar D-01).
**Cómo validar**: confirmar con la cátedra.

### SU-07 — Matriz de permisos RBAC
**Supuesto**: la matriz de [03](03_actores_y_roles.md) (SE-12).
**Origen**: Supuesto del equipo; el informe define solo los tres roles.
**Riesgo si es falso**: permisos demasiado restrictivos o laxos.
**Cómo validar**: revisar con el equipo y la cátedra.
