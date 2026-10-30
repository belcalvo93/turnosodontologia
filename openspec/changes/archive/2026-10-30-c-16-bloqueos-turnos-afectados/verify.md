# Verify — C-16 bloqueos-turnos-afectados

## Resultado de la suite completa

```
python -m pytest -q
759 passed, 1 warning in 74.99s (0:01:14)
```

- Línea de base de `main` al iniciar el change: **744 tests** (`744 passed, 1 warning in 73.22s`).
- Tests nuevos de C-16: **15** (8 de dominio + 3 de repositorio + 4 de API).
- Total esperado y obtenido: **744 + 15 = 759**.
- Además se editaron dos aserciones de tests ya existentes de C-09 en `tests/api/test_bloqueos.py` (tarea 4.1); no cambian el conteo.
- El único warning es el `StarletteDeprecationWarning` de `fastapi.testclient` (`httpx` → `httpx2`), preexistente.

## Validación OpenSpec

```
openspec validate c-16-bloqueos-turnos-afectados --strict
Change 'c-16-bloqueos-turnos-afectados' is valid
```

No se corrió `validate --specs --strict`: no pertenece a este change.

## Trazabilidad escenario → test (10 escenarios del delta `bloqueos`)

Los tests de API están en `tests/api/test_bloqueos.py`; los de repositorio, en `tests/api/test_repositorio_turnos.py`; los de dominio, en `tests/domain/test_bloqueos_turnos_afectados.py`.

| # | Escenario | Test |
|---|---|---|
| 1 | Alta válida de bloqueo para un profesional | `tests/api/test_bloqueos.py::test_post_bloqueos_para_profesional_y_sillon_responde_201` (editado en 4.1: respuesta incluye `turnos_afectados: []`) |
| 2 | Rechazo por intervalo inválido | `tests/api/test_bloqueos.py::test_post_bloqueos_con_inicio_mayor_o_igual_que_fin_responde_422` (preexistente de C-09) |
| 3 | Rechazo por recurso inexistente | `tests/api/test_bloqueos.py::test_post_bloqueos_con_recurso_inexistente_responde_422` (preexistente de C-09) |
| 4 | Crear un bloqueo reporta los turnos reservados solapados (RN-TUR-05 con RN-TUR-04) | `tests/api/test_bloqueos.py::test_post_bloqueos_profesional_lista_los_reservados_en_rango_ordenados_sin_auditoria` (parcial + interno reportados, con los 8 campos). La exclusión del turno de otro recurso la cubren `tests/domain/test_bloqueos_turnos_afectados.py::test_bloqueo_de_profesional_excluye_turnos_de_otro_profesional` y `tests/api/test_repositorio_turnos.py::test_listar_reservados_del_recurso_devuelve_los_reservados_del_profesional_en_rango` |
| 5 | Crear un bloqueo de sillón reporta solo los turnos de ese sillón | `tests/api/test_bloqueos.py::test_post_bloqueos_sillon_lista_solo_los_turnos_de_ese_sillon` + `tests/domain/test_bloqueos_turnos_afectados.py::test_bloqueo_de_sillon_excluye_turnos_de_otro_sillon_y_de_otro_profesional` + `tests/api/test_repositorio_turnos.py::test_listar_reservados_del_recurso_con_alcance_sillon_devuelve_solo_los_de_ese_sillon` |
| 6 | Los turnos contiguos al intervalo no se reportan (RN-TUR-04) | **Sin test de API.** Cubierto en dominio por `tests/domain/test_bloqueos_turnos_afectados.py::test_turnos_contiguos_al_bloqueo_no_se_reportan` y en repositorio por `tests/api/test_repositorio_turnos.py::test_listar_reservados_del_recurso_excluye_los_turnos_contiguos_al_borde` |
| 7 | Los turnos cancelados no se reportan (RN-TUR-08) | `tests/api/test_bloqueos.py::test_post_bloqueos_profesional_lista_los_reservados_en_rango_ordenados_sin_auditoria` (2 `reservado` + 1 `cancelado` en rango; solo salen los 2) + `tests/domain/test_bloqueos_turnos_afectados.py::test_turnos_cancelados_no_se_reportan` |
| 8 | `turnos_afectados` llega vacío cuando no hay turnos superpuestos | `tests/api/test_bloqueos.py::test_post_bloqueos_profesional_con_intervalo_vacio_responde_turnos_afectados_vacio` (alcance `profesional`; el escenario nombra `sillon`, el caso vacío de sillón se ejerce además en `test_post_bloqueos_para_profesional_y_sillon_responde_201`) |
| 9 | Los turnos afectados se listan ordenados por inicio y no se modifican | `tests/api/test_bloqueos.py::test_post_bloqueos_profesional_lista_los_reservados_en_rango_ordenados_sin_auditoria` (orden, `estado = reservado` vía `GET /turnos/{id}` y sin filas nuevas en `auditoria_turno`) + `tests/domain/test_bloqueos_turnos_afectados.py::test_ordena_por_inicio_ascendente` (tres turnos fuera de orden, como en el escenario) |
| 10 | `GET /bloqueos` no incluye `turnos_afectados` | `tests/api/test_bloqueos.py::test_get_bloqueos_no_incluye_turnos_afectados` + `tests/api/test_bloqueos.py::test_recepcion_y_odontologo_reciben_403_al_crear_o_eliminar_y_200_al_listar` (editado en 4.1) |

