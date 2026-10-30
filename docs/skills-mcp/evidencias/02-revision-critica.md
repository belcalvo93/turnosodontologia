# Revisión crítica: errores detectados en los resultados del agente

Fecha: 2026-10-29. Contexto: revisión del propose de C-16 con la skill `revisor-escenarios-sdd` (evidencia 01).

## 1. Falso positivo de la skill: "el desempate por id nunca se ejercita"

- **Antes:** la skill informó (severidad media) que el escenario de orden dice "empatados por `id ASC`" pero sus turnos tienen inicios distintos, y sugirió usar dos turnos con el mismo inicio.
- **Cómo se detectó:** al aplicar la sugerencia, el escenario quedó con dos turnos `reservado` del mismo profesional empezando a las 10:00. La base de conocimiento lo prohíbe: RN-TUR-04 (intervalos semiabiertos, sin solapamiento por profesional o sillón) y RN-TUR-11 (no hay sobreturnos), en `knowledge-base/05_reglas_de_negocio.md`. C-11 lo rechazaría con `conflicto_agenda`. Como `turnos_afectados` lista los turnos de un solo recurso, el empate no puede ocurrir con datos válidos.
- **Después (commit 60db148):** el escenario vuelve a turnos con inicios distintos y sin afirmar empates; el desempate por `id` se prueba solo a nivel dominio con una lista armada a mano (tasks.md 1.3), aclarando que es un orden determinista defensivo.

## 2. Sugerencia inadecuada: citar RN-TUR-14 en lugar de RN-TUR-08

- **Antes:** la skill señaló que la cita de RN-TUR-08 para "los cancelados no se reportan" era estirada y sugirió agregar RN-TUR-14.
- **Cómo se detectó:** se leyó la regla en la KB. RN-TUR-08 (línea 52) dice textualmente que "los turnos cancelados nunca generan conflicto", y RN-TUR-14 (línea 70) solo establece que un turno nuevo se crea `reservado`, sin respaldar la exclusión de cancelados.
- **Después:** la cita de RN-TUR-08 se mantuvo sin cambios.

## 3. Falso positivo: RN-TUR-09 "mal citada" para la prohibición de datetime.now()

- **Antes:** la skill marcó como cita errónea que el proposal use RN-TUR-09 para el reloj, atribuyéndolo a la regla dura 2 de AGENTS.md.
- **Cómo se detectó:** la propia regla dura 2 de AGENTS.md (línea 84) cita RN-TUR-09 para esa prohibición ("NUNCA llamar datetime.now() dentro del dominio ... (RN-TUR-09)").
- **Después:** el proposal quedó como estaba.

## 4. Alerta falsa en la integración: "divergencia" de skill-creator y cambio a skills-lock.json

- **Antes:** el agente informó que la copia de `skill-creator` no coincidía con `anthropics/skills@ca45fc4` (hashes distintos) y agregó una entrada con un campo `commit` fuera del esquema en `skills-lock.json`.
- **Cómo se detectó:** se clonó el repositorio oficial en ese commit y se calculó el hash del `SKILL.md`: coincide con el blob commiteado en nuestro repositorio. La diferencia venía de los saltos de línea (CRLF) de la copia de trabajo en Windows.
- **Después:** se revirtió `skills-lock.json` (archivo manejado por `npx skills`) y el origen de la skill quedó documentado en la ficha de investigación.

## 5. Primer borrador de la skill propia

- **Antes:** el borrador generado con `skill-creator` contaba `#### Escenario:` (el formato real es `#### Scenario:`), imponía el código 404 para cualquier recurso inexistente (el proyecto usa 422 si el id viene en el cuerpo), citaba una ruta de test inventada y tenía frases sin sentido.
- **Cómo se detectó:** se contrastó con un spec real del repositorio y con `openspec/specs/errores-api/spec.md`.
- **Después (commit aa85923):** formato y códigos alineados con los specs, tabla rotulada como ejemplo ilustrativo.

## Limitaciones y mejoras pendientes de la skill

- No verifica que un caso de borde propuesto pueda construirse con datos válidos (falso positivo 1).
- Debería citar la línea de la KB literal antes de marcar una RN como mal usada (2 y 3).
- Mejora pendiente: incorporar ambas verificaciones al procedimiento de `SKILL.md`.
