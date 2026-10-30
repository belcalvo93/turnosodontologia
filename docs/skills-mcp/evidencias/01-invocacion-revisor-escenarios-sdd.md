# Revisión del change C-16 con `revisor-escenarios-sdd` — evidencia de invocación

- **Fecha:** 2026-10-29
- **Skill usada:** `revisor-escenarios-sdd` (del proyecto)
- **Ruta desde la que se cargó:** `C:\Users\beluu\Documents\1 Tec en Programacion\2DO\Metodologia de sistemas I\8 SDD y Active Stack\turnosodontologia\.agents\skills\revisor-escenarios-sdd`

## Solicitud textual

> Terminé el propose del change C-16 (openspec/changes/c-16-bloqueos-turnos-afectados/). Revisalo antes del apply siguiendo las instrucciones del proyecto. No modifiques ningún archivo. Al final decime qué skill del proyecto usaste y desde qué ruta la cargaste.

---

La revisión está completa. No modifiqué ningún archivo.

# Revisión de `c-16-bloqueos-turnos-afectados` (pre-apply)

**Verificación previa:** todos los elementos de código citados en el propose existen y se comportan como se declara: `solapan()` semiabierto (`app/domain/intervalos.py:15`), `_bloqueo_afecta` con comentario RN-TUR-05 (`app/domain/reglas_turno.py:110`), `COLUMNAS_TURNO` y `turno_desde_fila` (`app/db/repositorio_turnos.py:16,48`), patrón SQL `inicio < ? AND fin > ?` de `listar_bloqueos_de_recursos` (`app/db/repositorio_bloqueos.py:85`), `TurnoResponse`/`turno_a_response` (`app/api/turnos.py:47,58`), `transaccion(conexion)` en `POST /bloqueos` (`app/api/bloqueos.py:81`) y la aserción de igualdad exacta en `tests/api/test_bloqueos.py:46`. Los changes de los que depende están archivados en `openspec/changes/archive/` (C-02 a C-11 inclusive); lo tratado en el proposal es correcto.

## 1. Tabla de trazabilidad

| Escenario | Spec | RN-xx / fuente | Cómo se verifica (tasks.md) |
|---|---|---|---|
| Alta válida de bloqueo (profesional) | specs/bloqueos/spec.md:15 | — (heredado de C-09, RN-REC-02) | Asersión editada en 4.1 (`tests/api/test_bloqueos.py:46`) |
| Rechazo por intervalo inválido (422) | specs/bloqueos/spec.md:21 | RN-REC-02 (KB 05, línea 22) | Tests de C-09 ya en `main`; sin tarea nueva (comportamiento intacto) |
| Rechazo por recurso inexistente (422) | specs/bloqueos/spec.md:27 | — (heredado; contrato errores-api: 422 `dato_invalido` porque va en el cuerpo) | Ídem |
| Reporta turnos reservados solapados (profesional) | specs/bloqueos/spec.md:33 | RN-TUR-05 + RN-TUR-04 (KB 05, líneas 43 y 40) | Tasks 1.1 (dominio puro) y 3.1 (API), `tests/domain/` + `tests/api/test_bloqueos.py` |
| Bloqueo de sillón reporta solo ese sillón | specs/bloqueos/spec.md:39 | RN-TUR-05 (KB 05, línea 43) | Task 3.2 |
| Turnos contiguos no se reportan (dos bordes) | specs/bloqueos/spec.md:45 | RN-TUR-04 (KB 05, línea 40; SE-10) | Tasks 1.2 y 2.2 (dominio + SQL) |
| Turnos cancelados no se reportan | specs/bloqueos/spec.md:51 | RN-TUR-08 (KB 05, línea 52 — ver hallazgo 2) | Tasks 1.2 y 3.1 |
| `turnos_afectados = []` sin superposición | specs/bloqueos/spec.md:57 | RN-TUR-04/08 (borde de lista vacía) | Task 3.1 |
| Ordenado por `inicio ASC` y no modificado | specs/bloqueos/spec.md:63 | D-A3/D-A4 (design) — ver hallazgo 1 | Tasks 1.3 y 3.1 (GET + auditoría) |
| `GET /bloqueos` sin `turnos_afectados` | specs/bloqueos/spec.md:69 | D-A2 (design) | Task 3.2 |