Huecos y matices, sin inventar cobertura:

- **Escenario 6:** no hay test a nivel API; queda cubierto por dominio y repositorio.
- **Escenario 9:** el test de API reserva 2 turnos (09:15 y 09:45), no los 3 del escenario (11:00, 10:00, 10:30). El orden con 3 turnos desordenados se prueba solo en dominio.
- **Escenario 8:** el test dedicado usa `alcance = "profesional"`, no `"sillon"` como dice el escenario.
- **Escenario 4:** el test de API del profesional no incluye un turno de otro recurso; esa exclusión se verifica en dominio y repositorio.

Cobertura adicional (no exigida por un escenario puntual): `tests/domain/test_bloqueos_turnos_afectados.py::test_reporta_turno_reservado_que_solapa_parcialmente`, `::test_desempata_por_id_ascendente_con_inicio_igual` y `::test_no_depende_del_reloj` (D-A3).

## Trazabilidad de reglas RN → test de dominio

Todos en `tests/domain/test_bloqueos_turnos_afectados.py`.

| Regla | Tests |
|---|---|
| RN-TUR-04 (intervalos semiabiertos `[inicio, fin)`, contiguos válidos) | `test_turnos_contiguos_al_bloqueo_no_se_reportan`; `test_reporta_turno_reservado_que_solapa_parcialmente` (solape parcial sí reportado) |
| RN-TUR-05 (el bloqueo afecta por `profesional_id` o `sillon_id`) | `test_reporta_turno_reservado_que_solapa_parcialmente`; `test_bloqueo_de_profesional_excluye_turnos_de_otro_profesional`; `test_bloqueo_de_sillon_excluye_turnos_de_otro_sillon_y_de_otro_profesional` |
| RN-TUR-08 (el turno cancelado no ocupa agenda) | `test_turnos_cancelados_no_se_reportan` |

Los tests de dominio corren sin base de datos ni HTTP (Regla dura 11): solo importan `app.domain.models` y `app.domain.reglas_turno`. No queda ninguna de las tres RN sin test.

## Datos ficticios

Revisado con `git diff main...HEAD -- tests/`:

- `tests/api/test_bloqueos.py` (fixture `contexto_bloqueos`): pacientes con DNI `"00000001 (ficticio)"` y `"00000002 (ficticio)"`; profesionales `Odontólogo Ficticio A` / `Odontóloga Ficticia B`; sillones `"Sillón 1 (ficticio)"` / `"Sillón 2 (ficticio)"`; prestación `"Consulta ficticia"`; usuarios `recepcion_ficticia` y `admin_ficticio`; motivo `"Urgencia ficticia"`.
- `tests/domain/test_bloqueos_turnos_afectados.py`: los pacientes se referencian por id; los comentarios documentan DNIs `"0000000N (ficticio)"` y el motivo del bloqueo es `"Motivo ficticio"`. No se construyen pacientes reales.
- `tests/api/test_repositorio_turnos.py`: los tests nuevos reutilizan los helpers preexistentes (`_agregar_recursos_alternativos`, `_insertar_turno`), con DNIs `"30111222 (ficticio)"` y `"30333444 (ficticio)"`, ya rotulados antes de C-16.
- No se encontraron DNIs sin el sufijo `(ficticio)`, ni nombres, correos, contraseñas o secretos reales en los datos nuevos.
- No se editó nada fuera de este `verify.md` y de las marcas de `tasks.md`.

## Archivos del change

Modificados:

- `app/domain/reglas_turno.py`: `turnos_afectados_por_bloqueo`.
- `app/db/repositorio_turnos.py`: `listar_reservados_del_recurso`.
- `app/api/bloqueos.py`: `BloqueoCreadoSalida` y respuesta de `POST /bloqueos`.
- `tests/api/test_bloqueos.py`, `tests/api/test_repositorio_turnos.py`.

Nuevos:

- `tests/domain/test_bloqueos_turnos_afectados.py`

## Pendiente

- **5.4** (sincronizar el delta a `openspec/specs/bloqueos/spec.md`) queda para `/opsx:archive`; no se hizo aquí.
