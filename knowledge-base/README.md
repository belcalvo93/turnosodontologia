# Turnos Odontológicos — Base de Conocimiento

Base de conocimiento generada a partir de `docs/discovery/informe-discovery.md` (versión final: 18 sistemas relevados, 5 fuentes verificadas). Todo el contenido que no figura en el informe está marcado como **Supuesto del equipo**. Todos los datos de ejemplo son ficticios.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance MVP (informe D.3 ítems 1 a 9) y fuera de alcance |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack provisional (Python + FastAPI + pytest + SQLite), arquitectura general, resumen de API |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Administración, recepción y odontólogo; matriz RBAC; rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Entidades, ERD, restricciones y datos semilla ficticios |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas RN-PRO, RN-REC, RN-TUR, RN-PAC, RN-ACC, RN-AUD con origen y forma de verificación |
| [06_funcionalidades.md](06_funcionalidades.md) | Historias de usuario del MVP y sección separada de funcionalidades NO MVP |
| [07_flujos_principales.md](07_flujos_principales.md) | Login, crear, cancelar y reprogramar turno, bloqueos, agenda, auditoría |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Estructura `app/domain`, `app/api`, `app/db`, `tests`; seguridad; variables de entorno |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones (D-01 stack provisional) y supuestos |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias, hallazgos del informe (IF) y supuestos del equipo (SE), priorizados |

## Quick Start para Desarrolladores

1. Entender el dominio: [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos: [04](04_modelo_de_datos.md)
3. Entender las reglas: [05](05_reglas_de_negocio.md)
4. Entender la arquitectura: [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar: [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar: [10](10_preguntas_abiertas.md) y las decisiones provisionales de [09](09_decisiones_y_supuestos.md)

## Resumen Ejecutivo

Sistema de turnos y agenda para consultorios odontológicos de Argentina. El MVP es un núcleo de agenda con profesionales, sillones o boxes y prestaciones de duración variable, que evita solapamientos por profesional y por sillón, permite cancelar liberando el horario y reprogramar conservando el historial, y audita cada cambio (quién, qué y cuándo), con roles de administración, recepción y odontólogo. El stack es Python + FastAPI + pytest + SQLite (provisional), con el dominio separado del framework para poder testear las reglas sin base de datos ni HTTP. WhatsApp, pagos, ARCA, obras sociales e historia clínica quedan fuera del MVP.
