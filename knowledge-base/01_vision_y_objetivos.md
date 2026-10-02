# Visión y Objetivos

## Propósito del sistema

Ordenar la agenda de un consultorio odontológico pequeño mediante un módulo Python de lógica de dominio (sin interfaz gráfica ni deploy) que gestione pacientes, profesionales y turnos con reglas explícitas.

El caos actual —llamadas, WhatsApp dispersos, sobre-turnos y ausentismo sin trazabilidad— se reemplaza por un núcleo de dominio testeable que valida solapamientos, reprograma y registra cada cambio.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Paciente | Conseguir y reprogramar su turno sin fricción | Recibir confirmación/recordatorio; ver sus turnos |
| Secretaria (recepción) | Gestionar la agenda diaria sin sobre-turnos | Bloquear franjas, registrar ausencias, listar espera |
| Odontólogo | Atender con agenda predecible y ficha mínima | Ver turnos del día, registrar estado clínico básico |

## Alcance v1.0

- Altas/bajas de pacientes y profesionales (con especialidad y sillón).
- Creación, confirmación, cancelación y reprogramación de turnos con validación anti-solapamiento.
- Bloqueos de agenda (feriados, vacaciones, franjas no laborables).
- Lista de espera simple con reasignación de huecos.
- Odontograma básico y caja mínima (cobro particular + seña) según MVP "agenda + clínica básica".
- Persistencia liviana en memoria o SQLite; sin servidor ni interfaz gráfica.
- Reglas de negocio codificadas con códigos RN-XX-NN y audit log en memoria.

## Fuera de alcance

- Interfaz gráfica web o móvil; deploy en servidor o nube.
- Facturación ARCA con CAE, validación PUCO/obras sociales en línea (diferenciador posterior).
- Integración real con WhatsApp Business API o Mercado Pago (se modelan como puertos/stubs).
- Historia clínica completa, radiografías, receta ReNaPDiS.
- Multi-consultorio / multi-tenant.

## Métricas de éxito

- Cero turnos solapados aceptados por el dominio (100% de intentos inválidos rechazados en tests).
- Reprogramación autónoma posible sin intervención manual en el 100% de los casos simples.
- Cobertura de tests del dominio ≥ 80% en reglas de agenda.
