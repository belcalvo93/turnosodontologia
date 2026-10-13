# Funcionalidades

Organizadas por épica e historia de usuario (US-NNN). Las épicas del MVP corresponden uno a uno con los ítems 1 a 9 de la sección **D.3 "Imprescindible (MVP)"** del informe. Lo que figura en "Diferenciador" y "Etapas posteriores" está en la sección final **Funcionalidades NO MVP** y nunca forma parte del MVP.

Los criterios de aceptación son propuesta del equipo; los datos de ejemplo son ficticios.

---

# PARTE 1 — MVP (informe D.3, ítems 1 a 9)

## Épica 1: Profesionales, sillones y prestaciones (D.3 #1)

### US-001 — Gestionar profesionales
**Como** administración
**Quiero** dar de alta, editar y desactivar profesionales
**Para** poder asignarles turnos

**Criterios de aceptación**:
- [ ] Se crea un profesional con nombre y apellido.
- [ ] Un profesional desactivado no acepta turnos nuevos y conserva los históricos.
- [ ] Recepción y odontólogo solo pueden listarlos.

**Reglas relacionadas**: RN-REC-03, RN-ACC-02

### US-002 — Gestionar sillones o boxes
**Como** administración
**Quiero** dar de alta, editar y desactivar sillones o boxes
**Para** agendarlos como recurso de cada turno

**Criterios de aceptación**:
- [ ] Se crea un sillón con nombre único.
- [ ] Un sillón desactivado no acepta turnos nuevos.

**Reglas relacionadas**: RN-REC-01, RN-REC-03, RN-TUR-02

### US-003 — Gestionar prestaciones con duración
**Como** administración
**Quiero** definir prestaciones con su duración en minutos
**Para** que el turno tome la duración de la prestación

**Criterios de aceptación**:
- [ ] Se crea una prestación con nombre y duración mayor que cero.
- [ ] Duración 0 o negativa devuelve error de validación.

**Reglas relacionadas**: RN-REC-01, RN-TUR-01

## Épica 2: Horarios y bloqueos (D.3 #2)

### US-004 — Definir horarios de atención por profesional
**Como** administración
**Quiero** cargar los días y franjas horarias de cada profesional
**Para** que no se den turnos fuera de su horario

**Criterios de aceptación**:
- [ ] Se cargan una o más franjas por día de la semana.
- [ ] Una franja con hora_desde >= hora_hasta es inválida.

**Reglas relacionadas**: RN-PRO-01, RN-PRO-02

### US-005 — Bloquear horarios de profesional o sillón
**Como** administración
**Quiero** bloquear intervalos de un profesional (vacaciones, feriados) o de un sillón (mantenimiento)
**Para** que no se den turnos en esos intervalos

**Criterios de aceptación**:
- [ ] Se crea un bloqueo con alcance, recurso, inicio, fin y motivo.
- [ ] Un turno que se superpone con un bloqueo del profesional o del sillón es rechazado.
- [ ] Se puede eliminar un bloqueo y el horario vuelve a estar disponible.
- [ ] Qué pasa con turnos ya existentes dentro del bloqueo nuevo: pregunta abierta (SE-09), el MVP los reporta pero no los cancela automáticamente (propuesta).

**Reglas relacionadas**: RN-REC-02, RN-TUR-05

## Épica 3: Crear turno sin solapamientos (D.3 #3)

### US-006 — Crear un turno
**Como** recepción
**Quiero** crear un turno eligiendo paciente, profesional, sillón, prestación e inicio
**Para** reservar sin superposiciones

**Criterios de aceptación**:
- [ ] El fin se calcula como inicio + duración de la prestación.
- [ ] Si el profesional tiene otro turno activo que se superpone, responde 409.
- [ ] Si el sillón tiene otro turno activo que se superpone, responde 409.
- [ ] Turnos contiguos (uno termina cuando empieza el otro) son aceptados.
- [ ] Fuera del horario del profesional o dentro de un bloqueo responde 409 con mensaje claro (RN-GLO-01).
- [ ] Se registra auditoría de la creación.

**Reglas relacionadas**: RN-TUR-01 a RN-TUR-05, RN-TUR-12, RN-AUD-01

## Épica 4: Cancelar turno (D.3 #4)

### US-007 — Cancelar un turno liberando el horario
**Como** recepción
**Quiero** cancelar un turno futuro
**Para** liberar el horario del profesional y del sillón

**Criterios de aceptación**:
- [ ] El turno pasa a estado cancelado y deja de ocupar agenda.
- [ ] Un turno pasado o ya cancelado no se puede cancelar.
- [ ] El horario liberado puede volver a reservarse.
- [ ] Se registra auditoría de la cancelación.

**Reglas relacionadas**: RN-TUR-06, RN-TUR-08, RN-TUR-09, RN-TUR-10, RN-AUD-01

## Épica 5: Reprogramar turno (D.3 #5)

### US-008 — Reprogramar un turno conservando el historial
**Como** recepción
**Quiero** mover un turno futuro a otro horario (y opcionalmente otro profesional o sillón)
**Para** no tener que cancelar y crear uno nuevo

