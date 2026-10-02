# Reglas de Negocio

Cada regla tiene código único `RN-{DOMINIO}-{NN}` para trazabilidad en tests y casos de uso.

## Dominio: Agenda (RN-AG)

- **RN-AG-01**: Un profesional no puede tener dos turnos activos solapados — todo intento se rechaza con error de dominio.
- **RN-AG-02**: Un sillón no puede tener dos turnos activos solapados (aunque sean distintos profesionales).
- **RN-AG-03**: El turno debe caer dentro del horario base del profesional; fuera de horario se rechaza.
- **RN-AG-04**: La duración debe ser > 0 y múltiplo de 5 minutos.
- **RN-AG-05**: No se agenda sobre un bloqueo vigente (feriado, vacaciones, franja no laborable); desde < hasta.
- **RN-AG-06**: El sobreturno solo se crea con flag explícito + rol secretaria; queda marcado con `origen=sobreturno`.
- **RN-AG-07**: El turno solicitado por paciente nace en estado `solicitado`; solo secretaria lo confirma.
- **RN-AG-08**: Solo se reprograma un turno en estado `solicitado` o `confirmado`; la reprogramación valida RN-AG-01/02/03/05 y deja el anterior como `reprogramado` (trazabilidad).
- **RN-AG-09**: Solo se cancela un turno activo; la cancelación libera el hueco y dispara oferta a lista de espera.
- **RN-AG-10**: El paciente solo opera sobre sus propios turnos.

## Dominio: Pacientes (RN-PA)

- **RN-PA-01**: DNI único y no vacío; duplicado se rechaza.

## Dominio: Profesionales (RN-PR)

- **RN-PR-01**: Matrícula única; duplicada se rechaza.

## Dominio: Clínica mínima (RN-CL)

- **RN-CL-01**: Pieza en sistema dígito-dos FDI (11–18, 21–28, 31–38, 41–48); otro valor se rechaza.
- **RN-CL-02**: El odontograma pertenece a un paciente existente.

## Dominio: Caja mínima (RN-CA)

- **RN-CA-01**: No se registra cobro sobre turno cancelado.
- **RN-CA-02**: Monto > 0; medio dentro del enum permitido.
- **RN-CA-03**: La seña reserva pero no confirma por sí sola (la confirmación la da secretaria, RN-AG-07).

## Dominio: Lista de espera (RN-LE)

- **RN-LE-01**: Al liberarse un hueco, se ofrece al primer activo compatible (prestación + preferencia); la oferta expira y pasa al siguiente.
- **RN-LE-02**: Aceptar la oferta crea un turno validado por todas las RN-AG.

## Dominio: Excepciones globales

- Todo error de dominio es explícito (excepción o Result con código RN-XX-NN), nunca un `None` silencioso.
- Todo cambio de estado de turno escribe una entrada en AuditLog con actor y timestamp (trazabilidad mínima, base para Ley 26.529 art. 13 a futuro).
- El reloj es inyectable (puerto) para que los tests sean deterministas.
