# Funcionalidades

Organizadas por épica e historias de usuario (US-NNN).

## Épica 1: Gestión de turnos

### US-001 — Solicitar turno
**Como** paciente **Quiero** solicitar un turno (profesional, fecha, prestación) **Para** asegurar mi atención.
**Criterios de aceptación**:
- [ ] CA-1 Valida RN-AG-01/02/03/04/05; si falla, error con código RN.
- [ ] CA-2 Crea el turno en estado `solicitado` (RN-AG-07).
- [ ] CA-3 Escribe AuditLog.
**Reglas relacionadas**: RN-AG-01, RN-AG-02, RN-AG-03, RN-AG-04, RN-AG-05, RN-AG-07, RN-AG-10.

### US-002 — Confirmar turno
**Como** secretaria **Quiero** confirmar un turno solicitado **Para** comprometer el sillón.
**Criterios de aceptación**:
- [ ] CA-1 Solo rol secretaria; solo estado `solicitado`.
- [ ] CA-2 Revalida solapamiento al confirmar.
**Reglas relacionadas**: RN-AG-01, RN-AG-02, RN-AG-07.

### US-003 — Reprogramar turno
**Como** paciente o secretaria **Quiero** mover un turno a nueva fecha **Para** adaptarme a imprevistos.
**Criterios de aceptación**:
- [ ] CA-1 Valida nuevo horario con todas las RN-AG.
- [ ] CA-2 El turno original pasa a `reprogramado` con enlace al nuevo.
**Reglas relacionadas**: RN-AG-08.

### US-004 — Cancelar turno y liberar hueco
**Como** paciente o secretaria **Quiero** cancelar con motivo **Para** liberar el sillón.
**Criterios de aceptación**:
- [ ] CA-1 Pide motivo; cambia a `cancelado`.
- [ ] CA-2 Dispara oferta a lista de espera (RN-LE-01).
**Reglas relacionadas**: RN-AG-09, RN-LE-01.

### US-005 — Bloquear franja
**Como** secretaria **Quiero** bloquear feriados/vacaciones **Para** que nadie reserve ahí.
**Criterios de aceptación**:
- [ ] CA-1 Valida desde < hasta; admite bloqueo global o por profesional.
**Reglas relacionadas**: RN-AG-05.

### US-006 — Sobreturno explícito
**Como** secretaria **Quiero** crear un sobreturno marcado **Para** atender urgencias.
**Criterios de aceptación**:
- [ ] CA-1 Exige flag + rol secretaria; queda `origen=sobreturno`.
**Reglas relacionadas**: RN-AG-06.

## Épica 2: Lista de espera

### US-010 — Anotarse y recibir oferta
**Como** paciente **Quiero** anotarme y que me ofrezcan el primer hueco compatible **Para** adelantar mi atención.
**Criterios de aceptación**:
- [ ] CA-1 Orden FIFO por `creado_en` entre compatibles.
- [ ] CA-2 Aceptar crea turno validado.
**Reglas relacionadas**: RN-LE-01, RN-LE-02.

## Épica 3: Clínica mínima

### US-020 — Registrar odontograma básico
**Como** odontólogo **Quiero** cargar pieza/estado en dígito-dos **Para** dejar constancia mínima.
**Criterios de aceptación**:
- [ ] CA-1 Valida pieza FDI y paciente existente.
**Reglas relacionadas**: RN-CL-01, RN-CL-02.

## Épica 4: Caja mínima

### US-030 — Registrar cobro o seña
**Como** secretaria **Quiero** registrar un cobro asociado al turno **Para** conciliar caja.
**Criterios de aceptación**:
- [ ] CA-1 Rechaza cobro sobre turno cancelado; monto > 0.
**Reglas relacionadas**: RN-CA-01, RN-CA-02, RN-CA-03.

## Épica 5: Trazabilidad

### US-040 — Consultar audit log
**Como** admin **Quiero** ver el historial de un turno **Para** auditar cambios.
**Criterios de aceptación**:
- [ ] CA-1 Cada cambio de estado tiene entrada con actor y timestamp.
