# Reflexión — Hernán Gonzalez

## 1. Información incorrecta del Discovery y cómo la detecté

Mi verificación fue la de Doctoralia en la App Store, que dio "Sí (con precisión)". Lo que más me chocó al abrir la ficha fue que no hubiera una ficha de Argentina y que las reseñas visibles fueran tan viejas (2019, 2023). Yo que estoy todos los días en atención al público en el laburo sé muy bien que las reseñas de hace 4 o 5 años no te sirven de nada para saber cómo está funcionando realmente un lugar hoy.

La corrección que propuse (A.1, el proveedor) la detecté yo comparando los textos: estaba leyendo la letra chica de la documentación oficial y vi que figuraba la razón social completa, "Docplanner Health (proveedor: Docplanner Italy S.R.L.)", así que lo corregí porque solemos quedarnos solo con el nombre comercial. El resto coincidía (planes Premium/First Class y las 3 mil valoraciones), así que no hubo más cambios. También dejé registrado que era la tienda de España y que la app es de agenda sin gestión clínica ni mención de odontología.

## 2. Uso de Ajustar y de Parar acá

En mi etapa el Ajustar fue la revisión de Belén a mi propose de C-10. El faltante que más me dolió, pero que a la vez fue el más justo, fue el de los escenarios de bloqueo y horarios: justo yo que laburo cerrando caja y manejando la recepción sé que si no controlás bien los horarios se te arma un quilombo bárbaro, y fue un detalle groso que se me pasó por distracción al documentar. Los otros dos (la base técnica y la inconsistencia de la prestación) también eran correctos.

Si le dábamos "Continuar" a mi versión original, el pobre Joaquín se iba a volver loco: cuando quisiera meter el código iba a estar a ciegas, y podía terminar armando algo donde se superponen los turnos o se dan reservas en horarios donde no hay nadie atendiendo. Iba a tener que frenar todo para preguntarnos qué hacer o mandar algún parche temporal para safar. También tuve que corregir mi propio design (el `ahora` sin uso y lo de Java), que de llegar al apply le dejaba una firma incorrecta al implementador.

## 3. Especificación aprobada vs. prompt suelto

La diferencia la viví en C-10. Con la especificación aprobada (cinco escenarios finales), Joaquín implementó exactamente lo acordado. El caso del error `DatoInvalido` lo demuestra perfecto: había quedado colgado en mi design y él no lo implementó porque no estaba en la spec, y me parece perfecto lo que hizo Joaco. La posta es que la spec manda: si no lo bajé a la especificación, él no tiene por qué adivinarlo ni darlo por sentado. Me sirve de lección de que lo que no está escrito en la spec no existe para el que programa. Con un prompt suelto del tipo "validá el alta de un turno", en cambio, el agente habría tenido que inventar qué validar y qué errores devolver, y la verificación objetiva con 32 tests no habría sido posible.

## 4. Qué parte de la fundación aportó más y cuál menos

Lo que más miré fueron las reglas de negocio (las RN de la KB): necesitaba entender bien la lógica de la clínica antes de ponerme a armar la estructura y los datos, y redactar la spec fue casi traducir esos ejemplos a escenarios. Las reglas de `AGENTS.md` también me sirvieron (dominio puro, datos ficticios). A lo que menos bola le di fue al roadmap, porque mi cabeza estaba a mil intentando que ande bien la asignación de los turnos para esta entrega y no me fijé tanto en qué iba a pasar a largo plazo.

## 5. Qué hice yo dentro del grupo

Mi participación se concentró en las etapas 2 y 6, más la 7. En la Etapa 2 verifiqué manualmente la fuente de Doctoralia en la App Store. En la Etapa 6 hice el explore de C-10, redacté el propose completo, acepté los ajustes de Belén, corregí el design y guardé el resumen del explore en el repo. En la Etapa 7 guardé el explore en Engram y preparé mi evidencia y mi bitácora. Belén verificó Dentalink, ajustó la KB y revisó mi propose; Elías verificó Turnito, consolidó las verificaciones y se encargó de skills y reglas; Bruno hizo el Discovery y la entrega final; Joaquín habría hecho el apply, verify, archive y README, aunque esto queda **pendiente de confirmar con él**.

## 6. Uso de IA

Durante el proyecto utilicé OpenCode con el modelo Muse Spark para ejecutar el ciclo OPSX del propose, ordenar los datos de mi verificación y generar borradores de la bitácora y de esta reflexión. La IA me sirvió para estructurar documentos y no olvidar verificaciones, pero las decisiones fueron mías: verifiqué la fuente en el navegador, elegí el change, acepté los ajustes y pedí las correcciones del design. Revisé cada borrador y lo puse en mis palabras antes de subirlo. Esta reflexión la escribí yo a partir de mis respuestas a las preguntas del agente.
