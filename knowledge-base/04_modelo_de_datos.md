# Modelo de Datos

## Dominios

- **Personas:** pacientes y profesionales (con especialidad y sillón asignado).
- **Agenda:** turnos, bloqueos de franja, sobreturnos, lista de espera.
- **Clínica mínima:** odontograma básico por paciente (pieza + estado).
- **Caja mínima:** cobros asociados a turnos (particular + seña).
- **Auditoría:** eventos de dominio (creación, cambio de estado) con marca temporal.

## ERD (textual)

```
Paciente 1───* Turno *───1 Profesional
Paciente 1───1 Odontograma 1───* PiezaEstado
Turno 1───* Cobro
Profesional 1───* BloqueoFranja
ListaEspera *───1 Paciente (con prestacion + preferencia)
AuditLog * (turno_id, evento, actor, timestamp)
```

Relaciones: un turno pertenece a exactamente un paciente y un profesional; un profesional atiende en un sillón por franja (RN-AG-03); los bloqueos impiden agendar (RN-AG-05).

## Entidades

### Paciente
- Atributos: id (str/uuid), nombre, dni (único), telefono, email (opcional).
- Relaciones: turnos (1-*), odontograma (1-1), lista_espera (0-*).
- Constraints: dni único y no vacío (RN-PA-01); teléfono con formato mínimo de 6 dígitos si se informa.

### Profesional
- Atributos: id, nombre, matricula (única), especialidades (lista), sillon_id, horario_base (franjas semanales).
- Relaciones: turnos (1-*), bloqueos (1-*).
- Constraints: matrícula única (RN-PR-01); un profesional no atiende dos turnos solapados (RN-AG-01).

### Turno
- Atributos: id, paciente_id, profesional_id, inicio (datetime), duracion_min, prestacion, estado (solicitado | confirmado | atendido | ausente | cancelado | reprogramado), origen (reserva | sobreturno).
- Relaciones: cobros (0-*).
- Constraints: duración > 0 y múltiplo de 5 min (RN-AG-04); inicio dentro del horario del profesional y fuera de bloqueos (RN-AG-05); sin solapamiento con otro turno activo del mismo profesional/sillón (RN-AG-01/03); sobreturno solo con flag explícito y confirmación de secretaria (RN-AG-06).

### BloqueoFranja
- Atributos: id, profesional_id (o null = toda la clínica), desde, hasta, motivo.
- Constraints: desde < hasta (RN-AG-05).

### ListaEspera
- Atributos: id, paciente_id, prestacion, preferencia_profesional (opcional), creado_en, estado (activa | ofrecida | cerrada).

### PiezaEstado (odontograma mínimo)
- Atributos: paciente_id, pieza (dígito-dos FDI, ej. "11"–"48"), estado (sana | cariada | obturada | ausente | tratamiento).
- Constraints: pieza válida FDI dígito-dos (RN-CL-01, Ley 26.529 art. 15 inc. f).

### Cobro
- Atributos: id, turno_id, monto (> 0), medio (efectivo | transferencia | mercado_pago_stub), fecha, es_seña (bool).
- Constraints: no se cobra un turno cancelado (RN-CA-01).

### AuditLog
- Atributos: id, turno_id (opcional), evento, actor_rol, detalle, timestamp (reloj inyectable para tests).

## Seed data inicial

- 2 profesionales (ej. odontología general sillón A; ortodoncia sillón B) con horario Lun–Vie 9–18.
- 3 pacientes de prueba con DNI.
- 1 bloqueo de ejemplo (feriado) y 1 turno confirmado de ejemplo.
