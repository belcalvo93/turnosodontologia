---
name: revisor-escenarios-sdd
description: Revisa los specs y tasks.md de un change de OpenSpec (openspec/changes/<nombre>/) antes del /opsx:apply, verificando escenarios contra la knowledge-base y el contrato de errores-api. Usala SIEMPRE al terminar un /opsx:propose, o cuando se pide revisar los escenarios de un spec, validar un change o hacer una revisión pre-apply: detecta ambigüedades, casos de borde faltantes, citas a reglas RN-xx inexistentes o mal usadas, y escenarios sin verificación. Solo informa; no modifica archivos.
---

# Revisor de escenarios SDD

Revisora de specs de OpenSpec para este proyecto (turnos odontológicos, Python + FastAPI + pytest + SQLite).
La skill es de **solo lectura**: produce evidencia, una tabla de trazabilidad y una lista de hallazgos.
Nunca edita specs, tasks.md, ni ningún otro archivo; las correcciones corresponden a un nuevo
/opsx:propose o a ediciones del change que pida el usuario.

## Cuándo activarse

- Terminó de ejecutarse `/opsx:propose C-NN-nombre` (revisión previa obligatoria a `/opsx:apply`).
- El usuario pide revisar escenarios, validar un spec, "chequear el change" o pulir un `tasks.md`.

## Entrada

- Ruta del change: `openspec/changes/<nombre>/` con `proposal.md`, `design.md` (si existe),
  `specs/*/spec.md` y `tasks.md`. Los changes ya archivados están en `openspec/changes/archive/`.
- Fuentes de contraste (siempre abrirlas en este orden, citar lo que se usa):
  1. `knowledge-base/05_reglas_de_negocio.md` — fuente única de las reglas RN-xx.
  2. `openspec/specs/errores-api/spec.md` — contrato único de errores (status + `codigo`).
  3. Specs ya aplicados en `openspec/specs/` — comportamientos vigentes con los que cruza el change.
  4. `CHANGES.md` — alcance y dependencias del change.

## Formato real de los specs

Cada spec tiene `### Requirement:` y debajo escenarios con este formato exacto:

```markdown
#### Scenario: DNI duplicado

- **Dado** un paciente existente con un DNI determinado y un usuario con rol `recepcion`
- **Cuando** envía `POST /pacientes` con ese mismo DNI
- **Entonces** el sistema responde `409` con `codigo` `dni_duplicado` y no persiste un segundo paciente
```

Los escenarios se cuentan contando líneas `#### Scenario:`; un documento puede declarar "N
escenarios" en su encabezado, y ese número no es de confianza.

## Procedimiento

1. **Contar escenarios reales.** Para cada `specs/*/spec.md` del change: contá las líneas
   `#### Scenario:` de cada `### Requirement:`. Si el número declarado en algún resumen difiere del
   contado, es un hallazgo de tipo conteo con archivo y línea.
2. **Verificar el formato.** Cada `#### Scenario:` debe tener las tres viñetas `- **Dado**`,
   `- **Cuando**`, `- **Entonces**`. El "Cuando" describe una acción concreta y el "Entonces" un
   resultado observable (un status, un cuerpo, un efecto persistente). Un "Entonces" subjetivo
   ("debería funcionar mejor") es hallazgo de ambigüedad.
3. **Cruzar cada escenario con su RN-xx.** Abrí `knowledge-base/05_reglas_de_negocio.md` y para
   cada escenario que cite una RN-xx, verificá: (a) que el número exista (prefijos: RN-TUR, RN-PAC,
   RN-AUD, RN-ACC, RN-GLO, RN-PRO, entre otros), (b) que la regla diga lo que el escenario afirma.
   Si el escenario no cita ninguna RN pero su comportamiento corresponde a una existente, es hallazgo
   de cita faltante.
4. **Reglas sin escenario.** Relevá en `proposal.md` y `design.md` toda regla de dominio (RN-xx
   citada, restricción, cálculo, error nuevo): cada una debe tener al menos un escenario que la
   pruebe, y si es una regla nueva respecto de la KB, estar justificada en el design. Regla nueva
   sin justificación, o regla mencionada sin ningún escenario que la verifique, es hallazgo de falta
   (archivo y sección).
