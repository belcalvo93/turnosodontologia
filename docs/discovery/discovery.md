# Discovery — Turnos y agenda para consultorios odontológicos

**Fecha:** 2026-10-08
**Fuentes investigadas:** 18 sistemas (ver `informe-discovery.md` y las notas en `sources/`)
**Origen:** checklist de 11 puntos de `discovery-research`, respondido por Bruno Fiouchetta sobre la base del informe de investigación

## 1. Problema que resuelve

Los consultorios odontológicos argentinos gestionan turnos con herramientas que no evitan solapamientos de profesional ni de sillón, no liberan los horarios cancelados y no dejan registro de quién cambió qué. El informe confirma el vacío: ninguno de los 18 sistemas relevados evidencia la prevención de solapamientos como regla, ni por profesional ni por sillón o box.

## 2. Usuarios / roles

- **Administración:** configura profesionales, sillones o boxes, prestaciones, horarios de atención y bloqueos.
- **Recepción:** crea, cancela y reprograma turnos.
- **Odontólogo:** consulta su agenda diaria y semanal.
- **Paciente:** no usa el sistema en el MVP. Se incorpora con la reserva online, en la iteración diferenciadora.

## 3. Casos de uso

1. Como recepción, quiero crear un turno eligiendo paciente, profesional, sillón y prestación, para que el sistema rechace cualquier solapamiento.
2. Como recepción, quiero cancelar un turno, para liberar el horario.
3. Como recepción, quiero reprogramar un turno respetando las mismas reglas, sin perder su historial.
4. Como odontólogo, quiero ver mi agenda del día y de la semana.
5. Como administración, quiero bloquear horarios de un profesional o de un sillón (vacaciones, feriados, mantenimiento).

## 4. Competidores / soluciones existentes

Detalle completo en `informe-discovery.md` (secciones A y B). Los prioritarios son estos:

| Competidor | Problema que resuelve | Precio | Diferenciador |
|---|---|---|---|
| AgendaPro | "Más turnos, menos papeleo": agenda, recordatorios y pagos | No publicado | Versión argentina dental; liberación automática del horario cancelado |
| Dentalink | Gestión clínica y administrativa dental | Por cotización | Agenda por recursos documentada; odontograma y periodontograma |
| Doctocliq | Software dental y médico 100 % online | Plan gratuito; resto no publicado | Roles por perfil, odontograma y WhatsApp |
| Turnito | Turnos online para negocios de servicios | ARS 0 / 12.000 / 24.500 / 42.000 por mes | Seña que bloquea el turno; único con precios en pesos |
| Reservo | Agenda, ficha y facturación para salud | No publicado | Opera en Argentina; declara facturación ARCA (sin evidencia funcional) |

**Notas:** ningún competidor evidencia prevención de solapamientos, lista de espera, exportación de datos, auditoría, facturación ARCA ni liquidación a obras sociales. Esos vacíos fundamentan el MVP.

## 5. Funcionalidades necesarias (MVP)

- Alta y gestión de profesionales, sillones o boxes y prestaciones con duración.
- Horarios de atención por profesional y bloqueos de agenda por profesional o por sillón.
- Crear turno evitando solapamientos por profesional, por sillón y por paciente.
- Cancelar un turno liberando el horario.
- Reprogramar un turno con las mismas reglas, conservando el historial.
- Agenda diaria y semanal por profesional y por sillón.
- Pacientes con datos mínimos ficticios; la obra social o prepaga se guarda como dato.
- Autenticación con JWT y roles: administración, recepción y odontólogo.
- Registro de auditoría de cambios en turnos (quién, qué y cuándo).

## 6. Funcionalidades opcionales

**Diferenciadores (siguiente iteración):**

- Confirmación del turno por el paciente mediante enlace.
- Lista de espera que ofrece los horarios liberados.
- Anticipación mínima configurable para cancelar o reprogramar.
- Reserva online por enlace público sin registro.
- Exportación de datos.

**Etapas posteriores:**

