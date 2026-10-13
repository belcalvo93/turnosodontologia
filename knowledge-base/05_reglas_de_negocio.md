# Reglas de Negocio

Cada regla tiene un código único `RN-{DOMINIO}-{NN}`. Cada una indica:
- **Origen**: *Informe* (con sección) o **Supuesto del equipo** (SE; referencia cruzada a [10_preguntas_abiertas.md](10_preguntas_abiertas.md)).
- **Verificación**: cómo se prueba con un test (T = pytest; "dominio" = test unitario sin DB ni HTTP; "API" = test de API).

Dominios: RN-PRO (profesionales y horarios), RN-REC (recursos: sillón, prestación, bloqueos), RN-TUR (turnos), RN-PAC (pacientes), RN-ACC (acceso), RN-AUD (auditoría).

Datos de los ejemplos: ficticios.

## Dominio: Recursos y disponibilidad (RN-PRO / RN-REC)

- **RN-PRO-01**: Cada profesional tiene horarios de atención por día de la semana; fuera de ellos no se le asignan turnos.
  Origen: Informe D.3 #2.
  Verificación (dominio): con horario lunes 09:00-13:00, un turno lunes 13:00-13:30 es rechazado; uno 12:30-13:00 es aceptado.
- **RN-PRO-02**: Un turno debe quedar completo dentro de una misma franja de atención del profesional (no puede empezar dentro y terminar fuera, ni cruzar el corte entre mañana y tarde).
  Origen: SE, derivada de RN-PRO-01 (ver 10, SE-14).
  Verificación (dominio): franja 09:00-13:00 y 14:00-18:00; turno 12:45-13:15 rechazado; turno 12:30-13:00 aceptado.
- **RN-REC-01**: La duración de la prestación es un entero mayor que cero en minutos; sillones y prestaciones tienen nombre único.
  Origen: Informe D.3 #1 (prestaciones con duración); unicidad de nombres SE.
  Verificación (API): crear prestación con duración 0 devuelve 422.
- **RN-REC-02**: Un bloqueo tiene alcance profesional o sillón, con inicio < fin y un motivo (vacaciones, feriado, mantenimiento del sillón).
  Origen: Informe D.3 #2.
  Verificación (dominio): bloqueo con fin <= inicio es inválido.
- **RN-REC-03**: Los sillones y profesionales desactivados no aceptan turnos nuevos; los turnos históricos se conservan.
  Origen: SE.
  Verificación (API): crear turno con sillón inactivo devuelve 422.

## Dominio: Turnos (RN-TUR)

- **RN-TUR-01**: La duración del turno la define la prestación: `fin = inicio + duracion_minutos`. El cliente no envía el fin.
  Origen: Informe D.3 #3.
  Verificación (dominio): prestación de 45 min con inicio 10:00 produce fin 10:45; con prestación de 30 min, fin 10:30 (dos casos).
- **RN-TUR-02**: El sillón/box es un recurso agendado del turno: todo turno tiene un sillón.
  Origen: Informe C.4 y D.3 #3 (doble recurso: profesional + sillón + prestación). Que absolutamente todo turno use sillón es **Supuesto del equipo** (SE-02, ver 10).
  Verificación (API): crear turno sin `sillon_id` devuelve 422.
- **RN-TUR-03**: No puede haber dos turnos activos superpuestos para el mismo profesional, ni dos para el mismo sillón/box.
  Origen: Informe D.3 #3, C.3 punto 2 y C.4.
  Verificación (dominio): turno 10:00-10:30 con Dr. A / Sillón 1 y nuevo 10:15-10:45 con Dr. A / Sillón 2 es rechazado (profesional); nuevo 10:15-10:45 con Dr. B / Sillón 1 es rechazado (sillón); nuevo 10:15-10:45 con Dr. B / Sillón 2 es aceptado.
- **RN-TUR-04**: Los intervalos son semiabiertos `[inicio, fin)`: un turno que empieza exactamente cuando termina otro (mismo profesional o sillón) es válido (turnos contiguos).
  Origen: **Supuesto del equipo** (el informe no lo dice literalmente; SE-10).
  Verificación (dominio): 10:00-10:30 y 10:30-11:00 con el mismo profesional y sillón: aceptado; 10:00-10:30 y 10:29-10:59: rechazado.
