# Actores y Roles

El informe (D.3 #8) establece tres roles para el MVP: **administración, recepción y odontólogo**. No define la matriz de permisos. Por eso cada permiso de esta matriz que no esté respaldado explícitamente por el informe se marca **Supuesto del equipo** (SE) y se valida en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

## Actores del sistema

| Actor | Descripción | Cómo interactúa | Respaldo |
|-------|-------------|-----------------|----------|
| Administración | Responsable de la configuración del consultorio | Gestiona profesionales, sillones, prestaciones, horarios, bloqueos y usuarios; consulta auditoría | Rol: informe D.3 #8. Tareas: SE |
| Recepción | Personal que da y modifica turnos | Carga pacientes; crea, cancela y reprograma turnos; consulta agendas | Rol: informe D.3 #8 (el informe cita la cuenta de recepcionista de AgendaPro como referencia, A.8). Tareas: SE |
| Odontólogo | Profesional que atiende | Consulta su agenda diaria y semanal | Rol: informe D.3 #8. Tareas: SE |
| Paciente | Persona atendida | **No es usuario del sistema en el MVP**: es un dato (reserva online y confirmación por enlace son siguiente iteración, D.3) | Informe D.3 (diferenciador) |

## RBAC — Matriz de permisos

Leyenda: C = crear, L = leer/ver, E = editar, B = baja/desactivar, — = sin acceso.
Todos los permisos de la tabla son **Supuesto del equipo** salvo la existencia de los tres roles y la exigencia de auditoría (informe D.3 #8 y #9).

| Recurso / acción | Administración | Recepción | Odontólogo | Respaldo |
|------------------|:--------------:|:---------:|:----------:|----------|
| Profesionales | C L E B | L | L | SE |
| Sillones/boxes | C L E B | L | L | SE |
| Prestaciones | C L E B | L | L | SE |
| Horarios de atención | C L E B | L | L (propios) | SE |
| Bloqueos (profesional o sillón) | C L B | L | L | SE |
| Pacientes | C L E | C L E | L (de sus turnos) | SE |
| Turno: crear | sí | sí | — | SE |
| Turno: cancelar (solo futuros) | sí | sí | — | SE |
| Turno: reprogramar (solo futuros) | sí | sí | — | SE |
| Agenda: ver (diaria/semanal) | todas | todas | solo la propia | SE |
| Auditoría: leer | sí | — | — | SE (quién lee: pregunta abierta del informe, C.3.4) |
| Usuarios y roles | C L E B | — | — | SE |
| Auditoría: escribir | solo el sistema, nunca un rol | idem | idem | Informe D.3 #9 (se registra siempre) |

Notas:
- El registro de auditoría es de solo agregado: ningún rol lo edita ni lo borra (SE, coherente con D.3 #9 y C.4).
- Si el odontólogo debe poder crear turnos propios o bloquear su propia agenda: pregunta abierta (ver 10).
- Un usuario con rol odontólogo se vincula a un profesional (campo `profesional_id` en usuario; SE).

## Rutas públicas

Sin autenticación (propuesta, SE):
- `POST /auth/login`
- `GET /health`
- Documentación OpenAPI de FastAPI (`/docs`) solo en entorno de desarrollo.

Todo lo demás exige autenticación. La reserva pública por enlace sin registro queda fuera del MVP (informe D.3, diferenciador).
