# Proposal — C-10 reglas-alta-turno

## Why

Los consultorios gestionan turnos con herramientas que no evitan solapamientos por profesional ni por sillón y no validan horario ni bloqueos antes de reservar. Este change concentra esa validación en dominio puro para que crear (y luego reprogramar) un turno sea determinista y testeable sin DB ni HTTP.

Seleccionamos el change C-10 (reglas-alta-turno) porque pertenece al MVP recomendado, es lógica de dominio puro y nos permite aislar el desarrollo minimizando dependencias (solo C-01 y C-02), cubriendo perfectamente los escenarios requeridos de validación.

## What Changes

- Nueva función pura `app/domain/reglas_turno.py::validar_alta(...)`: recibe prestación, horarios del profesional, bloqueos y turnos activos ya cargados; devuelve el turno armado o lanza error de dominio.
- Cálculo `fin = inicio + duracion_minutos` de la prestación (RN-TUR-01); el cliente no envía `fin`.
- Validación de franja única de atención (RN-PRO-01/02) → `FueraDeHorario` si no encaja completo en una franja.
- Validación de bloqueos de profesional y de sillón con intervalos semiabiertos (RN-TUR-05) → `DentroDeBloqueo`.
- Validación de solapamiento por profesional, sillón (RN-TUR-03/04) y paciente (RN-TUR-12); los cancelados no cuentan y se soporta `excluir_turno_id` para reprogramación (RN-TUR-08) → `ConflictoAgenda`.
- Reutiliza `solapan()` de intervalos semiabiertos `[inicio, fin)` y errores de dominio de C-02 (`ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`, `DatoInvalido`).

## Capabilities

### New Capabilities

- `reglas-alta-turno`: validación de alta de un turno en dominio puro (cálculo de fin, franja, bloqueos y solapamientos) sin persistencia ni HTTP.

### Modified Capabilities

Ninguna (no hay specs previas; `openspec/specs/` está vacío).

## Impact

- Afecta solo `app/domain/` (nuevo archivo `reglas_turno.py` + tests en `tests/domain/`).
- Depende del contrato de C-02 (`models.py`, `intervalos.py`, `errores.py`) y del scaffold de C-01; no toca `app/api/` ni `app/db/`.
- Desbloquea C-11 (`crear-turno`), que llamará a `validar_alta` dentro de una transacción.
