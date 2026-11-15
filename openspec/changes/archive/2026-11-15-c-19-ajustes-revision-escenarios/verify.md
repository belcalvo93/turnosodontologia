# Verify — C-19 ajustes-revision-escenarios

## Suite

- Línea de base (0.1): `789 passed`.
- Final (5.1): `795 passed` (base + 6 tests nuevos: 1 trazabilidad, 4 seed, 1 turnos), 0 fallos.
- `openspec validate c-19-ajustes-revision-escenarios --strict`: válido. `openspec validate --all --strict`: 19 passed, 0 failed.

## Escenario -> test

| Escenario | RN | Test | Estado |
|---|---|---|---|
| RN-TUR-13 con un test distinto del de RN-TUR-04 hace fallar la verificación | RN-TUR-13, RN-TUR-04 | `tests/test_trazabilidad.py::test_rn_tur_13_con_un_test_distinto_del_de_rn_tur_04_falla_nombrando_rn_tur_13` | nuevo |
| Solo la contraseña de odontología crea solo odontologo_demo | RN-ACC-04 | `tests/api/test_seed_demo.py::test_arranque_solo_con_contrasena_de_odontologo_crea_solo_odontologo_demo` y `::test_sembrar_demo_solo_con_hash_de_odontologo_crea_solo_odontologo_demo` | nuevo |
| Solo la contraseña de recepción crea solo recepcion_demo | RN-ACC-04 | `tests/api/test_seed_demo.py::test_arranque_solo_con_contrasena_de_recepcion_crea_solo_recepcion_demo` y `::test_sembrar_demo_solo_con_hash_de_recepcion_crea_solo_recepcion_demo` | nuevo |
| La desactivación del profesional no borra auditoría | RN-REC-03 | `tests/api/test_turnos.py::test_desactivar_el_profesional_no_borra_ni_modifica_la_auditoria_del_turno` | nuevo |
| Profesional desactivado después de la reserva | RN-REC-03 | `tests/api/test_turnos.py::test_profesional_desactivado_despues_de_la_reserva_conserva_el_turno_y_rechaza_nuevos_422` (afirma `estado == "reservado"`, línea 695) | existente, sin cambios |
| Catálogo completo al arrancar (matrículas ficticias) | RN-PAC-03 | `tests/api/test_seed_demo.py::test_sembrar_demo_crea_catalogo_completo_con_duraciones_matriculas_y_obra_social` (`"(ficticia)"` en ambas, líneas 51, 58, 62) | existente, sin cambios |
| Los recursos sembrados aceptan turnos | RN-TUR-02, RN-TUR-09 | `tests/api/test_flujo_e2e.py` pasos 2-4 (lunes 2026-01-05 10:00, `sillon_id` Sillón 1, 201 con turno completo; reprogramar y cancelar con éxito) | existente, sin cambios |
| Los nombres demo están rotulados | RN-PAC-03 | `tests/api/test_seed_demo.py::test_datos_ficticios_rotulados_en_pacientes_y_profesionales` (`f"{nombre} {apellido}".lower()`, línea 215) | existente, sin cambios |

## Evidencia de mutaciones (caracterización: pasan sin mutación; rojo por mutación; revertidas)

1. Tarea 1.2 — comentado el bloque RN-TUR-13/RN-TUR-04 de `tests/trazabilidad.py`: el test nuevo falla en `assert len(problemas) == 1` (`assert 0 == 1`). Revertido con `git checkout -- tests/trazabilidad.py`; `tests/test_trazabilidad.py` 6 passed.
2. Tarea 2.3 (recepción) — `recepcion_demo` creado siempre con `password_hash_recepcion or password_hash_admin` en `app/db/seed.py`: fallan los tests de solo-odontología (unidad y arranque) con `At index 1 diff: 'recepcion_demo' != 'odontologo_demo'`. Revertido; `test_seed_demo.py` 16 passed.
3. Tarea 2.3 (odontólogo) — mutación simétrica: fallan los tests de solo-recepción (unidad y arranque) con `Left contains one more item: 'odontologo_demo'`. Revertido; 16 passed.
4. Tarea 3.3 — `INSERT` extra en `auditoria_turno` dentro de `actualizar_profesional`: el test nuevo falla en la comparación de `_auditorias` (`Left contains one more item: (1, 'cancelar', ...)`). Revertido con `git checkout -- app/db/repositorio_profesionales.py`; `test_turnos.py` 49 passed.

Tras cada reversión, `git --no-pager diff --stat -- app/ tests/trazabilidad.py` quedó vacío.

## Archivos protegidos

`git status` / `git diff --stat` finales: solo cambian `tests/test_trazabilidad.py`, `tests/api/test_seed_demo.py`, `tests/api/test_turnos.py` y la carpeta del change (sin trackear). Sin cambios en `app/`, `frontend/`, `knowledge-base/`, `docs/`, `openspec/specs/`, `openspec/changes/archive/`, `tests/trazabilidad.py` ni `CHANGES.md`.