- **RN-TUR-05**: Un turno se rechaza si cae fuera del horario de atención del profesional (RN-PRO-01/02) o si se superpone con un bloqueo del profesional o del sillón elegido (intervalo semiabierto también para bloqueos).
  Origen: Informe D.3 #2 y #3 (existencia de horarios y bloqueos); el rechazo como regla de validación explícita y los límites semiabiertos de bloqueos son SE.
  Verificación (dominio): bloqueo de sillón 1 de 10:00 a 12:00; turno en sillón 1 a las 11:00 rechazado; turno en sillón 2 a las 11:00 aceptado; turno en sillón 1 a las 12:00 aceptado.
- **RN-TUR-06**: Cancelar un turno libera el horario: el profesional y el sillón quedan disponibles para ese intervalo.
  Origen: Informe D.3 #4.
  Verificación (dominio/API): cancelar turno 10:00-10:30 y luego crear otro en ese mismo intervalo con el mismo profesional y sillón: aceptado.
- **RN-TUR-07**: Reprogramar es una operación propia (no "cancelar y crear"): el mismo turno cambia de inicio y/o profesional y/o sillón, se aplican todas las reglas de creación (RN-TUR-01 a RN-TUR-05) y se conserva el historial (RN-AUD-01).
  Origen: Informe D.3 #5 y C.4.
  Verificación (API): reprogramar a un horario libre mantiene el mismo `turno_id` y deja dos entradas en auditoría; reprogramar a un horario ocupado devuelve 409 y el turno queda como estaba.
- **RN-TUR-08**: Al validar solapamientos de un turno que se reprograma, el propio turno no cuenta como conflicto consigo mismo (se excluye su id), y los turnos cancelados nunca generan conflicto.
  Origen: SE (consecuencia de RN-TUR-06 y RN-TUR-07).
  Verificación (dominio): mover un turno 10:00-10:30 a 10:15-10:45 (solapa con su propio horario anterior) es aceptado si no hay otro turno; turno cancelado en 10:00-10:30 no bloquea un nuevo turno en ese intervalo.
- **RN-TUR-09**: Solo se pueden cancelar o reprogramar turnos futuros (inicio posterior al momento actual). Un turno pasado o en curso se rechaza.
  Origen: **Supuesto del equipo** (SE-11; no figura en el informe; la anticipación mínima configurable es una función de la siguiente iteración, D.3).
  Verificación (dominio, con reloj inyectado): con "ahora" = 09:00, cancelar turno de las 10:00 es aceptado; cancelar turno de las 08:30 es rechazado; cancelar turno de las 09:00 exactas es rechazado.
- **RN-TUR-10**: Un turno ya cancelado no se puede cancelar ni reprogramar de nuevo.
  Origen: SE.
  Verificación (API): cancelar dos veces devuelve 409 la segunda.
- **RN-TUR-11**: No hay sobreturnos: no se permite superponer turnos aun con autorización.
  Origen: **Supuesto del equipo** (SE-04). El informe señala que los sobreturnos no están evidenciados en ninguno de los 18 sistemas (C.3.3) y no define si el consultorio los necesita.
  Verificación: queda cubierta por RN-TUR-03 (no existe camino de excepción); test que confirma que ningún rol puede forzar un solapamiento.
- **RN-TUR-12**: Un mismo paciente no puede tener dos turnos activos superpuestos.
  Origen: **Supuesto del equipo** (SE-03). No figura en el informe.
  Verificación (dominio): el mismo paciente con dos turnos 10:00-10:30 y 10:15-10:45 con distintos profesional y sillón: el segundo es rechazado.
- **RN-TUR-13**: No hay margen de limpieza obligatorio entre turnos del mismo sillón en el MVP; el margen, si hace falta, se modela dentro de la duración de la prestación.
  Origen: SE (SE-07).
  Verificación (dominio): coincide con RN-TUR-04 (contiguos válidos).
- **RN-TUR-14**: Los turnos se crean con estado `reservado`; los estados confirmado, atendido y ausente no existen en el MVP.
  Origen: SE; el informe los menciona en C.4 pero D.3 no los incluye.
  Verificación (API): un turno nuevo tiene estado `reservado`.

## Dominio: Pacientes (RN-PAC)

