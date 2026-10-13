# Modelo de Datos

Modelo propuesto para el MVP (informe D.3 #1 a #9). Los nombres de tablas y columnas son propuesta del equipo (**Supuesto del equipo**); lo que el informe exige es: profesionales, sillones/boxes, prestaciones con duración, horarios de atención, bloqueos, turnos, pacientes con obra social como dato, usuarios con rol y auditoría (quién, qué, cuándo).

## Dominios

| Dominio | Contenido |
|---------|-----------|
| Recursos | Profesional, Sillón/box, Prestación |
| Disponibilidad | Horario de atención, Bloqueo |
| Pacientes | Paciente (con obra social/prepaga como dato) |
| Agenda | Turno |
| Acceso | Usuario (rol) |
| Trazabilidad | Registro de auditoría de turnos |

## ERD

```
Usuario (rol, profesional_id?) ---- 0..1 ---- Profesional
Profesional 1 ---- * HorarioAtencion
Profesional 1 ---- * Turno * ---- 1 Sillon
Prestacion  1 ---- * Turno * ---- 1 Paciente
Bloqueo * ---- 1 (Profesional | Sillon)     [alcance + recurso_id]
Turno 1 ---- * AuditoriaTurno
```

## Convenciones

- Fecha y hora: instante local del consultorio (zona de Argentina) guardado como texto ISO 8601 sin offset; ver supuesto de zona horaria/DST en [10_preguntas_abiertas.md](10_preguntas_abiertas.md) (SE).
- Intervalos de turno: `[inicio, fin)` semiabierto (RN-TUR-04).
- Borrado: no se borra físicamente lo que tenga turnos; se desactiva (`activo = 0`) (SE).
- Todos los datos de ejemplo son ficticios.

## Entidades

### Profesional
- `id` (entero, PK), `nombre` (texto), `apellido` (texto), `matricula` (texto, opcional; ficticia en ejemplos), `activo` (bool).
- Relaciones: 1..* HorarioAtencion, 1..* Turno.
- Constraints: `nombre` y `apellido` no vacíos.

### Sillon (sillón o box)
- `id` (PK), `nombre` (texto, ej. "Sillón 1"), `activo` (bool).
- Relaciones: 1..* Turno, 0..* Bloqueo (alcance sillón).
- Constraints: `nombre` único.

### Prestacion
- `id` (PK), `nombre` (texto, ej. "Consulta ficticia"), `duracion_minutos` (entero > 0), `activa` (bool).
- La duración del turno la define la prestación (informe D.3 #1 y #3).
- Constraints: `duracion_minutos > 0`; `nombre` único.

### HorarioAtencion
- `id` (PK), `profesional_id` (FK), `dia_semana` (0 = lunes ... 6 = domingo), `hora_desde` (HH:MM), `hora_hasta` (HH:MM).
- Constraints: `hora_desde < hora_hasta`; un profesional puede tener varias franjas por día (por ejemplo mañana y tarde); las franjas del mismo día no se superponen (SE).
- Índice: (`profesional_id`, `dia_semana`).

### Bloqueo
- `id` (PK), `alcance` ("profesional" | "sillon"), `recurso_id` (id del profesional o del sillón según alcance), `inicio` (datetime), `fin` (datetime), `motivo` (texto: vacaciones, feriado, mantenimiento del sillón; informe D.3 #2).
- Constraints: `inicio < fin`.
- Índice: (`alcance`, `recurso_id`, `inicio`).

### Paciente
- `id` (PK), `nombre`, `apellido`, `dni` (texto), `telefono` (opcional), `obra_social` (texto, opcional), `nro_afiliado` (texto, opcional).
- La obra social o prepaga se guarda como dato, sin liquidación (informe D.3 #7).
- Constraints: `dni` único (SE).
- Datos siempre ficticios en pruebas (informe D.3 #7).

### Turno
- `id` (PK), `paciente_id` (FK), `profesional_id` (FK), `sillon_id` (FK, obligatorio: SE "todo turno usa un sillón"), `prestacion_id` (FK), `inicio` (datetime), `fin` (datetime, = inicio + duración de la prestación, calculado por el dominio y guardado), `estado` ("reservado" | "cancelado"), `creado_por` (usuario_id), `creado_en`.
- Estados del MVP: solo `reservado` y `cancelado` (SE). Los estados confirmado, atendido y ausente aparecen como oportunidad en C.4 pero no en D.3, y quedan para la siguiente iteración.
- Constraints: `inicio < fin`; `fin - inicio = duracion` de la prestación al momento de crear.
- Índices: (`profesional_id`, `inicio`), (`sillon_id`, `inicio`), (`paciente_id`, `inicio`).
- Solo los turnos en estado `reservado` ocupan agenda (RN-TUR-08).

### AuditoriaTurno
- `id` (PK), `turno_id` (FK), `accion` ("crear" | "cancelar" | "reprogramar"), `usuario_id` (FK; quién), `ocurrio_en` (datetime; cuándo), `antes` (JSON o texto; qué, valores previos, nulo al crear), `despues` (JSON o texto; qué, valores nuevos).
- Solo se inserta, nunca se actualiza ni se borra (RN-AUD-02).
- Cubre "quién, qué y cuándo" (informe D.3 #9) y el historial de reprogramaciones (D.3 #5).
- Retención y quién la lee: preguntas abiertas del informe (C.3.4).

### Usuario
- `id` (PK), `username` (único), `password_hash` (texto, nunca la contraseña), `rol` ("administracion" | "recepcion" | "odontologo"), `profesional_id` (FK, opcional; obligatorio si el rol es odontólogo, SE), `activo` (bool).

## Seed data inicial (TODO FICTICIO)

Datos mínimos para desarrollo y tests. Ningún dato es real; no se versionan contraseñas reales (el usuario inicial se crea con variables de entorno placeholder, ver [08](08_arquitectura_propuesta.md)).

| Entidad | Ejemplo ficticio |
|---------|------------------|
| Profesional | "Odontólogo Ficticio A", matrícula "0001 (ficticia)"; "Odontóloga Ficticia B" |
| Sillón | "Sillón 1", "Sillón 2" |
| Prestación | "Consulta ficticia" 30 min; "Limpieza ficticia" 45 min; "Tratamiento ficticio" 60 min |
| Horario | lunes a viernes 09:00-13:00 y 14:00-18:00 para ambos profesionales (ficticio) |
| Paciente | "Paciente Ficticio 1", DNI "00000001 (ficticio)", "Obra Social Ficticia A"; "Paciente Ficticio 2", DNI "00000002 (ficticio)", sin obra social |
| Usuario | `admin_demo`, `recepcion_demo`, `odontologo_demo` (rol correspondiente; contraseña definida por variable de entorno en cada entorno, no en el repo) |
