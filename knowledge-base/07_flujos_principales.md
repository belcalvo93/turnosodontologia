# Flujos Principales

## Flujo 1: Reserva y confirmación

**Disparador**: el paciente solicita un turno.
**Actor**: paciente, luego secretaria.

**Pasos**:
1. Paciente invoca `solicitar_turno` con profesional, inicio, duración y prestación.
2. El dominio valida RN-AG-01/02/03/04/05 y crea el turno en `solicitado` + AuditLog.
3. Secretaria revisa y ejecuta `confirmar_turno` (revalida solapamiento).
4. El notificador stub registra el recordatorio programado (sin envío real).

**Casos de error**:
- Solapamiento → se rechaza con RN-AG-01/02 y no se crea nada.
- Fuera de horario o sobre bloqueo → RN-AG-03/RN-AG-05.
- Paciente duplicado por DNI → RN-PA-01 al dar de alta.

## Flujo 2: Reprogramación autónoma

**Disparador**: el paciente no puede asistir.
**Actor**: paciente.

**Pasos**:
1. Paciente invoca `reprogramar_turno` con nuevo inicio.
2. El dominio valida el nuevo hueco con todas las RN-AG.
3. El turno viejo pasa a `reprogramado` (con enlace) y nace el nuevo en `solicitado` o `confirmado` según rol.
4. AuditLog registra ambos movimientos.

**Casos de error**:
- Nuevo hueco inválido → se conserva el turno original intacto.

## Flujo 3: Cancelación con lista de espera

**Disparador**: cancelación con motivo.
**Actor**: paciente o secretaria.

**Pasos**:
1. Se ejecuta `cancelar_turno`; el turno pasa a `cancelado`.
2. El motor de lista de espera busca el primer activo compatible (RN-LE-01).
3. Se emite oferta; si se acepta, se crea turno validado; si expira, pasa al siguiente.

```
Paciente → Application → Domain (valida RN-AG) → Repo (guarda) → AuditLog
                                                      └── ListaEspera → oferta → nuevo Turno
```

**Casos de error**:
- Sin compatibles → el hueco queda libre y visible en disponibilidad.

## Flujo 4: Cobro mínimo

**Disparador**: seña o pago de la consulta.
**Actor**: secretaria.

**Pasos**:
1. Secretaria invoca `registrar_cobro` con turno, monto y medio.
2. El dominio valida RN-CA-01/02 y guarda el cobro.
3. La seña no confirma por sí sola (RN-CA-03).

**Casos de error**:
- Turno cancelado o monto ≤ 0 → rechazo con código RN.
