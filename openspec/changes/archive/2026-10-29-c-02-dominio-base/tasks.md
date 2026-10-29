# Tasks — C-02 dominio-base

## 1. Intervalos semiabiertos y reloj inyectado (`RN-TUR-04`, `RN-TUR-09`)

- [x] 1.1 Agregar los tests unitarios en `tests/domain/test_intervalos.py` para `solapan` con mismo inicio y para `es_futuro(turno, ahora)` con reloj fijo (`ahora` antes del inicio → `True`, `ahora` igual al inicio → `False`, `ahora` después del inicio → `False`), e implementar `es_futuro(intervalo: Intervalo, ahora: datetime) -> bool` en `app/domain/intervalos.py`

## 2. Error `TurnoNoModificable` y mapeo HTTP (`RN-GLO-01`)

- [x] 2.1 Agregar `TurnoNoModificable(ErrorDominio)` en `app/domain/errores.py` y verificar en `tests/domain/test_estructura.py` el aislamiento de `app/domain/` (sin imports de FastAPI, SQLite, `app.db` ni `app.api`, sin llamadas a `now()`/`today()`) y la jerarquía de errores y modelos de `C-02`
- [x] 2.2 Registrar `TurnoNoModificable: (409, "turno_no_modificable")` en `MAPEO_DOMINIO` de `app/api/errores.py`, agregar la ruta de prueba en `tests/api/rutas_prueba.py` y el caso en `tests/api/test_errores.py`, y actualizar la tabla de códigos de error en `README.md`

## 3. Verificación integral del change

- [x] 3.1 Ejecutar la suite completa `pytest tests -v` y verificar que todos los tests de dominio y de API pasan en verde
- [x] 3.2 Documentar el resultado en `openspec/changes/archive/2026-10-29-c-02-dominio-base/verify.md`, archivar el change en `openspec/changes/archive/`, sincronizar `openspec/specs/` y marcar `C-02` como `[x]` en `CHANGES.md`
