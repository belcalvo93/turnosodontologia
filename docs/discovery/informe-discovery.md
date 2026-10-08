# Informe de Discovery — Sistema de turnos y agenda para consultorios odontológicos (Argentina)

**Materia:** Metodología I — Tecnicatura Universitaria en Programación (UTN)
**Integrantes:** Bruno Fiouchetta, Elías Tello, Belén Calvo, Hernán Gonzales, Joaquín Morán
**Fecha de relevamiento:** 2026-10-08
**Estado:** borrador pendiente de verificación de fuentes (etapa en "Parar acá")
**Consigna que responde:** `docs/discovery/consigna-investigacion.md` (texto literal de la consigna del TP)

---

## Resumen ejecutivo

Se relevaron **18 soluciones** de gestión de turnos y agenda aplicables a consultorios odontológicos:

- **Por país de origen:** 4 argentinas, 8 latinoamericanas (Chile, Perú y Brasil) y 6 internacionales. Las internacionales incluyen un componente de mensajería por WhatsApp que no es una agenda.
- **Con presencia en Argentina:** 7 (las 4 argentinas, más AgendaPro, Doctoralia y Reservo).
- **Fuentes:** solo públicas (sitios oficiales, páginas de precios, centros de ayuda, tutoriales oficiales, fichas de tiendas de aplicaciones, marketplaces y prensa). No se contactó a proveedores ni se crearon cuentas.

**Principales hallazgos:**

1. **La evidencia es mayormente comercial.** De lo relevado, solo una parte está comprobada: centros de ayuda de Dentalink y RAS Salud, tutoriales oficiales de AgendaPro, precios publicados de Turnito, Encuadrado y Clinicorp, y datos de tiendas de aplicaciones. El resto es afirmación del proveedor. Ninguna cifra de resultados publicada, como la reducción de inasistencias o la cantidad de clientes, informa metodología o fuente independiente.
2. **El estándar de mercado ya está definido.** Lo componen la agenda online por profesional, la reserva por enlace sin registro del paciente, los recordatorios con confirmación (WhatsApp como canal dominante), la historia clínica digital y el funcionamiento en la nube con acceso móvil.
3. **El mercado argentino tiene vacíos visibles:**
   - Ningún software odontológico especializado evidencia facturación electrónica ARCA ni liquidación a obras sociales y prepagas.
   - Solo un producto horizontal, no odontológico, publica precios en pesos (Turnito).
   - Ningún producto evidencia la prevención de solapamientos como regla, ni por profesional ni por sillón o box.
   - Ningún producto evidencia lista de espera ni exportación de datos.
4. **El costo de WhatsApp es real.** Los recordatorios por la API oficial de WhatsApp tienen costos de Meta además de los de la plataforma, lo que condiciona su inclusión en un MVP.

**MVP recomendado:** núcleo de agenda odontológica con profesionales, sillones o boxes y prestaciones de duración variable. Incluye:

- creación de turnos con **prevención de solapamientos por profesional y por sillón**;
- cancelación con liberación del horario;
- reprogramación;
- bloqueos de agenda;
- roles (administración, recepción y odontólogo);
- registro de auditoría de cambios en los turnos.

WhatsApp, señas con Mercado Pago, facturación ARCA, obras sociales y odontograma quedan para etapas posteriores (ver sección D).

---

## Metodología

- **Fecha de consulta:** todas las fuentes se consultaron el **2026-10-08**.
- **Herramientas:** búsqueda web y lectura de las páginas citadas por el agente de IA, con verificación humana posterior (ver "Verificación de fuentes").
- **Accesos fallidos:** si una página bloqueó el acceso automatizado (error 403), no respondió o devolvió una página vacía, se dejó constancia y **no se completó el dato por deducción**.
- **Datos indirectos:** algunos datos de TurneroMed y una reseña de Doctoralia se tomaron del **resumen del buscador** sobre fichas de Capterra que no se pudieron abrir. Están marcados como "Tercero" y señalados en la sección "Hallazgos".

**Clasificación de la evidencia** (se usa en todas las celdas):

| Etiqueta | Significado |
|---|---|
| **Comprobado** | Consta en documentación de uso (centro de ayuda), en un manual o video tutorial oficial, o en datos propios de una tienda de aplicaciones (por ejemplo, la calificación). Un **precio publicado** se considera comprobado como oferta vigente. Las funcionalidades listadas dentro de un plan siguen siendo "Declarado". |
| **Declarado** | Afirmación comercial: lo dice el proveedor en su sitio, sin demostración. |
| **Tercero** | Surge de marketplace, prensa o resumen del buscador, no del proveedor. Se usa solo cuando no hubo acceso a una fuente oficial. |
| **No evidenciado** | No se encontró respaldo público. **No equivale a "no lo tiene".** |
| **No aplica** | El producto no pertenece a esa categoría (por ejemplo, una plataforma de mensajería no tiene odontograma). |

Las cifras de clientes, reducción de ausencias o productividad se informan siempre como afirmación comercial.

---

## A. Tabla comparativa (18 sistemas, ordenados por relevancia para Argentina)

**Criterio de orden:**

1. Presencia en Argentina, comprobada o declarada.
2. Especialización odontológica.
3. Utilidad como referencia para un producto argentino.

