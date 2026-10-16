# Reflexión — Elías Tello

## 1. Información incorrecta del Discovery y cómo la detecté

En mi caso, encontré un error en la información de Turnito. El informe citaba la página principal, donde no aparecían los precios, aunque estos sí estaban publicados en la sección de planes. Además, decía que los precios incluían IVA, cuando la página mostraba el precio sin IVA y el total con el impuesto incluido. Por eso, la información era correcta en cuanto a los montos, pero necesitaba corregir la fuente y la aclaración sobre el IVA.

También consolidé la verificación de AgendaPro que había hecho Bruno. El informe decía que no publicaba precios, pero el agente había probado una URL que no existía en lugar de seguir el enlace de precios del menú. Los precios sí estaban publicados en pesos. Además, la información sobre el odontograma aparecía en una pregunta frecuente desplegable. Esto hizo que la conclusión de que solo Turnito publicaba precios en pesos fuera incorrecta.

Lo detectamos abriendo manualmente las páginas originales y comprobando la información directamente, sin crear cuentas. Al ver que el agente podía presentar información incorrecta con tanta seguridad, me quedó claro que una respuesta convincente no necesariamente es una respuesta verificada. Aprendí que hay que comprobar las fuentes antes de dar por válida una conclusión, especialmente cuando después se utiliza para justificar puntajes o tomar decisiones.

## 2. Uso de Ajustar y de Parar acá

El caso más claro de Ajustar fue la regla 14 de `AGENTS.md`. La regla prohibía modificar la carpeta `openspec/`, pero esa carpeta es necesaria para trabajar con los flujos de OPSX, como `propose` y `archive`. Si hubiéramos continuado sin corregirla, el agente podría haberse encontrado con una contradicción al intentar ejecutar esas tareas o haber evitado modificar archivos que necesitaba utilizar.

También corregimos otras cosas del archivo: una regla que decía que nunca se debían hacer commits, aunque eso correspondía a una instrucción puntual de una sesión y no a una regla permanente del proyecto; una nota que indicaba incorrectamente que el registro no estaba versionado; y un flujo al que le faltaban las etapas de exploración y verificación. Revisé las instrucciones con Claude Code y después se hicieron las correcciones con OpenCode.

Creo que es mejor corregir estos problemas temprano porque una regla incorrecta puede afectar varias tareas y hacer que tengamos que revisar o rehacer parte del trabajo. Si hubiéramos llegado al apply con la regla 14 sin corregir, probablemente habría sido más costoso detectar el problema, entender por qué ocurría y volver atrás para ajustar las instrucciones.

También hubo un caso de Parar acá. Ejecuté por error `/active-orchestrator:init` en OpenCode, que iniciaba el flujo completo en lugar de limitarse a la etapa 5. Esto sobrescribió `.active-orchestrator-state.json`: el archivo pasó de 146 a 8 líneas, se perdió la información del Discovery y quedó marcado como omitido (`"discovery": {"skipped": true}`). Detuvimos el proceso y recuperamos el archivo con `git checkout`. La KB y `CHANGES.md` no se modificaron. Esto me mostró la importancia de detenerse cuando una herramienta empieza a hacer algo distinto de lo esperado, en lugar de continuar y arriesgar más información.

## 3. Especificación aprobada vs. prompt suelto

La diferencia principal que noté fue que trabajar con una especificación aprobada permite tener claro qué se debe implementar y cómo comprobar que funciona. En el caso de C-10, la especificación definía cinco escenarios para la función `validar_alta`: un alta exitosa, un solapamiento del profesional, turnos contiguos, un turno fuera de horario y un turno dentro de un bloqueo.

Después, en la etapa de verificación, `verify.md` comprobó que los 32 tests pasaran y que se respetaran dos reglas importantes de `AGENTS.md`: que el dominio no importara FastAPI y que no se llamara a `now()`. También se hizo una prueba de mutación para comprobar que los tests detectaran errores en la lógica de los intervalos.

