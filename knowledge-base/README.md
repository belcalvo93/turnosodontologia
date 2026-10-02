# Turnos Odontología — Base de Conocimiento

Módulo Python de lógica de dominio para gestión de turnos (sin GUI ni deploy). Fuente: discovery interactivo + informe de mercado en `reports/Sistemas odontológicos turnos Argentina.md`.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance v1.0, fuera de alcance |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack Python, arquitectura de puertos, API interna del módulo |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Paciente, secretaria, odontólogo; matriz RBAC lógica |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Entidades, ERD textual, constraints, seed data |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas RN-AG/PA/PR/CL/CA/LE + excepciones globales |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas e historias US-001…US-040 con criterios |
| [07_flujos_principales.md](07_flujos_principales.md) | Reserva, reprogramación, cancelación+lista de espera, cobro |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, directorios, seguridad, env vars |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-01…DD-04, SU-01…SU-03 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | IN-01 + preguntas priorizadas |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

Módulo Python sin GUI que ordena la agenda de un consultorio pequeño: anti-solapamiento duro, reprogramación con trazabilidad, lista de espera FIFO, odontograma dígito-dos mínimo y caja con seña. WhatsApp, Mercado Pago y ARCA/PUCO quedan como puertos stub para etapas posteriores, tal como recomienda el análisis competitivo.
