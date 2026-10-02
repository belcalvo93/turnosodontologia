# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|---|---|---|
| Paciente | Persona que reserva y recibe atención | Llama a casos de uso: solicitar, confirmar, cancelar, reprogramar sus turnos |
| Secretaria (recepción) | Gestiona la agenda operativa | Agenda, bloquea franjas, registra ausencias, opera lista de espera |
| Odontólogo | Profesional que atiende | Consulta su agenda del día, registra resultado del turno (atendido/ausente) |
| Admin (opcional v1.0) | Liquida y audita | Lee reportes y audit log; sin permisos clínicos |

**Suposición:** en v1.0 no hay autenticación real; los roles se modelan como parámetro de contexto en los casos de uso para validar permisos (RBAC lógico, no login).

## RBAC — Matriz de permisos

| Rol | Pacientes | Profesionales | Turnos | Bloqueos | Lista de espera | Caja | Audit log |
|---|---|---|---|---|---|---|---|
| Paciente | R propio | R | CRU propios (*) | — | R propia / anotarse | R propios pagos | — |
| Secretaria | CRUD | R | CRUD | CRUD | CRUD | CR | R |
| Odontólogo | R | R propio | RU (sus turnos) | R | R | R | R propio |
| Admin | R | R | R | R | R | R + reportes | R total |

(*) El paciente solo opera sobre sus propios turnos; no puede agendar sobre bloqueos ni crear sobreturnos.

## Rutas públicas

Sin interfaz gráfica no hay rutas HTTP. Equivalentes "públicos" del módulo (sin rol requerido): `solicitar_turno` y `consultar_disponibilidad` — ambos solo lectura/creación pendiente de confirmación por secretaria (RN-AG-07).
