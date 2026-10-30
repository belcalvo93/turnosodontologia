# Verify — C-17 seed-y-flujo-e2e

## Resultado de la suite completa

```
.venv\Scripts\python.exe -m pytest -q
785 passed, 1 warning
```

- Línea de base de `main` al iniciar el change: **759 tests** (`759 passed, 1 warning`).
- Tests nuevos de C-17: **26**
  - `tests/api/test_config.py`: **3** (lectura y defaults de `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD`).
  - `tests/api/test_flujo_e2e.py`: **3** (flujo completo de 6 pasos, reutilización del hueco liberado al cancelar y rechazo `409` sin ensuciar auditoría).
  - `tests/api/test_seed_demo.py`: **12** (6 de unidad sobre `sembrar_demo` + 6 de arranque en `lifespan`, incluyendo 2 parametrizados para `test` y `production`).
  - `tests/api/test_turnos.py`: **3** (caracterización de `RN-REC-03`: sillón desactivado, profesional desactivado y conservación de auditoría).
  - `tests/test_trazabilidad.py`: **5** (verificación real de las 31 reglas y 4 casos sintéticos sobre `tests/trazabilidad.py`).
- Total esperado y obtenido: **759 + 26 = 785**.
- `tests/api/test_seed.py` (12 tests preexistentes) sigue en verde **sin modificaciones**.
- El único warning es el `StarletteDeprecationWarning` de `fastapi.testclient` (`httpx` → `httpx2`), preexistente.

## Validación OpenSpec

```
openspec validate c-17-seed-y-flujo-e2e --strict
Change 'c-17-seed-y-flujo-e2e' is valid
```

## Trazabilidad escenario → test (8 requirements del delta: 6 de `acceso-usuarios`, 1 de `base-tecnica` y 1 de `turnos`)