- **RN-PAC-01**: Un paciente tiene datos mínimos (nombre, apellido, DNI) y puede tener obra social/prepaga y nro. de afiliado como datos opcionales, sin liquidación ni validación contra el padrón.
  Origen: Informe D.3 #7.
  Verificación (API): crear paciente con obra social "Obra Social Ficticia A" la guarda y la devuelve; sin obra social también es válido.
- **RN-PAC-02**: El DNI es único por paciente.
  Origen: SE (SE-15).
  Verificación (API): crear dos pacientes con DNI "00000001 (ficticio)" devuelve 409 la segunda vez.
- **RN-PAC-03**: Solo se usan datos ficticios en seeds, ejemplos y tests; el repositorio no contiene datos reales de pacientes.
  Origen: Informe D.3 #7.
  Verificación: revisión de seeds/fixtures; los valores de DNI de fixtures llevan el sufijo "(ficticio)".

## Dominio: Acceso (RN-ACC)

- **RN-ACC-01**: Toda operación excepto login y health exige usuario autenticado con uno de los tres roles: administración, recepción, odontólogo.
  Origen: Informe D.3 #8.
  Verificación (API): sin token, `GET /turnos/1` devuelve 401.
- **RN-ACC-02**: Los permisos por rol siguen la matriz de [03_actores_y_roles.md](03_actores_y_roles.md); un rol sin permiso recibe 403.
  Origen: SE (la matriz no está en el informe; SE-12).
  Verificación (API): recepción creando una prestación devuelve 403; odontólogo creando un turno devuelve 403.
- **RN-ACC-03**: Un odontólogo solo ve su propia agenda.
  Origen: SE (SE-12).
  Verificación (API): odontólogo A pidiendo la agenda del odontólogo B devuelve 403.
- **RN-ACC-04**: Las contraseñas se guardan solo como hash; los secretos no se versionan.
  Origen: SE (buena práctica; restricción "sin secretos en el repo" del contexto del proyecto).
  Verificación: test que confirma que la columna es un hash y no el texto original.

## Dominio: Auditoría (RN-AUD)

- **RN-AUD-01**: Toda modificación de un turno (crear, cancelar, reprogramar) genera un registro de auditoría con quién (usuario), qué (acción y valores antes/después) y cuándo (fecha y hora).
  Origen: Informe D.3 #9 y C.4.
  Verificación (API): crear, reprogramar y cancelar un turno deja exactamente tres registros en orden cronológico, con el usuario que operó.
- **RN-AUD-02**: El registro de auditoría es de solo agregado: no hay operación para editarlo ni borrarlo.
  Origen: SE (SE-13; coherente con la trazabilidad de C.4).
  Verificación (API): no existen rutas PUT/PATCH/DELETE de auditoría (405/404).
- **RN-AUD-03**: Si una operación de turno se rechaza (por ejemplo un 409 de solapamiento), el turno no cambia y no se registra una modificación; el registro y el cambio se confirman o se descartan juntos (misma transacción).
  Origen: SE.
  Verificación (API): reprogramar a un horario ocupado devuelve 409 y la cantidad de registros de auditoría no cambia.

## Dominio: Excepciones globales

- **RN-GLO-01**: Los errores de regla de negocio devuelven un mensaje claro en español y un código HTTP consistente (409 conflicto de agenda, 422 dato inválido, 403 sin permiso, 401 sin autenticar).
  Origen: SE.
  Verificación (API): un test por código.
- **RN-GLO-02**: Funciones fuera del MVP (confirmación por enlace, lista de espera, anticipación mínima configurable, reserva online, exportación, WhatsApp, Mercado Pago, ARCA, obras sociales, historia clínica) no tienen reglas en esta versión.
  Origen: Informe D.3.

## Trazabilidad de reglas hacia preguntas abiertas

| Regla | Pregunta/supuesto en 10 |
|-------|--------------------------|
| RN-TUR-02 | SE-02 |
| RN-TUR-04 | SE-10 |
| RN-TUR-09 | SE-11 |
| RN-TUR-11 | IF-04, SE-04 |
| RN-TUR-12 | SE-03 |
| RN-TUR-13 | SE-07 |
| RN-ACC-02/03 | SE-12 |
| RN-AUD-01/02 | IF-06, SE-13 |