Otro detalle importante fue que Joaquín no implementó un error llamado `DatoInvalido` que aparecía en el design, porque no estaba contemplado en la especificación. Esto me pareció una buena decisión, ya que demuestra que tener una especificación definida ayuda a evitar agregar cosas que no fueron acordadas.

También hubo que ajustar el propose de C-10 porque faltaba la base técnica de C-02 y había referencias a Java y JUnit que venían de otro proyecto. Para mí, esto demuestra que la IA puede ayudar a generar una propuesta, pero sigue siendo necesario revisarla y corregirla antes de avanzar. Un prompt suelto puede servir para obtener una primera solución, pero una especificación aprobada permite trabajar con criterios claros y verificar el resultado de manera más objetiva.

## 4. Qué parte de la fundación aportó más y cuál menos

Para mí, lo que más valor aportó fueron las reglas de `AGENTS.md`, junto con la KB. La KB definía el stack, las reglas de negocio y los códigos HTTP, mientras que las 14 reglas de `AGENTS.md` establecían límites concretos para la implementación. Además, `verify.md` permitía comprobar algunas de esas reglas automáticamente.

El roadmap también fue útil porque organizaba los 17 changes en seis fases y mostraba sus dependencias. En particular, permitió identificar que C-10 dependía de C-02. Sin embargo, en este trabajo su utilidad fue más de planificación que de implementación directa, porque solamente se desarrolló C-10.

Las skills también fueron útiles como herramientas de apoyo. Se eligieron cinco de las dieciséis recomendadas por `find-skill`, se justificó la selección y se incluyeron en el repositorio. Después fue necesario corregir el registro, porque la primera versión tenía reglas genéricas y rutas absolutas de mi computadora.

Si tengo que elegir la parte que menos aportó directamente a este ciclo, diría que fue el roadmap, no porque estuviera mal hecho, sino porque su utilidad principal era organizar el desarrollo futuro y solamente implementamos un change. En cambio, las reglas y la KB tuvieron una relación más directa con las decisiones y verificaciones de C-10. Sobre si las skills se utilizaron durante el apply, no tengo evidencia suficiente para afirmarlo; tendría que confirmarlo con Joaquín.

## 5. Qué hice yo dentro del grupo

Mi participación se repartió entre las etapas 0, 2 y 5.

- **Etapa 0:** tomé las siete capturas de evidencia y las organicé en `docs/evidencia/etapa-0-elias/`.
- **Etapa 2:** verifiqué manualmente la información de Turnito, consolidé las cinco verificaciones del grupo, apliqué las correcciones al informe y preparé el PDF final. También incorporé los hallazgos sobre los errores del agente y revisé el puntaje de AgendaPro, que quedó en 4 en lugar de 5 por prudencia.
- **Etapa 5:** seleccioné cinco skills de las dieciséis recomendadas, corregí el registro, revisé y ajusté las instrucciones de `AGENTS.md` y `CLAUDE.md`, e incluí las skills en el repositorio a pedido del profesor, mediante el PR #7.

Además, fui registrando el trabajo en `docs/bitacora/bitacora-elias.md` y participé en varios commits y pull requests del proyecto. Mi tarea no fue solamente producir documentación, sino también revisar lo generado por los agentes y decidir qué información o instrucciones necesitaban correcciones.

## 6. Uso de IA

Durante el proyecto utilicé Claude Code y OpenCode para revisar el repositorio, ejecutar herramientas y skills, generar borradores y corregir las instrucciones del agente. También utilicé ChatGPT para ayudarme a redactar y reformular esta reflexión con un tono más natural. La IA me sirvió para acelerar tareas y organizar información, pero las decisiones finales fueron mías: elegí las cinco skills, revisé y aprobé las reglas, decidí el puntaje 4 para AgendaPro y determiné qué correcciones hacer. Aprendí que trabajar con un agente no significa delegar toda la responsabilidad, sino usarlo como una herramienta que necesita supervisión, verificación y criterio humano.
