# Preguntas Abiertas

## Inconsistencias detectadas

### IN-01 — Turnos del paciente: ¿auto-confirmados o con secretaria?
**Documento A dice**: el paciente solicita y la secretaria confirma (RN-AG-07, `03_actores_y_roles.md`).
**Documento B dice**: el flujo 2 permite reprogramación "autónoma" del paciente.
**Impacto**: ambigüedad en permisos del TP.
**Resolución propuesta**: solicitar crea `solicitado`; reprogramar un turno ya confirmado mantiene `confirmado` (no baja de nivel). Confirmar con la cátedra.

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|-----------|----------|---------|---------|
| Alta | ¿Duración por prestación fija o configurable por profesional? | Sprint 1 (RN-AG-04) | Cátedra / usuario |
| Alta | ¿La seña es obligatoria al reservar (modelo Doctocliq) u opcional? | Sprint 1 (RN-CA-03) | Usuario |
| Media | ¿SQLite desde el día uno o memoria + migración posterior? | Sprint 2 | Equipo técnico |
| Media | ¿Odontograma con estados extendidos o los 5 mínimos alcanzan? | Sprint 2 | Odontólogo referente |
| Baja | ¿Receta ReNaPDiS y ARCA entran al TP o quedan como roadmap? | Lanzamiento | Cátedra |
| Baja | [DISCOVERY] `system_type` se fijó en `api` por ajuste del usuario; si la cátedra exige otro formato, actualizar `02` y `08`. | Lanzamiento | Usuario |
