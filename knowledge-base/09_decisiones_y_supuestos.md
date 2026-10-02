# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Módulo Python sin GUI ni deploy
**Decisión**: implementar lógica de dominio pura, sin interfaz ni servidor.
**Contexto**: la consigna del TP lo permite ("API o módulo con su lógica de dominio").
**Alternativas consideradas**: web app con deploy; CLI.
**Justificación**: maximiza mantenibilidad y testeabilidad con el menor costo; el dominio queda portable a una futura API.
**Trade-offs aceptados**: sin demo visual; la UX se valida solo vía tests y scripts.

### DD-02 — Persistencia liviana (memoria / SQLite)
**Decisión**: puerto repositorio con adaptador en memoria por defecto y SQLite opcional.
**Contexto**: se necesita persistir turnos, pacientes y profesionales sin infra.
**Alternativas consideradas**: Postgres/Docker; archivos JSON sueltos.
**Justificación**: cero deploy, tests deterministas, migración simple a SQLite real.
**Trade-offs aceptados**: sin concurrencia real ni multi-instancia.

### DD-03 — Anti-solapamiento como invariante dura
**Decisión**: RN-AG-01/02 rechazan cualquier solapeamiento (salvo sobreturno explícito).
**Contexto**: es el diferencial verificado de DentalSoft/Dentiqa en el informe.
**Alternativas consideradas**: permitir solape con warning.
**Justificación**: el error de agenda es el costo central del problema (sillón ocioso o doble-reserva).
**Trade-offs aceptados**: la urgencia real pasa por sobreturno marcado, no por violar la regla.

### DD-04 — Notificaciones y pagos como stubs
**Decisión**: puertos con stubs en memoria para WhatsApp y Mercado Pago.
**Contexto**: el informe muestra que la API oficial y ARCA son el costo mayor; quedan para etapas posteriores.
**Justificación**: el dominio queda listo para enchufar lo real sin reescribir reglas.
**Trade-offs aceptados**: sin envío ni cobro real en v1.0.

## Supuestos inferidos

### SU-01 — Un consultorio, pocos sillones
**Supuesto**: escala equipo pequeño (< 50 personas), un solo tenant.
**Origen**: respuesta P0-scale.
**Riesgo si es falso**: el modelo multi-sede/tenant exigiría rediseño de agenda.
**Cómo validar**: confirmar con la cátedra si el TP contempla sucursales.

### SU-02 — System_type = módulo/API interna
**Supuesto**: `system_type: api` (no web app desplegada).
**Origen**: ajuste explícito del usuario (módulo Python sin GUI ni deploy).
**Riesgo si es falso**: bajo; el dominio es portable igual.
**Cómo validar**: ya validado por el usuario en esta sesión.

### SU-03 — Stack Python libre
**Supuesto**: Python 3.11+, pytest, stdlib.
**Origen**: respuesta P4 (libre elección) + ajuste del usuario.
**Riesgo si es falso**: la cátedra podría exigir otro stack.
**Cómo validar**: verificar consigna escrita de la materia.
