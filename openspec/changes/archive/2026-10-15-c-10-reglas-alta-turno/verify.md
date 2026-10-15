# Verify — C-10 reglas-alta-turno

- **Fecha:** 2026-10-15
- **Responsable:** Joaquín Moran
- **Comando:** `pytest tests/domain/ -v` (OpenSpec no ofrece una fase de verificación propia en esta instalación; la suite se ejecutó a mano)
- **Entorno:** Windows, Python 3.13.7, pytest 9.1.1
- **Resultado:** 32 passed in 0.09s. Sin tests en rojo.

## Cobertura de los escenarios del spec

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Alta exitosa de un turno | `test_fin_se_calcula_con_prestacion_de_30_minutos`, `test_turno_armado_queda_reservado_con_los_recursos_pedidos` | PASSED |
| Validación fallida por solapamiento del profesional | `test_solapamiento_del_profesional_lanza_conflicto_agenda` | PASSED |
| Turnos contiguos | `test_contiguo_mismo_profesional_y_sillon_se_acepta`, `test_borde_turno_que_empieza_cuando_termina_otro_se_acepta` | PASSED |
| Turno fuera del horario de atención | `test_franja_turno_que_excede_el_cierre_lanza_fuera_de_horario` | PASSED |
| Turno dentro de un bloqueo | `test_bloqueo_de_sillon_rechaza_turno_en_ese_sillon`, `test_bloqueo_de_sillon_no_afecta_a_otro_sillon` | PASSED |

## Chequeos adicionales

- `app/domain/` no importa FastAPI, Pydantic, sqlite3, `app/db` ni `app/api` (regla dura 1 de AGENTS.md).
- `app/domain/` no llama a `now()`, `today()` ni `utcnow()` (regla dura 2 de AGENTS.md).
- Prueba de mutación en la tarea 2.3: con `solapan()` cambiado a intervalos cerrados, fallan los tests de turnos contiguos. El archivo se restauró desde git.

## Observaciones del apply

- El design menciona `DatoInvalido` por duración inválida, pero ni el spec ni las tareas lo piden: no se implementó (RN-REC-01 lo valida al crear la prestación, C-05). Decisión registrada en Engram.
- Durante la tarea 2.2 se detectó y corrigió un caso en el que `excluir_turno_id=None` salteaba en silencio los turnos sin id.
- La tarea 2.3 no tuvo fase RED porque el comportamiento ya existía; se validó con la prueba de mutación.