- Recordatorios por WhatsApp Business API.
- Señas con Mercado Pago.
- Facturación ARCA.
- Liquidación a obras sociales y prepagas.
- Historia clínica, odontograma y periodontograma.
- Reportes, multisede, IA.
- Frontend React y app móvil.

## 7. Reglas de negocio

1. Un profesional no puede tener dos turnos solapados.
2. Un sillón o box no puede tener dos turnos solapados.
3. Un paciente no puede tener dos turnos solapados, aunque sean con distinto profesional y sillón.
4. Los turnos son intervalos semiabiertos [inicio, fin): un turno que empieza exactamente cuando termina otro **no** se solapa.
5. La duración del turno la define la prestación elegida.
6. Se rechaza un turno fuera del horario de atención del profesional.
7. Se rechaza un turno dentro de un bloqueo del profesional o del sillón.
8. No hay sobreturnos: la regla de no solapamiento no admite excepciones en el MVP.
9. Solo se puede cancelar o reprogramar un turno que todavía no empezó. No hay anticipación mínima en el MVP.
10. Cancelar libera el horario para nuevos turnos.
11. Reprogramar aplica las reglas 1 a 7 y conserva el historial del turno.
12. Toda creación, cancelación o reprogramación queda registrada con usuario, acción y fecha y hora.

## 8. Integraciones

Ninguna en el MVP: es una API backend autocontenida. WhatsApp, Mercado Pago, ARCA y Google Calendar quedan fuera por decisión consciente:

- **WhatsApp:** tiene costo por mensaje y requiere un proveedor oficial (ver Wati en el informe).
- **ARCA y Mercado Pago:** son dependencias externas que no hacen falta para validar el núcleo de agenda.

## 9. Restricciones

- **Stack definido por el grupo:** Python, FastAPI, JWT, SQLAlchemy, PostgreSQL y Docker/Compose. Redis y el frontend (React + TypeScript + Vite) quedan para después.
- Para el change del TP alcanza con el backend. No hace falta interfaz gráfica.
- Datos de pacientes siempre ficticios, en ejemplos, tests y capturas.
- Ninguna clave ni secreto en el repositorio.
- No se contactan proveedores ni se crean cuentas para evaluar competidores.
- La fecha de entrega todavía no está definida.

## 10. Riesgos

- **Evidencia comercial:** el MVP se apoya en evidencia mayormente comercial. No se probó ningún producto competidor; los vacíos detectados pueden ser falta de documentación pública y no de funcionalidad.
- **Supuesto sin probar:** que los consultorios necesiten la prevención de solapamientos por sillón. No está validado con odontólogos reales.
- **Supuesto sin probar:** que todo turno use un sillón. Prestaciones sin sillón, como una consulta en escritorio, no están contempladas.
- **Zonas horarias y cambios de horario:** sin una convención fija (por ejemplo, guardar en UTC y mostrar en America/Argentina/Buenos_Aires), los cálculos de solapamiento pueden fallar.
- **Concurrencia:** dos recepcionistas pueden reservar el mismo hueco a la vez. La validación tiene que estar respaldada por la base de datos (transacción o restricción), no solo por la aplicación.
- **Costo de WhatsApp:** puede hacer inviable el diferenciador de recordatorios.

## 11. Preguntas abiertas

**Supuesto de escala:** una sede con varios odontólogos y varios sillones. No fue confirmado explícitamente.

**Decisiones postergadas:**

- ¿Sobreturnos con permiso de administración, más adelante?
- ¿Margen de limpieza entre turnos en un mismo sillón?
- ¿Anticipación mínima para cancelar o reprogramar? ¿Cuánta?
- ¿Qué pasa con los turnos ya reservados cuando se crea un bloqueo que los cubre?
- ¿Cómo se usará la obra social o prepaga cuando llegue la liquidación?
- ¿Qué exige la Ley 27.706 (Decreto 393/2023) si más adelante se agrega historia clínica?

**Datos "No evidenciado" en el informe, que convendría confirmar mediante demos públicas:**

- facturación ARCA de Reservo;
- obras sociales en los productos dentales;
- gestión de sillones en los competidores;
- precios de AgendaPro y Dentalink en Argentina;
- sitio oficial de TurneroMed.