Cruce RN→tarea: RN-TUR-04, RN-TUR-05 y RN-TUR-08 tienen test en dominio (1.1–1.3) y en API (3.1/3.2), y la verificación final 5.2 lo corta: se cumple la regla dura 11. Los escenarios tienen las tres viñetas y son observables; el delta reproduce verbatim los 3 escenarios heredados de C-09 (correcto para un MODIFIED).

## 2. Hallazgos

Ninguno **crítico** ni **alto**. En orden de severidad:

1. **Medio — ambigüedad (desempate por `id` nunca se ejercita).** `specs/bloqueos/spec.md:63-67` y `tasks.md:9` (1.3) prometen validar `inicio ASC, empates por id ASC`, pero los tres turnos del escenario (10:00, 10:30 y 11:00) tienen inicios distintos: no hay empate real, el `id ASC` queda sin prueba. Para que el escenario haga lo que dice, alcanza con dos turnos `reservado` del mismo profesional con **el mismo `inicio`** pero distinto `id` (y el de mayor `id` último).
2. **Medio — cita estirada (RN-TUR-08).** `specs/bloqueos/spec.md:51` y `proposal.md:29` usan RN-TUR-08 para "los cancelados no se reportan". La letra de la regla (KB 05, línea 52) habla de validar solapamientos al reprogramar, no del reporte de un bloqueo; es el mismo espíritu ("los cancelados nunca generan conflicto") pero no es literal. No bloquea el apply; como guarda, sumar la cita de RN-TUR-14 (estado `reservado`, KB 05 línea 70) al mismo escenario, o aclarar en el design D-A4 que es extensión documentada.
3. **Bajo — `codigo` no explicitado en escenarios heredados.** En `specs/bloqueos/spec.md:25` y `:31` el "Entonces" dice "422 con un mensaje de error en español" sin afirmar `codigo = dato_invalido`, que es lo que exige el contrato `openspec/specs/errores-api/spec.md:81`. Es texto verbatim de C-09 y no es contradictorio, así que es opcional anclarlo ya que el requirement se está reescribiendo igual.
4. **Bajo — cita errónea menor (RN-TUR-09).** `proposal.md:9` dice "sin reloj (`datetime.now()` prohibido, RN-TUR-09)". RN-TUR-09 (KB 05, línea 55) es la regla de turnos futuros; la prohibición del reloj en el dominio es la **regla dura 2** de AGENTS.md (y RN-TUR-09 la ejemplifica con reloj inyectado). `tasks.md` lo cita bien (1.4), el impreciso es el proposal.
5. **Bajo — orden de ejecución en el roadmap.** `CHANGES.md:88` y `:119` ubican C-16 después de C-13 para el Agente B, aunque la dependencia formal del change es solo C-11 (`CHANGES.md:425`), que está archivada. No es contradicción de dependencias (es scheduling de agente), pero si C-13 se está implementando en paralelo en el repo, conviene rebasear antes del apply.

**Detalle que queda registrado a propósito (no es hallazgo):** el design D-A1 formaliza la decisión de SE-09 del 2026-10-29 sin tocar `knowledge-base/` (respetando la regla dura 14), y el propio design lo lista como pregunta abierta de sincronización pendiente. Eso está bien resuelto; solo recordá que `10_preguntas_abiertas.md` seguirá mostrando SE-09 como abierta hasta que se decida actualizar la KB aparte.

**Veredicto:** el change está en very good shape para `/opsx:apply`. Los únicos ajustes que valen la pena antes de arrancar son el 1 (empate por `id`) y opcionalmente el 2, ambos editables en el change sin re-proponer.
