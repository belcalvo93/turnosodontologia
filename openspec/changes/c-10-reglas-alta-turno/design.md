# Design — C-10 reglas-alta-turno

## Context

C-10 es lógica de dominio puro. Ver `proposal.md` (Why) para la motivación. Estado actual: no hay código (`app/` inexistente); el contrato de entrada es el de C-02 (`Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo`, `solapan(a, b)` semiabierto, errores de dominio). Restricciones duras: `domain` no importa FastAPI ni `app/db`/`app/api`; reloj inyectado (`ahora` por parámetro); `snake_case` + type hints (Python 3.11).

## Goals / Non-Goals

**Goals:**
- Módulo backend `app/domain/reglas_turno.py` con `validar_alta(...)` como función pura testeable sin DB ni HTTP.
- Suite de tests unitarios robusta con Python + PyTest en `tests/domain/test_reglas_turno.py` (un caso por ejemplo de verificación de RN-TUR-01/03/04/05/08/12 y RN-PRO-01/02).
- Errores de dominio precisos para que C-11 los traduzca a 409/422.

**Non-Goals:**
- Sin componentes de interfaz gráfica de usuario ni endpoints HTTP.
- Sin persistencia, migraciones, autenticación, RBAC ni auditoría (eso es C-01/C-03/C-11).
- Sin `validar_cancelacion` ni `validar_reprogramacion` (eso es C-12/C-13; solo se deja el gancho `excluir_turno_id`).

## Decisions

- **Stack: Python 3.11 + PyTest (se descarta Java/JUnit).** Por qué: el proyecto fija Python + FastAPI + SQLite + pytest en `AGENTS.md` y `knowledge-base/08`; introducir Java duplicaría toolchain y rompería la regla `domain` puro sin framework. Alternativa considerada: Java + JUnit — rechazada por inconsistencia con el stack y con C-01/C-02.
- **Función pura con contexto explícito.** Firma: `validar_alta(inicio, prestacion, profesional_id, sillon_id, paciente_id, horarios, bloqueos, turnos_activos, ahora, excluir_turno_id=None) -> Turno`. Por qué: respeta `08 §Cómo se usa el dominio` (el router carga contexto, el dominio valida); permite tests sin fixtures de DB. Alternativa: que el dominio consulte repositorios — rechazada (acopla dominio a DB).
- **Orden fijo de validación: fin → franja → bloqueos → solapes.** Por qué: los errores más baratos y específicos primero (`DatoInvalido` por duración, `FueraDeHorario`, `DentroDeBloqueo`, `ConflictoAgenda`); C-11 puede mapear en ese mismo orden. Todos los intervalos con `solapan()` semiabierto `[inicio, fin)`.
- **Filtrado por estado antes de solapar.** Solo se comparan turnos con `estado == "reservado"` y con `id != excluir_turno_id`. Por qué: implementa RN-TUR-06/08 sin que el llamador tenga que pre-filtrar.

## Risks / Trade-offs

- [C-02 aún no archivado] El contrato de modelos puede cambiar → Mitigación: `validar_alta` solo usa campos primitivos documentados en `04_modelo_de_datos.md` (`inicio/fin`, `duracion_minutos`, `dia_semana/hora_desde/hora_hasta`, `alcance/recurso_id/inicio/fin`, `estado`); si C-02 cambia nombres, el ajuste queda aislado en esta función.
- [Supuestos SE-02/SE-03/SE-04] `sillon_id` obligatorio, solape por paciente, sin sobreturnos con excepción → Mitigación: codificados como reglas con tests (RN-TUR-02/12/11); si cambian, el impacto queda en C-10 según `CHANGES.md`.
- [Zona horaria SE-05] Fechas locales sin offset → Mitigación: `ahora` inyectado y comparación naive consistente; `CLINIC_TIMEZONE` solo en config (C-01).

## Migration Plan

Sin migración: change nuevo, sin datos ni endpoints previos. Rollback: eliminar `reglas_turno.py` y sus tests; ningún otro módulo lo importa todavía (C-11 lo adoptará).

## Open Questions

Ninguna que cambie specs o tareas. SE-09 (turnos afectados por bloqueo) y SE-24 (feriado de consultorio) quedan para C-09/C-16, no afectan `validar_alta`.