| # | Capability | Requirement | Escenario | Test |
|---|---|---|---|---|
| 1 | `acceso-usuarios` | 1. Usuario administrador de desarrollo | Creación en development | `tests/api/test_seed.py::test_en_development_con_la_variable_crea_admin_demo_y_permite_el_login` + `tests/api/test_seed_demo.py::test_arranque_solo_con_seed_admin_password_siembra_catalogo_y_no_crea_odontologo_ni_recepcion` |
| 2 | `acceso-usuarios` | 1. Usuario administrador de desarrollo | Arranque repetido idempotente | `tests/api/test_seed_demo.py::test_dos_arranques_en_development_dejan_exactamente_32_filas_y_los_mismos_hashes` + `tests/api/test_seed.py::test_dos_arranques_sobre_la_misma_base_dejan_un_solo_admin_demo` |
| 3 | `acceso-usuarios` | 1. Usuario administrador de desarrollo | Sin seed fuera de development | `tests/api/test_seed_demo.py::test_arranque_fuera_de_development_no_siembra_nada` (`test`, `production`) + `tests/api/test_seed.py::test_en_test_con_la_variable_no_crea_usuarios` |
| 4 | `acceso-usuarios` | 1. Usuario administrador de desarrollo | Sin seed si falta la contraseña | `tests/api/test_seed_demo.py::test_arranque_sin_seed_admin_password_no_siembra_nada` + `tests/api/test_seed.py::test_en_development_sin_la_variable_arranca_y_no_crea_usuarios` |
| 5 | `acceso-usuarios` | 2. Catálogo demo de desarrollo | Catálogo completo al arrancar | `tests/api/test_seed_demo.py::test_sembrar_demo_crea_catalogo_completo_con_duraciones_matriculas_y_obra_social` + `tests/api/test_seed_demo.py::test_arranque_con_las_tres_contrasenas_crea_los_tres_usuarios_el_catalogo_y_permite_login` |
| 6 | `acceso-usuarios` | 2. Catálogo demo de desarrollo | Los recursos sembrados aceptan turnos | `tests/api/test_flujo_e2e.py::test_flujo_e2e_seis_pasos_login_alta_reprogramar_cancelar_y_auditoria` |
| 7 | `acceso-usuarios` | 3. Horarios de atención demo | Horarios de lunes a viernes para ambos profesionales | `tests/api/test_seed_demo.py::test_sembrar_demo_crea_veinte_horarios_lunes_a_viernes_para_ambos_profesionales` |
| 8 | `acceso-usuarios` | 3. Horarios de atención demo | Un segundo arranque no duplica franjas | `tests/api/test_seed_demo.py::test_dos_arranques_en_development_dejan_exactamente_32_filas_y_los_mismos_hashes` |
| 9 | `acceso-usuarios` | 4. Usuarios demo de recepción y odontología | Seed completo con las tres contraseñas | `tests/api/test_seed_demo.py::test_arranque_con_las_tres_contrasenas_crea_los_tres_usuarios_el_catalogo_y_permite_login` + `tests/api/test_seed_demo.py::test_sembrar_demo_vincula_odontologo_demo_al_profesional_a_y_guarda_hashes_argon2id` |
| 10 | `acceso-usuarios` | 4. Usuarios demo de recepción y odontología | Sin variable de contraseña no hay usuario para ese rol | `tests/api/test_seed_demo.py::test_arranque_solo_con_seed_admin_password_siembra_catalogo_y_no_crea_odontologo_ni_recepcion` + `tests/api/test_seed_demo.py::test_sembrar_demo_no_crea_usuarios_sin_su_contrasena` |
| 11 | `acceso-usuarios` | 4. Usuarios demo de recepción y odontología | Un usuario demo existente no se modifica | `tests/api/test_seed_demo.py::test_un_usuario_demo_existente_no_se_modifica` |
| 12 | `acceso-usuarios` | 5. Contraseñas del seed desde el entorno | La base guarda hashes, no contraseñas | `tests/api/test_seed_demo.py::test_sembrar_demo_vincula_odontologo_demo_al_profesional_a_y_guarda_hashes_argon2id` + `tests/api/test_seed.py::test_en_development_con_la_variable_crea_admin_demo_y_permite_el_login` |
| 13 | `acceso-usuarios` | 5. Contraseñas del seed desde el entorno | La contraseña demo no queda en el archivo de la base | `tests/api/test_seed.py::test_la_contrasena_del_seed_no_queda_en_el_archivo_de_la_base` |
| 14 | `acceso-usuarios` | 6. Datos ficticios del seed | Los DNI demo están rotulados | `tests/api/test_seed_demo.py::test_datos_ficticios_rotulados_en_pacientes_y_profesionales` |
| 15 | `acceso-usuarios` | 6. Datos ficticios del seed | Los nombres demo están rotulados | `tests/api/test_seed_demo.py::test_datos_ficticios_rotulados_en_pacientes_y_profesionales` |
| 16 | `base-tecnica` | 7. Trazabilidad de reglas de negocio a tests | Todas las reglas están mapeadas | `tests/test_trazabilidad.py::test_todas_las_reglas_del_repositorio_estan_mapeadas_sin_hallazgos` |
| 17 | `base-tecnica` | 7. Trazabilidad de reglas de negocio a tests | Una regla sin fila hace fallar la verificación | `tests/test_trazabilidad.py::test_una_regla_sin_fila_falla_nombrando_el_codigo` |
| 18 | `base-tecnica` | 7. Trazabilidad de reglas de negocio a tests | Un test citado inexistente hace fallar la verificación | `tests/test_trazabilidad.py::test_un_test_citado_inexistente_falla_nombrando_el_nodo` |
| 19 | `base-tecnica` | 7. Trazabilidad de reglas de negocio a tests | No aplica solo vale para RN-GLO-02 y con motivo | `tests/test_trazabilidad.py::test_no_aplica_solo_vale_para_rn_glo_02_y_con_motivo` |
| 20 | `base-tecnica` | 7. Trazabilidad de reglas de negocio a tests | Una regla sin test verificable no rompe la tabla | `tests/test_trazabilidad.py::test_una_tabla_completa_con_rn_glo_02_con_motivo_no_reporta_nada` |
| 21 | `turnos` | 8. Conservación del turno histórico al desactivar un recurso | Sillón desactivado después de la reserva | `tests/api/test_turnos.py::test_sillon_desactivado_despues_de_la_reserva_conserva_el_turno_y_rechaza_nuevos_422` |
| 22 | `turnos` | 8. Conservación del turno histórico al desactivar un recurso | Profesional desactivado después de la reserva | `tests/api/test_turnos.py::test_profesional_desactivado_despues_de_la_reserva_conserva_el_turno_y_rechaza_nuevos_422` |
| 23 | `turnos` | 8. Conservación del turno histórico al desactivar un recurso | La desactivación no borra auditoría | `tests/api/test_turnos.py::test_desactivar_el_sillon_no_borra_ni_modifica_la_auditoria_del_turno` |

## Conteo de filas del seed demo

Con `APP_ENV=development` y las tres variables (`SEED_ADMIN_PASSWORD`, `SEED_RECEPCION_PASSWORD` y `SEED_ODONTOLOGO_PASSWORD`) definidas, `sembrar_demo` deja exactamente **32 filas** de forma idempotente:

| Tabla | Filas | Detalle |
|---|---|---|
| `profesional` | 2 | `"Odontólogo Ficticio A"` (`"0001 (ficticia)"`), `"Odontóloga Ficticia B"` (`"0002 (ficticia)"`) |
| `sillon` | 2 | `"Sillón 1"`, `"Sillón 2"` |
| `prestacion` | 3 | `"Consulta ficticia"` (30 min), `"Limpieza ficticia"` (45 min), `"Tratamiento ficticio"` (60 min) |
| `horario_atencion` | 20 | 2 profesionales × 5 días (`0`..`4`) × 2 franjas (`09:00`-`13:00` y `14:00`-`18:00`) |
| `paciente` | 2 | `"Paciente Ficticio 1"` (`"00000001 (ficticio)"`, con obra social) y `"Paciente Ficticio 2"` (`"00000002 (ficticio)"`, sin obra social) |
| `usuario` | 3 | `admin_demo`, `recepcion_demo`, `odontologo_demo` (vinculado a `profesional_a`) |
| **Total** | **32** | Idempotente ante múltiples arranques |

## Confirmación de archivos protegidos

Verificado con `git diff --stat`:

```
git diff --stat -- tests/api/test_seed.py app/db/esquema.sql app/api/ knowledge-base/ CHANGES.md docs/discovery/ .active-orchestrator-state.json
(sin salida)
```

Ninguno de los archivos protegidos fue modificado.
