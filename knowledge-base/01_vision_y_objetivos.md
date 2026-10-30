# Visión y Objetivos

> Fuente única: `docs/discovery/informe-discovery.md` (versión final, 18 sistemas relevados, 5 fuentes verificadas). Las referencias tipo "D.3" o "C.3" apuntan a secciones del informe. Todo lo que no figura textualmente en el informe se marca **Supuesto del equipo** y se registra en [10_preguntas_abiertas.md](10_preguntas_abiertas.md).

## Propósito del sistema

Sistema de turnos y agenda para consultorios odontológicos de Argentina, centrado en un núcleo de agenda que evita solapamientos de turnos por profesional y por sillón o box, con duración variable según la prestación y trazabilidad de todo cambio.

Contexto: el relevamiento de 18 soluciones (informe, resumen ejecutivo y C.3) muestra que ningún producto evidencia la prevención de solapamientos como regla, ni por profesional ni por sillón o box, y que ninguno evidencia auditoría ni exportación de datos. Esa agenda con doble recurso (profesional + sillón + prestación) es la oportunidad concreta que se ataca (C.4) y es verificable con tests dentro del alcance del trabajo práctico (UTN, Metodología I).

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|-------|--------------------|-----------------------|
| Administración | Dejar configurado el consultorio (profesionales, sillones, prestaciones, horarios, bloqueos, usuarios) | Consultar el registro de auditoría de los turnos |
| Recepción | Dar, cancelar y reprogramar turnos sin errores de superposición | Cargar pacientes con sus datos mínimos; ver la agenda diaria y semanal |
| Odontólogo | Ver su agenda diaria y semanal | Ver en qué sillón atiende cada turno |

(Los objetivos secundarios de cada rol son Supuesto del equipo, salvo que el informe (D.3 #8) establece los tres roles.)

## Alcance v1.0 (MVP)

El MVP es exactamente la sección **D.3 "Imprescindible (MVP)"**, ítems 1 a 9 del informe:

1. Alta y gestión de profesionales, sillones o boxes y prestaciones con duración.
2. Horarios de atención por profesional y bloqueos de agenda (vacaciones, feriados, mantenimiento del sillón).
3. Crear turno evitando solapamientos por profesional y por sillón o box, con la duración tomada de la prestación.
4. Cancelar un turno liberando el horario.
5. Reprogramar un turno con las mismas reglas de solapamiento, conservando el historial.
6. Agenda diaria y semanal por profesional y por sillón.
7. Pacientes con datos mínimos, siempre ficticios en pruebas. La obra social o prepaga se guarda como dato, sin liquidación.
8. Autenticación y roles: administración, recepción y odontólogo.
9. Registro de auditoría de cambios en turnos (quién, qué y cuándo).

## Fuera de alcance del MVP (futuro)

Nada de esta lista forma parte del MVP. Se detalla en [06_funcionalidades.md](06_funcionalidades.md), sección "Funcionalidades NO MVP".

**Diferenciador (siguiente iteración), D.3:**
- Confirmación del turno por el paciente mediante enlace.
- Lista de espera que ofrece los horarios liberados.
- Reglas configurables de anticipación mínima para cancelar o reprogramar.
- Reserva online por enlace público sin registro.
- Exportación de datos del consultorio.

**Etapas posteriores, D.3:**
- Recordatorios por WhatsApp Business API (con costo por mensaje y proveedor oficial).
- Señas y pagos con Mercado Pago.
- Facturación electrónica ARCA.
- Liquidación a obras sociales y prepagas.
- Historia clínica, odontograma y periodontograma.
- Reportes y métricas, multisede, funciones de IA.
- Frontend React completo y aplicación móvil (el frontend mínimo en TypeScript es el change C-18, posterior al MVP).

## Métricas de éxito

Medibles dentro del alcance del trabajo práctico (propuesta del equipo, **Supuesto del equipo**):

- Cero turnos superpuestos por profesional o por sillón/box en la suite de tests (incluidos los casos de borde de intervalos contiguos).
- Todo cambio de turno (crear, cancelar, reprogramar) genera un registro de auditoría con quién, qué y cuándo.
- Los tests de dominio corren sin base de datos ni HTTP.
- Cada regla de [05_reglas_de_negocio.md](05_reglas_de_negocio.md) tiene al menos un test asociado.

## Datos de prueba

Todos los datos de ejemplo, semillas y tests son **ficticios** y están rotulados como tales ("Paciente Ficticio 1", DNI "00000001 (ficticio)", "Obra Social Ficticia A"). No se usan datos reales de pacientes en ningún entorno del repositorio.
