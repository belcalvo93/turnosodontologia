# Descripción General

## Stack tecnológico

| Capa | Tecnologías | Versión mínima |
|---|---|---|
| Lenguaje | Python | 3.11 |
| Dominio | Módulo puro (dataclasses, sin framework) | — |
| Persistencia | En memoria (dict) con puerto repositorio; SQLite opcional | sqlite3 stdlib |
| Tests | pytest | 8.x |
| Calidad | ruff (lint) — opcional para el TP | — |

Sin interfaz gráfica por consigna ("puede ser una API o un módulo con su lógica de dominio"). Sin deploy: se ejecuta como librería importable + suite de tests.

## Arquitectura general

```
turnosodontologia/
├── domain/          # entidades + reglas (sin I/O)
│   ├── paciente.py / profesional.py / turno.py
│   └── rules.py     # validaciones RN-*
├── application/     # casos de uso (agendar, reprogramar, lista de espera)
├── infrastructure/  # repositorios en memoria / sqlite + audit log
└── tests/           # tests por regla y flujo
```

El dominio no conoce persistencia ni notificaciones: agenda y caja operan sobre puertos (repositorios, reloj, notificador stub). Esto permite probar toda la lógica sin servidor y mantener el código extensible (prioridad: mantenibilidad).

## Integraciones externas

| Servicio | Propósito | Tipo | Estado en v1.0 |
|---|---|---|---|
| WhatsApp (recordatorios) | Avisar y confirmar turnos | Stub en memoria | Puerto definido, sin envío real |
| Mercado Pago (señas) | Cobro de seña/reserva | Stub en memoria | Puerto definido, sin cobro real |
| Google Calendar | Sincronizar agenda | No | Posterior (Turnia es la única referencia AR con GCal+Meet) |
| ARCA / PUCO / OS | Facturación y validación | No | Posterior (diferenciador; solo DentalTec/ClinIA/DoctorYa lo declaran) |

## API interna (módulo)

Casos de uso expuestos como funciones del paquete `application`:

- `agendar_turno(paciente_id, profesional_id, inicio, duracion_min, prestacion)` → Turno o error de dominio.
- `confirmar_turno(turno_id)`, `cancelar_turno(turno_id, motivo)`, `reprogramar_turno(turno_id, nuevo_inicio)`.
- `bloquear_franja(profesional_id, desde, hasta, motivo)`, `agregar_sobreturno(...)` con validación explícita.
- `ofrecer_hueco(lista_espera_id)` — reasigna el primer hueco compatible.
- `registrar_cobro(turno_id, monto, medio)` — caja mínima.
