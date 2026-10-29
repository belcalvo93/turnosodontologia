# Proposal — C-02 dominio-base

## Why

Las reglas de turnos (`C-10`, `C-12`, `C-13`), horarios (`C-08`) y bloqueos (`C-09`) necesitan un núcleo común en Python puro con modelos de dominio inmutables, comparación de intervalos semiabiertos `[inicio, fin)`, validación temporal con reloj inyectado y jerarquía de errores de dominio. Aunque parte de este contrato se adelantó al implementar `C-10`, falta completar `es_futuro(turno, ahora)` (`RN-TUR-09`), el error `TurnoNoModificable` con su traducción HTTP (`RN-GLO-01`), los tests exigidos por el scope de `C-02` y la especificación formal en OpenSpec para destrabar `C-08`, `C-09` y el resto del roadmap.

## What Changes

- Se completa `app/domain/intervalos.py` agregando `es_futuro(turno: Intervalo, ahora: datetime) -> bool`, que evalúa `turno.inicio > ahora` recibiendo el reloj inyectado como parámetro (`RN-TUR-09`, regla dura 2).
- Se completa `app/domain/errores.py` agregando `TurnoNoModificable(ErrorDominio)` para representar el rechazo al intentar cancelar o reprogramar un turno pasado, en curso o ya cancelado (`RN-TUR-09`, `RN-TUR-10`).
- Se registra `TurnoNoModificable: (409, "turno_no_modificable")` en `MAPEO_DOMINIO` de `app/api/errores.py` (y en `README.md`) para cumplir `RN-GLO-01` y el test de invariante `test_todo_error_de_dominio_de_la_app_tiene_entrada_en_el_mapeo` de `C-03`.
- Se consolidan y amplían los tests unitarios en `tests/domain/test_intervalos.py` cubriendo todos los casos exigidos por `C-02`: turnos contiguos válidos, solapamiento parcial, contención, mismo inicio, y `es_futuro` con reloj fijo (antes, igual y después del inicio), además de la verificación en `tests/api/test_errores.py` para `turno_no_modificable`.

**Fuera de alcance:** reglas de alta (`C-10`, ya completado), reglas de cancelación y reprogramación (`C-12` y `C-13`), persistencia SQLite y endpoints de recursos o turnos.

## Capabilities

### New Capabilities

- `dominio-base`: modelos base de dominio (`Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo`), comparación de intervalos semiabiertos `solapan(a, b)`, evaluación temporal `es_futuro(turno, ahora)` con reloj inyectado y jerarquía de errores de dominio puros.

### Modified Capabilities

- `errores-api`: agrega la traducción de `TurnoNoModificable` a HTTP `409` con `codigo` `turno_no_modificable`.

## Impact

- **Archivos modificados:** `app/domain/intervalos.py`, `app/domain/errores.py`, `app/api/errores.py`, `tests/domain/test_intervalos.py`, `tests/domain/test_estructura.py`, `tests/api/rutas_prueba.py`, `tests/api/test_errores.py`, `README.md`.
- **Dependencias:** requiere `C-01` (`foundation-setup`). Desbloquea formalmente `C-08` (`horarios-atencion`) y el cierre/archivo de `C-09` (`bloqueos`).
