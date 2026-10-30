# Verify — C-14 agenda

> Verificación del change C-14 tras completar el apply con Strict TDD.

## 1. TDD Cycle Evidence

| Tarea | Archivo de Test | Capa | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1 - 1.2 | `tests/api/test_repositorio_agenda.py` | Repositorio / DB | ✅ 625/625 | ✅ ModuleNotFound | ✅ 4/4 pasaron | ✅ 6 casos (bordes semiabiertos y multidia) | ✅ Reutilización `COLUMNAS_TURNO` y `_bloqueo_desde_fila` |
| 2.1 | `tests/domain/test_permisos_agenda.py` | Dominio puro | ✅ 631/631 | ✅ Import error | ✅ 7/7 pasaron | ✅ 7 casos (roles, vinculación, fechas) | ✅ Sin dependencias |
| 2.2 - 3.2 | `tests/api/test_agenda.py` | API / Routers | ✅ 638/638 | ✅ 10 failed (404) | ✅ 12/12 pasaron | ✅ 12 casos (profesionales, sillones, RBAC, 422, 404, 401) | ✅ Clean schemas Pydantic |

## 2. Cobertura de Escenarios del Spec (`specs/agenda/spec.md`)

- [x] **Escenario 1 (Consulta cronológica de agenda de profesional):** Verificado en `test_agenda_profesional_recepcion_y_admin_200_cronologico`. Devuelve turnos y bloqueos ordenados por `inicio ASC`.
- [x] **Escenario 2 (Exclusión estricta de turnos cancelados):** Verificado en `test_agenda_profesional_excluye_turnos_cancelados`. El turno con `estado = 'cancelado'` no se incluye.
- [x] **Escenario 3 (Validación de rango temporal invertido):** Verificado en `test_agenda_profesional_rango_invertido_422` y `test_agenda_sillon_rango_invertido_422`. Responde 422 con código `dato_invalido`.
- [x] **Escenario 4 (Odontólogo consulta su propia agenda profesional):** Verificado en `test_agenda_profesional_odontologo_propio_200`. Responde 200 OK cuando `usuario.profesional_id == profesional_id`.
- [x] **Escenario 5 (Odontólogo intenta consultar agenda de colega):** Verificado en `test_agenda_profesional_odontologo_ajeno_403`. Responde 403 `sin_permiso`.
- [x] **Escenario 6 (Odontólogo intenta consultar agenda de sillón):** Verificado en `test_agenda_sillon_odontologo_403`. Responde 403 `sin_permiso`.
- [x] **Escenario 7 (Consulta válida de agenda de sillón):** Verificado en `test_agenda_sillon_recepcion_y_admin_200_cronologico`. Responde 200 OK con turnos y bloqueos asignados al sillón.

## 3. Estado de la Suite de Tests

```text
650 passed, 1 warning in 83.01s
```
- Total tests previos: 625 passed.
- Total tests incorporados en C-14: 25 tests (6 repositorio + 7 dominio + 12 endpoints API).
- Fallas: 0.

## 4. Verificación de Reglas Duras (`AGENTS.md`)

- **Regla 1 (Aislamiento de dominio):** `app/domain/usuarios.py` no importa FastAPI ni SQLite. Verificado con `test_estructura.py`.
- **Regla 2 (Reloj inyectado):** La consulta no llama `datetime.now()` dentro de dominio.
- **Regla 3 (Intervalos semiabiertos):** Consultas SQL con `inicio < hasta AND fin > desde` respetando `[desde, hasta)`.
- **Regla 4 (Consultas parametrizadas):** Todas las consultas en `app/db/repositorio_agenda.py` usan `?`.
- **Regla 7 (Errores consistentes):** Mapeo global consistente a 401, 403, 404 y 422 con JSON en español.
- **Regla 8 (Sin reglas de negocio en routers):** Reglas de visualización de agenda y validación de rango delegadas en funciones puras de `app/domain/usuarios.py`.
- **Regla 10 (Datos ficticios):** Fixtures con datos etiquetados explícitamente como ficticios.
- **Regla 12 (Estilo):** Tipado estricto con Python 3.11 y `snake_case`.