**Criterios de aceptación**:
- [ ] Se aplican las mismas reglas de solapamiento, horario y bloqueo que al crear.
- [ ] El turno conserva su identificador y su historial queda en auditoría con valores antes/después.
- [ ] Si el nuevo horario no es válido, responde 409 y el turno queda sin cambios.

**Reglas relacionadas**: RN-TUR-07, RN-TUR-08, RN-TUR-09, RN-AUD-01, RN-AUD-03

## Épica 6: Agenda diaria y semanal (D.3 #6)

### US-009 — Ver la agenda por profesional
**Como** recepción, administración u odontólogo (este último solo la propia)
**Quiero** ver la agenda diaria y semanal de un profesional
**Para** saber qué turnos tiene

**Criterios de aceptación**:
- [ ] Devuelve los turnos activos del rango pedido, ordenados por inicio.
- [ ] Odontólogo recibe 403 si pide la agenda de otro profesional.

**Reglas relacionadas**: RN-ACC-03

### US-010 — Ver la agenda por sillón
**Como** recepción o administración
**Quiero** ver la agenda diaria y semanal de un sillón
**Para** saber cuándo está ocupado o libre

**Criterios de aceptación**:
- [ ] Devuelve los turnos activos del sillón en el rango, ordenados por inicio.
- [ ] Incluye los bloqueos del sillón en el rango.

**Reglas relacionadas**: RN-TUR-02, RN-REC-02

## Épica 7: Pacientes (D.3 #7)

### US-011 — Gestionar pacientes con datos mínimos
**Como** recepción
**Quiero** cargar y editar pacientes (nombre, apellido, DNI y, opcionalmente, obra social o prepaga)
**Para** asignarles turnos

**Criterios de aceptación**:
- [ ] La obra social/prepaga se guarda como dato; no hay liquidación.
- [ ] DNI duplicado devuelve 409.
- [ ] Los datos de pruebas son ficticios.

**Reglas relacionadas**: RN-PAC-01, RN-PAC-02, RN-PAC-03

## Épica 8: Autenticación y roles (D.3 #8)

### US-012 — Iniciar sesión y operar según el rol
**Como** usuario del consultorio (administración, recepción u odontólogo)
**Quiero** iniciar sesión
**Para** acceder solo a lo que mi rol permite

**Criterios de aceptación**:
- [ ] Login válido devuelve un token; inválido devuelve 401.
- [ ] Sin token, las rutas protegidas devuelven 401.
- [ ] Un rol sin permiso recibe 403 según la matriz de 03.

**Reglas relacionadas**: RN-ACC-01 a RN-ACC-04

### US-013 — Gestionar usuarios
**Como** administración
**Quiero** crear usuarios y asignarles un rol
**Para** que el personal pueda operar

**Criterios de aceptación**:
- [ ] Se crea un usuario con rol; un odontólogo queda vinculado a un profesional.
- [ ] La contraseña se almacena solo como hash.

**Reglas relacionadas**: RN-ACC-04

## Épica 9: Auditoría de turnos (D.3 #9)

### US-014 — Consultar el registro de auditoría de un turno
**Como** administración
**Quiero** ver quién, qué y cuándo modificó un turno
**Para** tener trazabilidad

**Criterios de aceptación**:
- [ ] Cada creación, cancelación y reprogramación aparece con usuario, acción, valores antes/después y fecha y hora.
- [ ] No existe forma de editar ni borrar un registro.

**Reglas relacionadas**: RN-AUD-01, RN-AUD-02, RN-AUD-03

---

# PARTE 2 — Funcionalidades NO MVP (futuro, no se implementan en esta versión)

Todo lo que sigue es siguiente iteración o etapa posterior según el informe (D.3). No forma parte del alcance del MVP ni debe aparecer en las tareas del primer change.

## Diferenciador (siguiente iteración)

| Funcionalidad | Nota (informe) |
|---------------|----------------|
| Confirmación del turno por el paciente mediante enlace | Referencia: AgendaPro doble confirmación (D.2) |
| Lista de espera que ofrece los horarios liberados | No evidenciada en ninguno de los 18 sistemas (C.3.3); ver IF-03 en 10 |
| Reglas configurables de anticipación mínima para cancelar o reprogramar | Ver SE-08 en 10 |
| Reserva online por enlace público sin registro | Referencia: Turnito (D.2) |
| Exportación de datos del consultorio | No evidenciada en ningún sistema (C.3.4); ver IF-05 en 10 |

## Etapas posteriores

| Funcionalidad | Nota (informe) |
|---------------|----------------|
| Recordatorios por WhatsApp Business API | Costo por mensaje y proveedor oficial (resumen ejecutivo, hallazgo 4) |
| Señas y pagos con Mercado Pago | Referencia: Turnito |
| Facturación electrónica ARCA | Vacío del mercado argentino (C.3.1); ver IF-01 |
| Liquidación a obras sociales y prepagas | Vacío del mercado (C.3.1); ver IF-02 |
| Historia clínica, odontograma y periodontograma | Ley 27.706 y Decreto 393/2023 (C.3.6); ver IF-07 |
| Reportes y métricas, multisede, funciones de IA | — |
| Frontend React y aplicación móvil | — |
