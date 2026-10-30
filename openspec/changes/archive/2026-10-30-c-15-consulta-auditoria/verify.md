# Verify — C-15 consulta-auditoria

## Resultado de la suite completa

```
.venv\Scripts\python.exe -m pytest -q
744 passed, 1 warning in 58.64s
```

- Línea de base de `main` al iniciar el change: **718 tests**.
- Tests nuevos de C-15: **26** (6 de repositorio + 20 de API).
- Total esperado y obtenido: **718 + 26 = 744**.
- El único warning es el `StarletteDeprecationWarning` de `fastapi.testclient`, preexistente.

## Validación OpenSpec

```
openspec validate c-15-consulta-auditoria --strict
Change 'c-15-consulta-auditoria' is valid
```

No se corrió `validate --specs --strict`: los specs `agenda` y `horarios-atencion` ya fallaban en `main` por falta de `## Purpose` y no pertenecen a este change.

## Trazabilidad escenario → test (16 escenarios del delta `auditoria-turnos`)

| # | Requirement | Escenario | Test |
|---|---|---|---|
| 1 | Consulta del historial | Historial de un turno creado, reprogramado y cancelado | `tests/api/test_auditoria.py::test_historial_de_tres_acciones_devuelve_tres_registros_en_orden` |
| 2 | Consulta del historial | Turno sin más registros que el alta | `tests/api/test_auditoria.py::test_turno_recien_creado_devuelve_solo_el_alta` |
| 3 | Consulta del historial | Un turno cancelado conserva su historial completo | `tests/api/test_auditoria.py::test_historial_de_tres_acciones_devuelve_tres_registros_en_orden` + `tests/api/test_repositorio_auditoria.py::test_listar_auditoria_devuelve_solo_los_registros_del_turno` |
| 4 | Contrato del registro | Antes y después como objetos JSON | `tests/api/test_auditoria.py::test_antes_y_despues_son_objetos_con_las_ocho_claves` |
| 5 | Contrato del registro | Antes nulo solo en el alta | `tests/api/test_auditoria.py::test_antes_es_nulo_solo_en_el_alta` + `tests/api/test_repositorio_auditoria.py::test_listar_auditoria_deja_antes_en_none_para_el_alta` |
| 6 | Contrato del registro | La reprogramación describe el cambio | `tests/api/test_auditoria.py::test_reprogramacion_conserva_el_id_y_cambia_el_inicio` |
| 7 | Identificación sin datos sensibles | Nunca se expone el hash de la contraseña | `tests/api/test_auditoria.py::test_respuesta_sin_datos_sensibles` |
| 8 | Identificación sin datos sensibles | Un usuario desactivado sigue identificado | `tests/api/test_auditoria.py::test_usuario_desactivado_sigue_apareciendo` |
| 9 | Identificación sin datos sensibles | Sin datos del paciente en el snapshot | `tests/api/test_auditoria.py::test_respuesta_sin_datos_sensibles` + `test_antes_y_despues_son_objetos_con_las_ocho_claves` |
| 10 | Turno obligatorio y existencia | Sin `turno_id` | `tests/api/test_auditoria.py::test_turno_id_ausente_422` |
| 11 | Turno obligatorio y existencia | `turno_id` no positivo | `tests/api/test_auditoria.py::test_turno_id_cero_422` + `test_turno_id_negativo_422` + `test_turno_id_no_entero_422` |
| 12 | Turno obligatorio y existencia | Turno inexistente | `tests/api/test_auditoria.py::test_turno_inexistente_404_no_encontrado` |
| 13 | Acceso restringido | Recepción no puede consultar | `tests/api/test_auditoria.py::test_recepcion_403_sin_permiso` |
| 14 | Acceso restringido | Odontólogo no puede consultar | `tests/api/test_auditoria.py::test_odontologo_403_sin_permiso` |
| 15 | Acceso restringido | Sin token | `tests/api/test_auditoria.py::test_sin_token_401_no_autenticado` |
| 16 | Acceso restringido | El rol sin permiso no descubre si el turno existe | `tests/api/test_auditoria.py::test_rol_sin_permiso_con_turno_inexistente_recibe_403_no_404` |

Cobertura adicional (no exigida por un escenario puntual): orden con desempate por `id`, parseo de JSON, `username` y formato de `ocurrio_en` en `tests/api/test_repositorio_auditoria.py` y `tests/api/test_auditoria.py::test_ocurrio_en_tiene_formato_iso_de_segundos`.

## Verificación de archivos protegidos

`git diff --stat` para los archivos que C-15 no debía tocar: **vacío** (sin cambios).

```
git diff --stat -- app/db/esquema.sql app/db/repositorio_turnos.py app/api/turnos.py app/api/errores.py
(sin salida)
```

Archivos modificados por el change (permitidos):

- `app/domain/models.py`: `AccionAuditoria` y `RegistroAuditoria`.
- `app/main.py`: import y montaje de `router_auditoria`.

Archivos nuevos:

- `app/db/repositorio_auditoria.py`
- `app/api/auditoria.py`
- `tests/api/test_repositorio_auditoria.py`
- `tests/api/test_auditoria.py`

Sin secretos ni credenciales reales: todos los usuarios, pacientes y contraseñas de los tests son ficticios (`password_hash="x"` solo en fixtures de repositorio).

## Nota de implementación

El diseño D6 mencionaba un `NoEncontrado` propio; el proyecto no tiene esa clase y `GET /turnos/{id}` ya usa `HTTPException(status_code=404)`, que el mapeo global traduce a `codigo: "no_encontrado"`. C-15 sigue ese patrón existente sin agregar errores nuevos.