El número (#) de cada sistema se mantiene en todas las tablas.

### A.1 Identificación

| # | Producto | Proveedor | País de origen | Segmento | Modalidad | URL oficial / fuente principal | Fecha |
|---|---|---|---|---|---|---|---|
| 1 | AgendaPro (vertical dental) | AgendaPro | Chile (versión Argentina) | Consultorio y clínica, uno o varios sillones, multisede | SaaS + apps iOS/Android | https://agendapro.com/ar/dental/software-odontologico | 2026-10-08 |
| 2 | Turnito | Turnito | Argentina | Horizontal (consultorios médicos, psicólogos, estética, etc.); no específico de odontología | SaaS web | https://www.turnito.app/ | 2026-10-08 |
| 3 | TurneroMed | TusProgramas | Argentina (Tercero) | Odontólogos, médicos, kinesiólogos, estética (Tercero) | SaaS web (Tercero) | https://www.capterra.com/p/10040798/TurneroMed/ (sitio oficial: No evidenciado) | 2026-10-08 |
| 4 | Doctoralia (para especialistas) | Docplanner | España / Polonia (opera en Argentina) | Profesionales independientes y centros | SaaS + app + marketplace de pacientes | https://apps.apple.com/es/app/doctoralia-para-especialistas/id1237598188 (doctoralia.com.ar no respondió) | 2026-10-08 |
| 5 | Reservo | Reservo | Chile (opera en Chile, México y Argentina, Tercero) | Profesionales independientes, centros médicos y clínicas | SaaS | https://reservo.cl/ar/ · https://chocale.cl/2026/09/reservo-la-plataforma-que-ayuda-a-clinicas-a-recuperar-hasta-50-horas-semanales/ | 2026-10-08 |
| 6 | RAS Salud (módulo de turnos, MrTurno) | RAS Salud | Argentina (domicilio en Godoy Cruz, Mendoza, según su centro de ayuda) | Instituciones médicas; módulo para el paciente | Web | https://intercom.help/ayuda-ras-salud/en/articles/3843356-mrturno-gestion-de-turnos-confirmar-cancelar-etc · https://intercom.help/ayuda-ras-salud/en/articles/3400146-leccion-5-de-turnos-cancelacion-de-turnos | 2026-10-08 |
| 7 | Medicloud | Woopi App | Argentina (Tercero) | Médicos y profesionales de la salud | App Android | https://chrome-stats.com/d/com.woopi.medicloud (espejo de la ficha de Google Play) | 2026-10-08 |
| 8 | Dentalink | Dentalink | Chile | Odontólogos independientes y clínicas multisucursal | SaaS | https://www.softwaredentalink.com/ · https://web-es.softwaredentalink.com/en/planes · https://intercom.help/softwaredentalink/es/articles/9493130-como-confirmar-anular-y-cambiar-citas | 2026-10-08 |
| 9 | Doctocliq | Zolupro S.A.C. | Perú (contactos en Perú y México) | Consultorios dentales, estética, especialistas, fisioterapia | SaaS + apps iOS/Android | https://www.doctocliq.com/ · https://apps.apple.com/us/app/doctocliq/id1445399223 | 2026-10-08 |
| 10 | Dentidesk | Dentidesk | Chile | Clínicas, odontólogos, universidades, sindicatos | SaaS | https://www.dentidesk.com/ | 2026-10-08 |
| 11 | Encuadrado | Encuadrado | Chile (selector Chile/México) | Profesionales de la salud; odontología no listada | SaaS | https://encuadrado.com/ | 2026-10-08 |
| 12 | Clinicorp | Clinicorp | Brasil | Clínicas y consultorios odontológicos y de estética | SaaS + app del paciente | https://www.clinicorp.com/ | 2026-10-08 |
| 13 | Simples Dental | Simples Dental | Brasil | Dentistas y clínicas odontológicas | SaaS | https://www.simplesdental.com/ | 2026-10-08 |
| 14 | Clinic Cloud | Doctoralia España SL (Docplanner) | España | Clínicas y profesionales sanitarios; odontología no explícita | SaaS | https://www.clinic-cloud.com/ | 2026-10-08 |
| 15 | Wati (turnos por WhatsApp) | Wati | Internacional (proveedor oficial de Meta) | Clínicas: recepción y pacientes | SaaS de mensajería; no es agenda | https://www.wati.io/geo-argentina-es/automatiza-los-turnos-clinicos-por-whatsapp-sin-perder-el-cont | 2026-10-08 |
| 16 | Dentrix Ascend | Henry Schein One | Estados Unidos | Clínicas dentales, multisede | SaaS cloud-native | https://www.dentrixascend.com/ | 2026-10-08 |
| 17 | Curve Dental | CD Newco, LLC | Estados Unidos (usuarios en EE. UU. y Canadá) | Clínicas dentales | SaaS + app móvil | https://www.curvedental.com/ | 2026-10-08 |
| 18 | Open Dental | Open Dental Software | Estados Unidos (prefijo telefónico; país no declarado) | Consultorios dentales de cualquier tamaño | No evidenciado (local o nube) | https://www.opendental.com/ | 2026-10-08 |

### A.2 Gestión de agenda

| # | Producto | Vista diaria/semanal | Múltiples profesionales | Sillones o boxes | Duración variable | Bloqueos | Sobreturnos | Prevención de solapamientos |
|---|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | No evidenciado | Declarado (turnos por profesional) | Declarado solo como segmento ("uno o varios sillones") | Declarado (turnos por tipo de práctica) | No evidenciado | No evidenciado | No evidenciado |
| 2 | Turnito | No evidenciado | No evidenciado ("agendas" limitadas por plan, Declarado) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 3 | TurneroMed | Tercero (calendario digital) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 4 | Doctoralia | Declarado (resumen de citas del día) | No evidenciado | No evidenciado | No evidenciado | Tercero (reseña de usuario) | No evidenciado | No evidenciado |
| 5 | Reservo | Tercero (agenda) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | Comprobado ("Turnos del día") | Comprobado (agendas por profesional) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 7 | Medicloud | No evidenciado (turnos planificados) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 8 | Dentalink | Comprobado (vistas diaria, semanal y diaria global) | Comprobado (disponibilidad por especialidad, profesional y recurso) | Comprobado en parte (habla de "recursos"; no nombra sillones) | Comprobado (se modifica la duración de la cita) | No evidenciado | No evidenciado | No evidenciado |
| 9 | Doctocliq | Declarado (agenda por especialista) | Declarado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 10 | Dentidesk | Declarado (agenda personalizable) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 11 | Encuadrado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (bloqueo de horarios, límites diarios) | No evidenciado | No evidenciado |
| 12 | Clinicorp | Declarado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 13 | Simples Dental | Declarado (agenda online) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 14 | Clinic Cloud | No evidenciado | Declarado (multiprofesional y multisede, optimización de huecos) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 15 | Wati | No aplica | No aplica | No aplica | No aplica | No aplica | No aplica | No aplica |
| 16 | Dentrix Ascend | Declarado (agenda inteligente) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 17 | Curve Dental | Declarado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 18 | Open Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |

### A.3 Turnos digitales

| # | Producto | Reserva online 24/7 por enlace | Canales: web, redes, chatbot, WhatsApp | Confirmación | Cancelación | Reprogramación | Lista de espera |
|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | Declarado (sin registro del paciente) | No evidenciado como canal de reserva | Declarado (doble confirmación) | Declarado (liberación automática del espacio) | No evidenciado | No evidenciado |
| 2 | Turnito | Declarado (enlace sin registro ni descarga; el turno se bloquea al acreditarse la seña) | Declarado (enlace compartido por WhatsApp, Instagram o web) | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 3 | TurneroMed | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 4 | Doctoralia | Declarado (marketplace de pacientes) | Declarado (sitio de Doctoralia) | Declarado (el paciente confirma, app de México) | Declarado (el paciente cancela, app de México) | No evidenciado | No evidenciado |
| 5 | Reservo | Tercero (portal de agendamiento) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | No evidenciado | No evidenciado | Comprobado (el paciente confirma hasta un día antes) | Comprobado (desde "Turnos del día" o "Agendas"; el paciente cancela y libera el horario) | Comprobado (se cancela el turno y se crea uno nuevo con los datos precargados) | No evidenciado |
| 7 | Medicloud | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 8 | Dentalink | Declarado (agendamiento online) | No evidenciado | Comprobado (estados de cita configurables, p. ej. "Confirmado") | Comprobado (estado "anulado") | Comprobado (cambio de fecha o arrastre a otro horario) | No evidenciado |
| 9 | Doctocliq | Declarado (enlace de agendamiento) | Declarado (asistente de IA que agenda por WhatsApp) | Declarado | No evidenciado | No evidenciado | No evidenciado |
| 10 | Dentidesk | Declarado (por integración) | No evidenciado | No evidenciado | No evidenciado | Declarado | No evidenciado |
| 11 | Encuadrado | Declarado (el paciente agenda solo) | Declarado (perfil del profesional) | Declarado (automática por WhatsApp, plan Avanzado) | No evidenciado | Declarado (reagendamiento) | No evidenciado |
| 12 | Clinicorp | No evidenciado | Declarado (asistente de IA por WhatsApp) | Declarado (por WhatsApp) | No evidenciado | No evidenciado | No evidenciado |
| 13 | Simples Dental | No evidenciado | No evidenciado | Declarado (automática por WhatsApp) | No evidenciado | No evidenciado | No evidenciado |
| 14 | Clinic Cloud | Declarado (vía Doctoralia) | Declarado (Doctoralia) | Declarado (automática) | No evidenciado | No evidenciado | No evidenciado |
| 15 | Wati | No aplica | Declarado (chatbot de WhatsApp para preguntas frecuentes) | Declarado (botón "confirmar") | No evidenciado | Declarado (botón "cambiar"; deriva a recepción) | No evidenciado |
| 16 | Dentrix Ascend | Declarado | No evidenciado | Declarado | No evidenciado | No evidenciado | No evidenciado |
| 17 | Curve Dental | Declarado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 18 | Open Dental | Declarado (Web Sched) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |

### A.4 Automatización

| # | Producto | Recordatorios | Seguimiento de ausentes o recuperación | Controles periódicos | Campañas |
|---|---|---|---|---|---|
| 1 | AgendaPro | Declarado (WhatsApp, SMS, email) | No evidenciado | No evidenciado | Declarado (CRM, emailing) |
| 2 | Turnito | Declarado (desde el plan Plus; 30/100/250 mensajes de WhatsApp por mes) | No evidenciado | No evidenciado | No evidenciado |
| 3 | TurneroMed | Tercero (WhatsApp) | No evidenciado | No evidenciado | No evidenciado |
| 4 | Doctoralia | Declarado (al paciente) | No evidenciado | No evidenciado | No evidenciado |
| 5 | Reservo | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 7 | Medicloud | No evidenciado (planificado) | No evidenciado | No evidenciado | No evidenciado |
| 8 | Dentalink | Declarado (tareas automáticas de citas) | No evidenciado | No evidenciado | Declarado (email marketing, encuestas NPS) |
| 9 | Doctocliq | Declarado (WhatsApp, correo, SMS) | No evidenciado | No evidenciado | Declarado (marketing y campañas) |
| 10 | Dentidesk | Declarado (WhatsApp automático "próximamente") | No evidenciado | No evidenciado | No evidenciado |
| 11 | Encuadrado | Declarado (WhatsApp y email) | Declarado (recuperación de citas, plan Avanzado) | No evidenciado | No evidenciado |
| 12 | Clinicorp | Declarado (confirmación por WhatsApp) | No evidenciado | Declarado (alertas de retorno) | No evidenciado |
| 13 | Simples Dental | Declarado (confirmación por WhatsApp) | No evidenciado | No evidenciado | No evidenciado |
| 14 | Clinic Cloud | Declarado (WhatsApp, SMS, email) | No evidenciado | No evidenciado | No evidenciado |
| 15 | Wati | Declarado (48 h antes del turno) | No evidenciado | Declarado (seguimientos y controles posteriores a la atención) | Declarado |
| 16 | Dentrix Ascend | Declarado (recordatorios y encuestas) | No evidenciado | No evidenciado | No evidenciado |
| 17 | Curve Dental | Declarado | No evidenciado | No evidenciado | No evidenciado |
| 18 | Open Dental | Declarado (mensajería automática, SMS) | No evidenciado | No evidenciado | Declarado (email masivo) |

### A.5 Gestión odontológica

| # | Producto | Ficha / historia clínica | Anamnesis | Odontograma | Periodontograma | Imágenes / radiografías | Presupuestos / planes de tratamiento |
|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | Declarado (personalizable) | No evidenciado | No evidenciado | No evidenciado | Declarado | Declarado (presupuestos); planes No evidenciado |
| 2 | Turnito | No evidenciado (solo historial de clientes en plan Pro) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 3 | TurneroMed | Tercero (gestión de pacientes) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 4 | Doctoralia | Declarado (información básica del paciente) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 5 | Reservo | Tercero (ficha personalizable por especialidad) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | No evidenciado (solo documentación administrativa adjunta, Comprobado) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 7 | Medicloud | No evidenciado (planificado) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 8 | Dentalink | Declarado | No evidenciado | Declarado | Declarado | Declarado (radiografías) | Declarado (presupuestos) |
| 9 | Doctocliq | Declarado | No evidenciado | Declarado | Declarado | Declarado (imágenes por paciente) | Declarado (presupuestos) |
| 10 | Dentidesk | Declarado (con dictado por voz) | No evidenciado | Declarado | Declarado (ficha de periodoncia) | No evidenciado | No evidenciado |
| 11 | Encuadrado | Declarado (ficha certificada CENS) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 12 | Clinicorp | Declarado | Declarado (anamnesis personalizable) | No evidenciado | No evidenciado | Declarado (sugerencias de IA sobre radiografías) | Declarado (simulación de tratamientos) |
| 13 | Simples Dental | Declarado | No evidenciado | Declarado | No evidenciado | No evidenciado | No evidenciado |
| 14 | Clinic Cloud | Declarado (con IA) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 15 | Wati | No aplica | No aplica | No aplica | No aplica | No aplica | No aplica |
| 16 | Dentrix Ascend | Declarado (charting, notas por voz) | No evidenciado | Declarado (charting) | No evidenciado | Declarado (IA sobre radiografías) | Declarado (planes mostrados en el charting) |
| 17 | Curve Dental | Declarado | No evidenciado | Declarado (charting) | Declarado (perio charting) | Declarado | No evidenciado |
| 18 | Open Dental | No evidenciado | No evidenciado | Declarado (odontograma 3D) | No evidenciado | No evidenciado | No evidenciado |

### A.6 Administración

| # | Producto | Caja / cobros | Señas / pago online | Mercado Pago | Facturación electrónica local | Obras sociales / prepagas / seguros | Liquidaciones / comisiones | Reportes |
|---|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | Declarado | Declarado | No evidenciado | No evidenciado | No evidenciado | Declarado (comisiones por dentista) | Declarado (por profesional y sede) |
| 2 | Turnito | No evidenciado | Declarado (seña o total con MercadoPago, Talo o transferencia) | Declarado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 3 | TurneroMed | No evidenciado | No evidenciado | Tercero | Tercero ("facturación integrada") | Tercero (seguimiento de seguros) | No evidenciado | No evidenciado |
| 4 | Doctoralia | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 5 | Reservo | Tercero (pagos) | No evidenciado | No evidenciado | Declarado solo como título de la landing argentina ("factura AFIP/ARCA") | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 7 | Medicloud | No evidenciado | No evidenciado (Mercado Pago planificado) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 8 | Dentalink | Declarado (control de caja) | Declarado (pagos online, cuotas) | No evidenciado | No evidenciado | Declarado (convenios con seguros; Argentina No evidenciado) | Declarado (pago a odontólogos) | Declarado |
| 9 | Doctocliq | Declarado | No evidenciado | No evidenciado | Declarado (Perú, México, Ecuador, Colombia; Argentina No evidenciado) | No evidenciado | Declarado (comisiones) | Declarado |
| 10 | Dentidesk | No evidenciado | No evidenciado | No evidenciado | Declarado (SII de Chile) | No evidenciado | No evidenciado | Declarado |
| 11 | Encuadrado | Declarado | Declarado (pagos anticipados, Tap to Pay) | No evidenciado | Declarado (boletas SII de Chile) | No evidenciado | No evidenciado | No evidenciado |
| 12 | Clinicorp | Declarado | Declarado (Pix, boleto, tarjeta) | No evidenciado | No evidenciado | No evidenciado | Declarado (comisiones) | Declarado (más de 50 reportes) |
| 13 | Simples Dental | Declarado (flujo de caja, cobranzas) | No evidenciado | No evidenciado | Declarado (notas fiscales de Brasil) | No evidenciado | No evidenciado | Declarado (indicadores) |
| 14 | Clinic Cloud | Declarado (bonos, cobros) | No evidenciado | No evidenciado | Declarado (Verifactu, TicketBAI; España) | Declarado (mutuas; España) | No evidenciado | Declarado (KPI) |
| 15 | Wati | No aplica | No aplica | No aplica | No aplica | No aplica | No aplica | No aplica |
| 16 | Dentrix Ascend | Declarado | Declarado (pagos online) | No evidenciado | No evidenciado | Declarado (seguros de EE. UU.) | No evidenciado | Declarado |
| 17 | Curve Dental | Declarado | Declarado (Curve Pay) | No evidenciado | No evidenciado | Declarado (seguros de EE. UU.) | No evidenciado | Declarado |
| 18 | Open Dental | Declarado (facturación) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |

### A.7 Integraciones

| # | Producto | WhatsApp Business API | Google Calendar | Sitio web / redes | API pública | Mercado Pago | AFIP / ARCA | Otras (radiología, firma digital, marketing) |
|---|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | Declarado (WhatsApp; tipo de API No evidenciado) | No evidenciado | Declarado (marketplace propio) | No evidenciado | No evidenciado | No evidenciado | Declarado (emailing) |
| 2 | Turnito | Declarado (cupos de mensajes; tipo de API No evidenciado) | Declarado (más Google Meet) | Declarado (enlace para web e Instagram) | No evidenciado | Declarado | No evidenciado | Declarado (Pixel, Google Analytics) |
| 3 | TurneroMed | Tercero | No evidenciado | No evidenciado | No evidenciado | Tercero | No evidenciado | No evidenciado |
| 4 | Doctoralia | No evidenciado | No evidenciado | Declarado (marketplace) | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 5 | Reservo | No evidenciado | No evidenciado | Tercero (portal) | No evidenciado | No evidenciado | Declarado (solo título) | No evidenciado |
| 6 | RAS Salud | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 7 | Medicloud | No evidenciado (planificado) | No evidenciado | No evidenciado | No evidenciado | No evidenciado (planificado) | No evidenciado | No evidenciado |
| 8 | Dentalink | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (firma electrónica, email marketing) |
| 9 | Doctocliq | Declarado | Declarado (ficha de App Store) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (Zoom, marketing) |
| 10 | Dentidesk | No evidenciado ("próximamente") | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (Alegra, República Dominicana) |
| 11 | Encuadrado | Declarado | No evidenciado | Declarado (perfil profesional) | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 12 | Clinicorp | Declarado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (firma electrónica, SPC Brasil) |
| 13 | Simples Dental | Declarado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (firma electrónica) |
| 14 | Clinic Cloud | Declarado | No evidenciado | Declarado (Doctoralia) | No evidenciado | No evidenciado | No evidenciado | Declarado (firma digital) |
| 15 | Wati | Declarado (proveedor oficial de Meta) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (marketing) |
| 16 | Dentrix Ascend | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (imágenes en la nube) |
| 17 | Curve Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (imágenes, lista de compatibilidad) |
| 18 | Open Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado ("cientos de bridges" a otros programas) |

### A.8 Operación

| # | Producto | Sucursales | Roles y permisos | Auditoría | Exportación de datos | Importación / migración | Soporte y capacitación |
|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | Declarado (multisede) | Comprobado (video oficial "Creación de Cuenta Recepcionista") | No evidenciado | No evidenciado | No evidenciado | Comprobado (2 manuales PDF y 7 videos oficiales en Vimeo) |
| 2 | Turnito | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 3 | TurneroMed | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Tercero (email, teléfono, chat) |
| 4 | Doctoralia | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 5 | Reservo | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Comprobado (centro de ayuda con lecciones) |
| 7 | Medicloud | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 8 | Dentalink | Declarado (multicentro, plan Pro) | Comprobado (la importación de pacientes es exclusiva del usuario Admin) | No evidenciado | No evidenciado | Comprobado (Excel, hasta 10.000 pacientes, sin duplicar documento) | Comprobado (centro de ayuda) |
| 9 | Doctocliq | No evidenciado | Declarado (permisos por rol y por integrante) | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 10 | Dentidesk | Declarado (multisucursal) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 11 | Encuadrado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (asesoría en la promoción del primer mes) |
| 12 | Clinicorp | Declarado (plan Enterprise) | No evidenciado (usuarios ilimitados, Declarado) | No evidenciado | No evidenciado | Declarado (migración en 3 días hábiles) | Declarado (lunes a viernes de 8 a 18 h) |
| 13 | Simples Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 14 | Clinic Cloud | Declarado (multisede) | No evidenciado | No evidenciado | No evidenciado | Declarado (migración sin costo) | Declarado (formación, soporte los 7 días) |
| 15 | Wati | No aplica | No evidenciado (bandeja compartida, Declarado) | No evidenciado | No evidenciado | No aplica | No evidenciado |
| 16 | Dentrix Ascend | Declarado (multisede) | Declarado (acceso por roles) | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 17 | Curve Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (soporte en EE. UU.) |
| 18 | Open Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |

### A.9 Seguridad y cumplimiento

| # | Producto | Datos de salud / privacidad | Respaldo | Control de acceso | Adecuación a normativa argentina |
|---|---|---|---|---|---|
| 1 | AgendaPro | No evidenciado | No evidenciado ("almacenamiento en la nube", sin detalle) | Comprobado (cuenta de recepcionista diferenciada) | No evidenciado |
| 2 | Turnito | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 3 | TurneroMed | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 4 | Doctoralia | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 5 | Reservo | Tercero (ley de datos personales y CENS, de Chile; dicho por la empresa) | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 7 | Medicloud | Tercero (declara leyes 25.326 y 26.529) | No evidenciado | No evidenciado | Tercero (mismas leyes) |
| 8 | Dentalink | Declarado (ISO 27001, HIPAA, GDPR, tráfico cifrado) | Declarado (respaldos diarios) | No evidenciado | No evidenciado |
| 9 | Doctocliq | No evidenciado | No evidenciado | Declarado (por rol) | No evidenciado |
| 10 | Dentidesk | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 11 | Encuadrado | Declarado (ficha certificada CENS, Chile) | No evidenciado | No evidenciado | No evidenciado |
| 12 | Clinicorp | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 13 | Simples Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 14 | Clinic Cloud | Declarado (RGPD, cifrado, trazabilidad) | No evidenciado | No evidenciado | No evidenciado |
| 15 | Wati | Declarado (GDPR, SOC 2 Tipo II) | No evidenciado | No evidenciado | No evidenciado |
| 16 | Dentrix Ascend | Declarado (SOC 2, HIPAA) | Declarado (respaldos cifrados) | Declarado (por roles) | No evidenciado |
| 17 | Curve Dental | Declarado (infraestructura HIPAA) | No evidenciado | No evidenciado | No evidenciado |
| 18 | Open Dental | No evidenciado | No evidenciado | No evidenciado | No evidenciado |

### A.10 Modelo comercial

| # | Producto | Prueba gratuita | Plan gratuito | Precios publicados | Moneda | Modalidad de cobro | Costos adicionales visibles |
|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | Declarado | No evidenciado | No evidenciado (agendapro.com/ar/precios devolvió 404) | No evidenciado | No evidenciado | No evidenciado |
| 2 | Turnito | No evidenciado | Comprobado ("gratis sin límite de tiempo") | Comprobado: Plus $12.000, Advance $24.500, Pro $42.000 por mes, IVA incluido | ARS | Mensual; se puede pausar o cancelar (Declarado) | Comprobado (comisión por cobro: 5 %, 3,5 %, 1 % y 0 % según plan) |
| 3 | TurneroMed | Tercero | No evidenciado | Tercero, inconsistente (ver nota) | Inconsistente (rotulado USD) | Tercero (1, 3 o 6 meses) | No evidenciado |
| 4 | Doctoralia | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 5 | Reservo | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 6 | RAS Salud | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 7 | Medicloud | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 8 | Dentalink | No evidenciado (demo o acceso de prueba coordinado con ventas, Declarado) | No evidenciado | No evidenciado (cotización) | No evidenciado | Declarado (mensual, semestral o anual; sin permanencia) | No evidenciado |
| 9 | Doctocliq | Declarado (7 días sin tarjeta) | Declarado (plan GRATIS) | No evidenciado (página de precios devolvió 404) | No evidenciado | Declarado (semestral o anual con 25 % de descuento promocional) | No evidenciado |
| 10 | Dentidesk | Declarado (15 días) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 11 | Encuadrado | No evidenciado | No evidenciado | Comprobado: Esencial 0,6 UF, Profesional 1 UF, Avanzado 3 UF + IVA | CLP (UF) | Mensual | Comprobado (1 % por transferencias en el plan Esencial) |
| 12 | Clinicorp | No evidenciado | No evidenciado | Comprobado: Standard R$ 149,90 y Premium R$ 369,90 por mes; Enterprise a cotizar | BRL | Mensual, sin permanencia (Declarado) | No evidenciado |
| 13 | Simples Dental | Declarado (7 días sin tarjeta) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado |
| 14 | Clinic Cloud | Declarado (sin tarjeta) | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (sin costo de instalación) |
| 15 | Wati | No evidenciado | No evidenciado | No evidenciado | No evidenciado | No evidenciado | Declarado (cargos de Meta por la API, además de la plataforma) |
| 16 | Dentrix Ascend | No evidenciado | No evidenciado | No evidenciado (solicitar demo) | No evidenciado | No evidenciado | No evidenciado |
| 17 | Curve Dental | No evidenciado | No evidenciado | No evidenciado (cotización) | No evidenciado | No evidenciado | No evidenciado |
| 18 | Open Dental | No evidenciado | No evidenciado | No evidenciado ("precio accesible") | No evidenciado | No evidenciado | No evidenciado |

### A.11 Fortalezas, limitaciones, diferenciales y evidencia de adopción

| # | Producto | Fortalezas / diferenciales evidentes | Limitaciones evidentes | Adopción publicada |
|---|---|---|---|---|
| 1 | AgendaPro | Versión argentina dental; reserva sin registro; liberación automática del horario cancelado; señas integradas; tutoriales oficiales | Producto horizontal (también belleza y bienestar); precios argentinos no localizados; sin evidencia de odontograma, ARCA u obras sociales | Afirmación comercial: +135.000 profesionales, +20.000 negocios, 98 % de asistencia con confirmación |
| 2 | Turnito | Único con precios públicos en pesos; plan gratuito; seña que bloquea el turno | No odontológico; sin evidencia de cancelación, reprogramación, multiprofesional ni historia clínica | No evidenciado |
| 3 | TurneroMed | Local; WhatsApp y Mercado Pago (Tercero) | Sitio oficial no localizado; precios contradictorios | No evidenciado |
| 4 | Doctoralia | Marketplace con demanda de pacientes; app profesional bien calificada | Precios argentinos no evidenciados; la app se limita a planes Premium y First Class | Comprobado: 4,7/5 con unas 3.000 valoraciones (App Store España) |
| 5 | Reservo | Opera en Argentina; landing con mención a facturación ARCA | Landing argentina sin contenido funcional; odontología no evidenciada | Afirmación comercial: +36.500 profesionales y centros, unos 14 millones de reservas al año |
| 6 | RAS Salud | Ciclo de confirmar, cancelar y reprogramar documentado en su centro de ayuda; empresa argentina | Alcance odontológico no evidenciado; reprogramar exige cancelar y crear | No evidenciado |
| 7 | Medicloud | Declara la normativa argentina | Turnos e historia clínica solo planificados | No evidenciado |
| 8 | Dentalink | El más completo en lo clínico; agenda documentada (3 vistas, recursos, duración editable, estados configurables) | Sin precios; sin evidencia de Argentina, WhatsApp, Mercado Pago ni ARCA | Afirmación comercial: +15.000 clínicas, "+16 años" |
| 9 | Doctocliq | Plan gratuito; roles; odontograma y periodontograma; WhatsApp; Google Calendar | Argentina no evidenciada; facturación para otros países | Afirmación comercial: +20 países; menciones de Forbes y Endeavor Perú. La app de iOS no tiene valoraciones suficientes (Comprobado) |
| 10 | Dentidesk | Fichas por especialidad; prueba de 15 días | Facturación para Chile; WhatsApp "próximamente" | No evidenciado |
| 11 | Encuadrado | Precios públicos; cobros y confirmaciones por WhatsApp | No odontológico; solo Chile y México | No evidenciado |
| 12 | Clinicorp | Precios públicos; check-in con QR; app del paciente | Solo Brasil; odontograma no evidenciado | Afirmación comercial: +32.000 clínicas, +200 mil usuarios |
| 13 | Simples Dental | Odontograma online; confirmación por WhatsApp | Solo Brasil; precios no evidenciados | No evidenciado |
| 14 | Clinic Cloud | Agenda multisede con optimización de huecos; RGPD | España; odontología no evidenciada | Afirmación comercial: presencia en 12 países más |
| 15 | Wati | Flujo de confirmación con botones y derivación a una persona | No gestiona agenda; costo por mensaje | Afirmación comercial: +16.000 empresas, uptime 99,999 % |
| 16 | Dentrix Ascend | Seguridad (SOC 2, roles); IA en imágenes | Orientado a seguros de EE. UU.; sin precios | Afirmación comercial: "líder mundial" |
| 17 | Curve Dental | Perio charting; 100 % navegador | EE. UU. y Canadá; funciones solo para EE. UU. | Afirmación comercial: +100.000 usuarios, +6.000 consultorios, 4,6/5 con +500 reseñas |
| 18 | Open Dental | Odontograma 3D; reserva web | Modalidad y precio no evidenciados | No evidenciado |

**Notas de la tabla:**

- **TurneroMed:** según el resumen del buscador, la ficha de Capterra informa $65.000 por 1 mes, $555.000 por 3 meses y $48.333 por mes en el plan de 6 meses, rotulados en USD. El trimestral no es coherente con el mensual, y la moneda tampoco es coherente con un producto solo argentino. Se registra como **dato no confiable**.
- **Reservo:** https://reservo.cl/ y https://reservo.cl/ar/ devolvieron solo el título "Software médico con factura AFIP/ARCA en Argentina". Las funcionalidades provienen de prensa basada en información de la empresa.

---

## B. Matriz de puntuación (0 a 5)

**Pesos:** Turnos y automatización 25 %; Funcionalidad odontológica clínica 20 %; Integraciones locales y WhatsApp 15 %; Administración, cobros y facturación 15 %; Experiencia del paciente 10 %; Seguridad, exportación y trazabilidad 10 %; Precio y facilidad de adopción 5 %.

| # | Producto | Turnos y autom. (25 %) | Odontológica (20 %) | Integr. locales y WhatsApp (15 %) | Administración (15 %) | Paciente (10 %) | Seguridad (10 %) | Precio (5 %) | **Total ponderado** |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AgendaPro | 4 | 3 | 3 | 4 | 4 | 2 | 2 | **3,35** |
| 9 | Doctocliq | 4 | 4 | 2 | 4 | 3 | 2 | 3 | **3,35** |
| 8 | Dentalink | 4 | 4 | 1 | 4 | 3 | 4 | 1 | **3,30** |
| 12 | Clinicorp | 4 | 3 | 2 | 4 | 4 | 1 | 4 | **3,20** |
| 16 | Dentrix Ascend | 4 | 3 | 0 | 4 | 3 | 4 | 0 | **2,90** |
| 17 | Curve Dental | 4 | 4 | 0 | 4 | 3 | 2 | 0 | **2,90** |
| 11 | Encuadrado | 4 | 1 | 2 | 3 | 4 | 2 | 5 | **2,80** |
| 14 | Clinic Cloud | 4 | 1 | 2 | 4 | 3 | 3 | 2 | **2,80** |
| 2 | Turnito | 3 | 1 | 4 | 2 | 4 | 0 | 5 | **2,50** |
| 10 | Dentidesk | 3 | 4 | 1 | 3 | 2 | 0 | 2 | **2,45** |
| 13 | Simples Dental | 3 | 3 | 2 | 3 | 1 | 1 | 2 | **2,40** |
| 5 | Reservo | 2 | 2 | 2 | 3 | 2 | 2 | 0 | **2,05** |
| 18 | Open Dental | 3 | 3 | 0 | 2 | 2 | 0 | 1 | **1,90** |
| 4 | Doctoralia | 3 | 1 | 1 | 1 | 4 | 1 | 1 | **1,80** |
| 3 | TurneroMed | 2 | 1 | 3 | 2 | 1 | 0 | 2 | **1,65** |
| 15 | Wati | 2 | 0 | 4 | 0 | 3 | 2 | 1 | **1,65** |
| 6 | RAS Salud | 3 | 1 | 0 | 0 | 2 | 0 | 0 | **1,15** |
| 7 | Medicloud | 0 | 0 | 0 | 0 | 0 | 1 | 0 | **0,10** |

Ante empate de puntaje, el orden respeta la relevancia para Argentina.

**Nota metodológica:**

- **Escala:**
  - 0: no evidenciado.
  - 1: evidencia mínima.
  - 2: algunas subfuncionalidades del eje.
  - 3: la mayoría.
  - 4: el eje completo con evidencia declarada, o con evidencia comprobada parcial.
  - 5: el eje completo con evidencia comprobada.
- **Tope por tipo de evidencia:** un eje respaldado solo por afirmaciones del proveedor o de terceros **no supera 4**. Por eso solo los precios publicados alcanzan 5.
- **"No evidenciado" puntúa 0** en la subfuncionalidad: no se presume que el producto la tenga. Las funcionalidades planificadas o "próximamente" se tratan igual.
- **Integraciones locales:** se valoran WhatsApp, Mercado Pago y ARCA. Los productos sin presencia argentina puntúan 0 o 1 aunque tengan integraciones equivalentes en su país.
- **Seguridad, exportación y trazabilidad:** ningún sistema evidencia exportación de datos ni auditoría, así que ninguno supera 4 en este eje.
- **Total ponderado:** Σ(nota × peso) / 100.
- **Límites:** el ranking mide **evidencia pública**, no calidad real. Las notas son juicio del equipo y se revisan junto con la verificación de fuentes.

---

## C. Análisis competitivo

### C.1 Funcionalidades estándar de mercado

- Agenda online por profesional, con vista diaria y semanal, en la nube y con acceso móvil.
- Reserva por enlace público sin registro del paciente (AgendaPro, Turnito, Doctocliq, Encuadrado).
- Recordatorios automáticos con confirmación, con WhatsApp como canal dominante en Latinoamérica (AgendaPro, Doctocliq, Clinicorp, Simples Dental, Encuadrado).
- Estados del turno: confirmado y anulado (Dentalink y RAS Salud, comprobado).
- Historia clínica digital. En los productos odontológicos especializados, también odontograma (Dentalink, Doctocliq, Dentidesk, Simples Dental, Open Dental).
- Registro de pagos y caja. Prueba gratuita como vía de adopción.

### C.2 Funcionalidades diferenciadoras reales

Aparecen en pocos productos y tienen evidencia concreta:

- **Seña que bloquea el turno recién al acreditarse el pago** (Turnito, declarado; precios y comisiones comprobados). Ataca directamente el ausentismo.
- **Liberación del horario ante una cancelación:** AgendaPro de forma automática (declarado); RAS Salud desde el lado del paciente (comprobado).
- **Agenda diaria global por recurso**, con disponibilidad por especialidad, profesional y recurso (Dentalink, comprobado). Es lo más cercano a una agenda por sillón que se encontró.
- **Check-in con QR y app del paciente gratuita** (Clinicorp, declarado).
- **Marketplace que genera demanda de pacientes** (Doctoralia, AgendaPro, declarado).
- **Precios públicos y transparentes** (Turnito, Encuadrado, Clinicorp, comprobado). Es escaso en el segmento odontológico.

Las funciones de IA (notas por voz, copilotos clínicos, agentes de WhatsApp) están **declaradas** por Dentalink, Doctocliq, Clinicorp, Dentrix y Clinic Cloud, sin demostración pública. No se consideran diferenciales comprobados.

### C.3 Vacíos frecuentes del mercado argentino

1. **Facturación ARCA y obras sociales.** Ningún producto odontológico especializado evidencia facturación electrónica ARCA ni liquidación a obras sociales y prepagas. Reservo menciona ARCA solo en un título sin contenido; TurneroMed, seguimiento de seguros solo según un tercero.
2. **Sillón o box como recurso con reglas.** Ningún producto evidencia la prevención de solapamientos, ni por profesional ni por sillón o box. Dentalink muestra "recursos" en su agenda, pero no documenta qué ocurre si dos citas coinciden.
3. **Sobreturnos y lista de espera.** No están evidenciados en ninguno de los 18 sistemas.
4. **Exportación de datos y auditoría.** Tampoco están evidenciadas en ningún sistema. Dentalink documenta solo la importación.
5. **Precios en pesos.** Solo Turnito los publica, y no es odontológico. Los productos dentales funcionan por cotización.
6. **Normativa argentina.** Solo Medicloud declara (según un tercero) ajustarse a las leyes 25.326 (datos personales) y 26.529 (derechos del paciente). Nadie menciona la Ley 27.706 de historia clínica digital, reglamentada por el Decreto 393/2023, ni su exigencia de trazabilidad.

### C.4 Oportunidades de innovación

- **Agenda odontológica con doble recurso.** Profesional + sillón/box + prestación de duración variable, con prevención de solapamientos garantizada por reglas de negocio verificables. Es el vacío más concreto y es testeable dentro del alcance del TP.
- **Ciclo de vida del turno con trazabilidad.** Estados explícitos (reservado, confirmado, cancelado, atendido, ausente) con registro de quién cambió qué y cuándo. Responde a la normativa y ningún competidor lo evidencia.
- **Reprogramación como operación propia.** No como "cancelar y crear" (RAS Salud), conservando el historial del turno.
- **Lista de espera** que ofrezca automáticamente los horarios liberados por cancelaciones.
- **Precio transparente en pesos** para el odontólogo independiente.
- **Obra social o prepaga como dato del turno** desde el inicio, para habilitar más adelante la liquidación, que es el vacío local más grande.

---

## D. Recomendación final

### D.1 Cinco competidores prioritarios para analizar mediante demo

Por consigna del TP no se contactan proveedores ni se crean cuentas: el análisis se limita a demos, tutoriales y videos públicos.

1. **AgendaPro:** versión argentina dental, reserva sin registro, liberación de turnos y tutoriales oficiales disponibles.
2. **Dentalink:** referencia clínica más completa y agenda por recursos documentada.
3. **Doctocliq:** mejor puntaje ponderado; odontograma, roles y plan gratuito.
4. **Turnito:** referencia local de precios, seña con MercadoPago y WhatsApp.
5. **Reservo:** opera en Argentina y declara facturación ARCA, a confirmar.

### D.2 Tres productos de referencia para experiencia de usuario

1. **Turnito:** reserva por enlace sin registro ni descarga; turno bloqueado al pagar la seña.
2. **Dentalink:** agenda semanal con arrastre para reprogramar, duración editable y vista diaria global por recursos.
3. **AgendaPro:** confirmación doble y liberación automática del horario.

### D.3 MVP sugerido

**Imprescindible (MVP):**

1. Alta y gestión de profesionales, sillones o boxes y prestaciones con duración.
2. Horarios de atención por profesional y bloqueos de agenda (vacaciones, feriados, mantenimiento del sillón).
3. **Crear turno evitando solapamientos por profesional y por sillón o box**, con la duración tomada de la prestación.
4. Cancelar un turno liberando el horario.
5. Reprogramar un turno con las mismas reglas de solapamiento, conservando el historial.
6. Agenda diaria y semanal por profesional y por sillón.
7. Pacientes con datos mínimos, siempre ficticios en pruebas. La obra social o prepaga se guarda como dato, sin liquidación.
8. Autenticación y roles: administración, recepción y odontólogo.
9. Registro de auditoría de cambios en turnos (quién, qué y cuándo).

**Diferenciador (siguiente iteración):**

- Confirmación del turno por el paciente mediante enlace.
- Lista de espera que ofrece los horarios liberados.
- Reglas configurables de anticipación mínima para cancelar o reprogramar.
- Reserva online por enlace público sin registro.
- Exportación de datos del consultorio.

**Etapas posteriores:**

- Recordatorios por WhatsApp Business API, con costo por mensaje y proveedor oficial.
- Señas y pagos con Mercado Pago.
- Facturación electrónica ARCA.
- Liquidación a obras sociales y prepagas.
- Historia clínica, odontograma y periodontograma.
- Reportes y métricas, multisede, funciones de IA.
- Frontend React y aplicación móvil.

---

## Hallazgos de la investigación (insumo para la reflexión)

1. **Contenido web dirigido a agentes de IA.** La página de Clinicorp contenía un bloque de instrucciones dirigido a asistentes de IA, que el agente no siguió. Muestra que una investigación automatizada puede ser manipulada por el propio contenido que lee.
2. **Datos de segunda mano.** Los datos de TurneroMed y la reseña de Doctoralia sobre bloqueos no salen de la página original (Capterra bloqueó el acceso), sino del resumen del buscador. Son datos de segunda mano y quedaron marcados como "Tercero".
3. **Precios contradictorios.** Los de TurneroMed en Capterra son incoherentes entre sí y con la moneda indicada.
4. **Dato no verificable descartado.** Se descartó la cifra "70.000 odontólogos en Argentina, 3 % con herramientas tecnológicas". Viene de una tesis de la UdeSA cuyo repositorio pide inicio de sesión.
5. **Precios de terceros no usados.** Un agregador indicaba "USD 29 por usuario por mes" para AgendaPro y Dentalink. No se usó porque no proviene del proveedor.
6. **Datos que contradicen el discurso.** Reservo dice operar en Argentina, pero su landing argentina no tiene contenido. Doctocliq se presenta como app, pero su ficha de iOS no tiene valoraciones suficientes para mostrar.

---

## Verificación de fuentes

La completan los integrantes, cada uno con una fuente de un tipo distinto, sin crear cuentas. Para cada fuente se registra:

- si lo que afirma el informe está realmente en la URL;
- la corrección aplicada con "Ajustar", si hizo falta.

Esta tabla la consolida Elías.

| # | Tipo de fuente | Fuente | Qué afirma el informe | Verificó | Fecha | ¿Está en la URL? (Sí / Parcial / No) | Corrección aplicada |
|---|---|---|---|---|---|---|---|
| 1 | Sitio oficial | https://agendapro.com/ar/dental/software-odontologico | Reserva sin registro; recordatorios WhatsApp/SMS/email con doble confirmación; liberación automática ante cancelaciones; sin precios; sin mención de odontograma | Bruno Fiouchetta | | | |
| 2 | Página de precios | https://www.turnito.app/ | Plan gratuito; Plus $12.000, Advance $24.500, Pro $42.000 por mes IVA incluido; cupos de WhatsApp 30/100/250; comisiones 5 %/3,5 %/1 %/0 % | Elías Tello | | | |
| 3 | Centro de ayuda | https://intercom.help/softwaredentalink/es/articles/9493130-como-confirmar-anular-y-cambiar-citas | 3 vistas de agenda (diaria, semanal, diaria global por especialidad, profesional y recurso); cambio de fecha por arrastre; duración editable; estados configurables; no menciona sobrecupos ni sillones | Belén Calvo | | | |
| 4 | Tienda de aplicaciones | https://apps.apple.com/es/app/doctoralia-para-especialistas/id1237598188 | Desarrollador Docplanner; app solo para clientes Premium y First Class; 4,7/5 con unas 3.000 valoraciones | Hernán Gonzales | | | |
| 5 | Video / tutorial oficial | https://agendapro.com/bo/tutoriales | 2 manuales PDF y 7 videos en Vimeo, uno de ellos "Creación de Cuenta Recepcionista"; no hay tutoriales de agenda, recordatorios ni exportación | Joaquín Morán | | | |

**Fuentes adicionales sugeridas** si sobra tiempo:

- Ficha de TurneroMed en Capterra (precios inconsistentes; tipo marketplace).
- Centro de ayuda de RAS Salud (cancelación y reprogramación).
- Página de planes de Encuadrado (precios en UF).
- Página de Clinicorp (precios en R$ y bloque de instrucciones para IA).

---

## Referencias

Todas las fuentes se consultaron el 2026-10-08.

1. AgendaPro — Software odontológico (Argentina). https://agendapro.com/ar/dental/software-odontologico
2. AgendaPro — Tutoriales (manuales y videos oficiales). https://agendapro.com/bo/tutoriales
3. Turnito — Sitio oficial y planes. https://www.turnito.app/
4. Capterra — TurneroMed. https://www.capterra.com/p/10040798/TurneroMed/ (acceso automatizado bloqueado; datos tomados del resumen del buscador sobre las fichas regionales)
5. Apple App Store — Doctoralia para especialistas. https://apps.apple.com/es/app/doctoralia-para-especialistas/id1237598188
6. Reservo — Landing Argentina. https://reservo.cl/ar/
7. Chócale — "Reservo: la plataforma que ayuda a clínicas a recuperar hasta 50 horas semanales" (septiembre de 2026). https://chocale.cl/2026/09/reservo-la-plataforma-que-ayuda-a-clinicas-a-recuperar-hasta-50-horas-semanales/
8. RAS Salud — Centro de ayuda, "MrTurno: gestión de turnos". https://intercom.help/ayuda-ras-salud/en/articles/3843356-mrturno-gestion-de-turnos-confirmar-cancelar-etc
9. RAS Salud — Centro de ayuda, "Lección 5 de turnos: cancelación de turnos". https://intercom.help/ayuda-ras-salud/en/articles/3400146-leccion-5-de-turnos-cancelacion-de-turnos
10. Chrome-Stats — Medicloud, espejo de la ficha de Google Play. https://chrome-stats.com/d/com.woopi.medicloud
11. Dentalink — Sitio oficial. https://www.softwaredentalink.com/
12. Dentalink — Planes. https://web-es.softwaredentalink.com/en/planes
13. Dentalink — Centro de ayuda, "Cómo confirmar, anular y cambiar citas". https://intercom.help/softwaredentalink/es/articles/9493130-como-confirmar-anular-y-cambiar-citas
14. Dentalink — Centro de ayuda, "Cómo cargar tu listado de pacientes". https://intercom.help/softwaredentalink/es/articles/9488166-como-cargar-tu-listado-de-pacientes
15. Doctocliq — Sitio oficial. https://www.doctocliq.com/
16. Apple App Store — Doctocliq. https://apps.apple.com/us/app/doctocliq/id1445399223
17. Dentidesk — Sitio oficial. https://www.dentidesk.com/
18. Encuadrado — Sitio oficial y planes. https://encuadrado.com/
19. Clinicorp — Sitio oficial y planes. https://www.clinicorp.com/
20. Simples Dental — Sitio oficial. https://www.simplesdental.com/
21. Clinic Cloud — Sitio oficial. https://www.clinic-cloud.com/
22. Wati — "Automatizá los turnos clínicos por WhatsApp". https://www.wati.io/geo-argentina-es/automatiza-los-turnos-clinicos-por-whatsapp-sin-perder-el-cont
23. Dentrix Ascend — Sitio oficial. https://www.dentrixascend.com/
24. Curve Dental — Sitio oficial. https://www.curvedental.com/
25. Open Dental — Sitio oficial. https://www.opendental.com/
26. Argentina.gob.ar — Decreto 393/2023, reglamentario de la Ley 27.706. https://www.argentina.gob.ar/normativa/nacional/decreto-393-2023-387475/texto
27. Diario Judicial — "Salud digitalizada" (Ley 27.706 y Decreto 393/2023). https://www.diariojudicial.com/news-95586-salud-digitalizada
28. Develop Argentina — "Software para clínicas en Argentina: turnos y ausencias" (2026). Consultado como contexto; no aporta cifras con fuente. https://developargentina.com/blog/software-para-clinicas-argentina-turnos-ausencias-2026

**Fuentes consultadas y descartadas** (inaccesibles o no verificables):

- Capterra (fichas de Reservo y Doctoralia Pro): error 403.
- G2 (MedicAI): error 403.
- doctoralia.com.ar: conexión rechazada.
- Repositorio UdeSA, tesis sobre Sultapp/Consulmed: requiere inicio de sesión.
- Páginas de precios de AgendaPro (`/ar/precios`), Doctocliq (`/precios`) y Dentalink (`/precios`): error 404.
- DentalSoft Plus: no se localizó el sitio oficial.
