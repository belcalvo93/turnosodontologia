# Trazabilidad de Reglas de Negocio a Tests

Mapa canónico entre las 31 reglas de negocio de [`knowledge-base/05_reglas_de_negocio.md`](../knowledge-base/05_reglas_de_negocio.md) y los tests automatizados de la suite (`pytest`).

Este documento se verifica automáticamente en cada ejecución de la suite mediante `tests/test_trazabilidad.py` y `tests/trazabilidad.py`: si falta una regla de la KB, si un nodo citado no existe en disco, si `RN-TUR-13` no cita el mismo test que `RN-TUR-04`, o si una regla distinta de `RN-GLO-02` figura como `No aplica`, la suite falla.

| RN | Regla | Test | Estado |
|---|---|---|---|
| RN-PRO-01 | Cada profesional tiene horarios de atención por día; fuera de ellos no se asignan turnos | `tests/domain/test_reglas_turno.py::test_franja_turno_que_empieza_antes_de_la_apertura_lanza_fuera_de_horario` | cubierta |
| RN-PRO-02 | El turno debe caber completo dentro de una misma franja horaria del profesional | `tests/domain/test_reglas_turno.py::test_franja_turno_que_cruza_el_corte_entre_manana_y_tarde_lanza_fuera_de_horario` | cubierta |
| RN-REC-01 | Duración de prestación entera mayor que cero; sillones y prestaciones con nombre único | `tests/api/test_prestaciones.py::test_post_prestaciones_con_duracion_cero_responde_422` | cubierta |
| RN-REC-02 | Bloqueo con alcance profesional o sillón, `inicio < fin` y motivo | `tests/api/test_bloqueos.py::test_post_bloqueos_con_inicio_mayor_o_igual_que_fin_responde_422` | cubierta |
| RN-REC-03 | Recursos desactivados no aceptan turnos nuevos y los turnos históricos se conservan | `tests/api/test_turnos.py::test_sillon_desactivado_despues_de_la_reserva_conserva_el_turno_y_rechaza_nuevos_422` | cubierta |
| RN-TUR-01 | La duración del turno la define la prestación (`fin = inicio + duracion_minutos`) | `tests/domain/test_reglas_turno.py::test_fin_se_calcula_con_prestacion_de_45_minutos` | cubierta |
| RN-TUR-02 | Todo turno tiene un sillón asignado (`sillon_id` obligatorio) | `tests/api/test_turnos.py::test_post_turnos_sin_sillon_id_responde_422_con_detalle_del_campo` | cubierta |
| RN-TUR-03 | Sin solapamiento de turnos activos para el mismo profesional ni para el mismo sillón | `tests/domain/test_reglas_turno.py::test_solapamiento_del_profesional_lanza_conflicto_agenda` | cubierta |
| RN-TUR-04 | Intervalos semiabiertos `[inicio, fin)`: los turnos contiguos son válidos | `tests/domain/test_intervalos.py::test_turnos_contiguos_no_solapan` | cubierta |
| RN-TUR-05 | Se rechaza el turno fuera de horario o superpuesto con un bloqueo del profesional o sillón | `tests/domain/test_reglas_turno.py::test_bloqueo_de_sillon_rechaza_turno_en_ese_sillon` | cubierta |
| RN-TUR-06 | Cancelar un turno libera el horario del profesional y del sillón | `tests/api/test_cancelar_turno.py::test_tras_cancelar_se_puede_reservar_el_mismo_hueco_201` | cubierta |
| RN-TUR-07 | Reprogramar es una operación propia que mantiene el id del turno y su historial | `tests/api/test_reprogramar_turno.py::test_reprogramar_recepcion_mueve_el_turno_200_conservando_el_id` | cubierta |
| RN-TUR-08 | Al reprogramar se excluye el propio turno y los cancelados no generan conflicto | `tests/domain/test_reglas_turno.py::test_excluir_turno_id_ignora_el_propio_turno` | cubierta |
| RN-TUR-09 | Solo se pueden cancelar o reprogramar turnos futuros respecto del reloj inyectado | `tests/api/test_cancelar_turno.py::test_turno_pasado_409_y_sigue_reservado` | cubierta |
| RN-TUR-10 | Un turno ya cancelado no se puede volver a cancelar ni reprogramar | `tests/api/test_cancelar_turno.py::test_segunda_cancelacion_409_sin_nueva_auditoria` | cubierta |
| RN-TUR-11 | No existen sobreturnos: ningún rol puede forzar un solapamiento | `tests/api/test_turnos.py::test_post_turnos_administracion_tampoco_puede_superponer_un_turno` | cubierta |
| RN-TUR-12 | Un mismo paciente no puede tener dos turnos activos superpuestos | `tests/domain/test_reglas_turno.py::test_solapamiento_del_paciente_lanza_conflicto_agenda` | cubierta |
| RN-TUR-13 | Sin margen de limpieza obligatorio entre turnos (implícita en intervalos contiguos) | `tests/domain/test_intervalos.py::test_turnos_contiguos_no_solapan` | cubierta |
| RN-TUR-14 | Los turnos se crean con estado `reservado` | `tests/api/test_turnos.py::test_post_turnos_recepcion_crea_turno_reservado_201` | cubierta |
| RN-PAC-01 | Datos mínimos del paciente y obra social/afiliado opcionales como dato | `tests/api/test_pacientes.py::test_post_pacientes_alta_valida_con_obra_social` | cubierta |
| RN-PAC-02 | El DNI es único por paciente | `tests/api/test_pacientes.py::test_post_pacientes_con_dni_duplicado_responde_409_sin_repetir_el_dni` | cubierta |
| RN-PAC-03 | Solo datos ficticios rotulados en seeds, ejemplos y tests (DNI con `"(ficticio)"`) | `tests/api/test_seed_demo.py::test_datos_ficticios_rotulados_en_pacientes_y_profesionales` | cubierta |
| RN-ACC-01 | Toda operación salvo login y health exige usuario autenticado | `tests/api/test_turnos.py::test_post_turnos_sin_token_responde_401_no_autenticado` | cubierta |
| RN-ACC-02 | Permisos por rol según la matriz de actores (`403` cuando el rol no tiene permiso) | `tests/api/test_prestaciones.py::test_recepcion_post_prestaciones_recibe_403` | cubierta |
| RN-ACC-03 | Un odontólogo solo puede consultar su propia agenda y sus propios turnos | `tests/api/test_agenda.py::test_agenda_profesional_odontologo_ajeno_403` | cubierta |
| RN-ACC-04 | Las contraseñas se guardan solo como hash Argon2id y los secretos no se versionan | `tests/api/test_auth.py::test_la_contrasena_no_queda_en_la_base_ni_en_la_respuesta_del_login` | cubierta |
| RN-AUD-01 | Crear, reprogramar y cancelar registran quién, qué (antes/después) y cuándo en auditoría | `tests/api/test_auditoria.py::test_historial_de_tres_acciones_devuelve_tres_registros_en_orden` | cubierta |
| RN-AUD-02 | La auditoría es append-only: sin operaciones ni rutas para editar o borrar | `tests/api/test_auditoria.py::test_patch_y_delete_sobre_auditoria_405_sin_cambios` | cubierta |
| RN-AUD-03 | Una operación rechazada no modifica el turno ni agrega registros de auditoría | `tests/api/test_turnos.py::test_post_turnos_tras_un_409_no_cambia_la_cantidad_de_turnos_ni_auditorias` | cubierta |
| RN-GLO-01 | Formato único de error JSON en español con código HTTP consistente | `tests/api/test_errores.py::test_error_de_dominio_responde_su_status_con_codigo_y_mensaje` | cubierta |
| RN-GLO-02 | Funciones fuera del alcance del MVP no tienen reglas en esta versión | — | No aplica: declara una ausencia de funcionalidad del MVP |
