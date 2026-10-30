# Verify — C-12 cancelar-turno

- **Fecha:** 2026-10-30
- **Responsable:** Bruno Fiouchetta
- **Comando:** `python -m pytest tests -q`. OpenSpec no tiene una fase de verificación propia en esta instalación, así que la suite se corrió a mano.
- **Entorno:** Windows 10, Python 3.13.5, pytest 9.2.0. Rama `bruno-c12-cancelar-turno` con `main` mergeado.
- **Resultado:** `667 passed`, 1 warning (deprecación de `httpx` en el TestClient, ajena al change). Sin tests fallidos ni salteados.
  - Baseline después de mergear `main`: 654 tests en verde.
  - Nuevos de C-12 en el apply: 13 (3 en `tests/api/test_repositorio_turnos.py` y 10 en `tests/api/test_cancelar_turno.py`). Los 4 de `tests/domain/test_cancelar_turno.py` son de la tarea 1.1 y ya estaban en el baseline.
  - 654 + 13 = 667.

## Cobertura de los escenarios del spec

| Escenario del spec | Test que lo cubre | Resultado |
|---|---|---|
| Cancelación exitosa de un turno futuro | `test_cancelar_turno.py::test_recepcion_cancela_turno_futuro_200_y_registra_auditoria`, `test_administracion_tambien_puede_cancelar` | PASSED |
| Rechazo de cancelación de turno pasado o en el instante exacto de inicio | `test_cancelar_turno.py::test_turno_en_el_instante_exacto_de_inicio_409_y_sigue_reservado`, `test_turno_pasado_409_y_sigue_reservado` | PASSED |
| Rechazo de segunda cancelación sobre un turno ya cancelado | `test_cancelar_turno.py::test_segunda_cancelacion_409_sin_nueva_auditoria` | PASSED |
| Cancelación de turno inexistente | `test_cancelar_turno.py::test_turno_inexistente_404` | PASSED |
| Reservar nuevamente un hueco liberado por cancelación | `test_cancelar_turno.py::test_tras_cancelar_se_puede_reservar_el_mismo_hueco_201` (y su contraprueba `test_sin_cancelar_el_mismo_hueco_sigue_ocupado_409`) | PASSED |
| Odontólogo intenta cancelar un turno | `test_cancelar_turno.py::test_odontologo_no_puede_cancelar_403_y_sigue_reservado` | PASSED |

Además, la exigencia de token del requirement de acceso (`401`) la cubre `test_sin_token_401`, y la atomicidad (`RN-AUD-03`) la cubre `test_repositorio_turnos.py::test_cancelar_turno_si_falla_la_auditoria_el_turno_sigue_reservado`.

## Chequeos adicionales

- `app/domain/` no llama a `datetime.now()`, `date.today()` ni `utcnow()`, y no importa FastAPI, `sqlite3`, `app.db` ni `app.api` (reglas duras 1 y 2).
- `openspec validate c-12-cancelar-turno --strict`: el change es válido.
- Prueba de mutación: con la llamada a `validar_cancelacion` reemplazada en el endpoint por un cambio de estado directo, fallan 3 tests (instante exacto, turno pasado y doble cancelación). El código se restauró y la suite volvió a verde.

## Observaciones del apply

- **Ajustar en el design (D2) y la tarea 2.1:** la versión original ponía la llamada a `validar_cancelacion` dentro del repositorio, lo que rompía la regla dura 1 (`db → domain` solo tipos). Se ajustó al patrón de C-11: el router abre la transacción, llama al dominio y el repositorio solo escribe. Commit `4184ab5`.
- **Firma de `cancelar_turno`:** recibe el turno original y el que devuelve el dominio (`antes`, `despues`), así el repositorio no repite la regla de cambio de estado.
- **Tokens en los tests:** el token vence a los 60 minutos del reloj fijo, por eso los tests lo vuelven a emitir después de adelantar el reloj. No cambió código de producción.