5. **Casos de borde.** Para cada requirement del change, buscá los bordes típicos del dominio.
   No impongas códigos HTTP de memoria: cotejá la respuesta esperada con
   `openspec/specs/errores-api/spec.md` y con los specs ya aplicados. La convención vigente es:
   404 con `no_encontrado` si el identificador inexistente va en la ruta (`/pacientes/{id}`);
   422 con `dato_invalido` si el dato problemático viene en el cuerpo (p. ej. profesional inexistente
   en el payload); 409 con el `codigo` del tipo de error (`conflicto_agenda`, `fuera_de_horario`,
   `dentro_de_bloqueo`, `turno_no_modificable`, `dni_duplicado`, ...) para errores de dominio o
   unicidad; 401 `no_autenticado` sin token y 403 `sin_permiso` con token válido. Bordes a revisar:
   - **Intervalos semiabiertos** `[inicio, fin)`: turnos contiguos válidos y solapamiento real
     detectado. Revisá las dos direcciones: fin de uno = inicio del otro, y viceversa.
   - **Recurso inexistente**: id inexistente (404 si va en la ruta), profesional o sillón inexistente
     o inactivo (422 si va en el cuerpo).
   - **Rol y autenticación**: rol sin permiso (403) y acceso sin token (401).
   - **Listas vacías**: agenda sin turnos, listado sin resultados.
   - **Estados del turno**: cancelado dos veces, reprogramar un turno pasado, en curso o cancelado.
   - **Datos de pacientes**: todo ejemplo de entrada o salida usa datos ficticios rotulados con DNI
     con sufijo "(ficticio)" (RN-PAC-03); un valor real es hallazgo crítico.
   Si el change toca de lleno uno de estos bordes y ningún escenario lo cubre, proponelo como
   hallazgo de falta; si los códigos que espera el escenario contradicen el contrato de
   `errores-api` o el spec ya aplicado, es hallazgo de ambigüedad o contradicción con la fuente citada.
6. **Cruzar tasks.md con los escenarios.** En `tasks.md`:
   - Cada RN-xx del change mapea a al menos una tarea de test (regla dura 11 de AGENTS.md), y cada
     escenario tiene una tarea que lo verifica. Los tests de dominio van en `tests/domain/` y corren
     sin base de datos ni HTTP; los de API en `tests/api/` con `TestClient`.
   - El número de tareas declarado en el encabezado coincide con la cantidad real de ítems (hallazgo
     de conteo si difiere).
   - Está la tarea de verificación final (ejecutar la suite con pytest y validar todas las reglas duras
     de AGENTS.md). Sin esa tarea, el change no puede cerrarse limpio: es hallazgo de falta.

## Resultado

Dos secciones en español rioplatense neutro:

1. **Tabla de trazabilidad** (una fila por escenario):

   Ejemplo ilustrativo: las rutas, líneas y archivos de la tabla son de muestra; en una revisión real
   se reemplazan por los reales del change revisado.

   ```markdown
   | Escenario | Spec | RN-xx (fuente) | Cómo se verifica (tasks.md) |
   |-----------|------|----------------|------------------------------|
   | Reprogramar a horario solapado lanza ConflictoAgenda | openspec/changes/c-13-reprogramar-turno/specs/reprogramar-turno/spec.md:23 | RN-TUR-07 (KB 05, línea <n>) | Test en tasks.md 1.1, `tests/domain/test_reglas_turno.py` |
   | Reprogramar turno inexistente → 404 | openspec/changes/c-13-reprogramar-turno/specs/reprogramar-turno/spec.md:41 | — (contrato errores-api, 404 `no_encontrado`) | Test en tasks.md 3.1, `tests/api/test_reprogramar_turno.py` |
   ```

2. **Lista de hallazgos**, cada uno con tipo (ambigüedad, falta, sobra, cita errónea, conteo),
   archivo y línea, y descripción breve. Ordenados por severidad: crítico (viola el contrato de
   errores-api o una regla dura de AGENTS.md), alto (borde típico del dominio sin escenario, regla
   sin test), medio (forma, formato Dado/Cuando/Entonces, referencias).

## Criterios de revisión

- Mínimo 3 escenarios por historia de usuario del change: camino esperado, error de negocio y borde
  (límite de intervalo, recurso inexistente, rol sin permiso o lista vacía).
- Ninguna regla de dominio nueva sin justificación en el design; si falta, es hallazgo aunque los
  escenarios sean coherentes entre sí.
- Todo hallazgo cita su fuente: archivo y línea del change, o del spec/KB con el que contrasta. Un
  hallazgo sin cita no se informa.
- La skill solo informa: no crea ni modifica archivos, no resuelve los hallazgos por su cuenta. Si
  algún hallazgo exige tocar `knowledge-base/`, `CHANGES.md` ni otro archivo protegido por la regla
  dura 14, informalo y dejá la decisión al usuario.
- Si la ruta del change no existe, pedí la correcta antes de revisar; no adivines.
