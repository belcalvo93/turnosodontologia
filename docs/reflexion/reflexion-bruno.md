# Reflexión — Bruno Fiouchetta

## 1. ¿Qué información del Discovery resultó incorrecta, no verificable o inventada por el agente? ¿Cómo la detectaron?

En mi fuente, la página dental de AgendaPro, el informe tenía dos afirmaciones falsas. Decía que AgendaPro no publicaba precios, pero sí los publica en `/ar/planes`, en pesos y con IVA incluido. También decía que no mencionaba el odontograma, y lo menciona en una pregunta frecuente que está colapsada. Lo detecté abriendo la página yo mismo, desplegando las preguntas y siguiendo el enlace "Precios" del menú. Ahí vi que el agente había probado una URL que se inventó (`/ar/precios`, que da 404) y que el resumen de la página no leía lo que estaba colapsado. Lo que más me llamó la atención es que las dos afirmaciones sonaban razonables, así que sin abrir la página no me daba cuenta.

Además, en la primera versión del informe el agente usaba "NE" en vez de "No evidenciado" y el conteo de países del resumen estaba mal.

## 2. ¿En qué etapa usaron Ajustar, qué estaba mal y qué habría pasado si hubieran apretado Continuar?

En la etapa 2 lo usé dos veces. La primera fue con el informe inicial, que no cumplía el formato de la consigna: usaba abreviaturas, mezclaba en una sola celda cosas que se piden por separado y tenía mal el conteo de países. Con Continuar habríamos entregado una tabla que no cumple lo pedido. La segunda fue después de mi verificación de AgendaPro: propuse 7 correcciones y Elías las aplicó. Con Continuar habría quedado en el resumen y en el análisis de vacíos la frase "solo Turnito publica precios en pesos", que era falsa. También usé Parar acá después del Discovery, porque la consigna pide verificar 5 fuentes antes de seguir.

## 3. ¿Qué diferencia notaron entre implementar con una especificación aprobada y pedir código con un prompt suelto?

Yo no hice el apply, pero revisé el PR de Joaquín antes de mergearlo. Con el spec aprobado pude revisar rápido: para cada escenario había un test y sabía qué tenía que pasar. Además, cuando apareció algo que no estaba en el spec (el error `DatoInvalido`), no se implementó y quedó anotado. Con un prompt suelto el agente lo habría agregado sin preguntar y yo no habría tenido contra qué compararlo.

## 4. ¿Qué parte de la fundación (knowledge-base, roadmap, reglas) le aportó más valor al ciclo OPSX y cuál menos?

Lo que más valor le aportó al ciclo fueron las reglas de `AGENTS.md`, junto con las reglas de negocio de la knowledge-base. Cuando revisé el PR de Joaquín, pude chequear el código contra reglas concretas: que el dominio no use FastAPI, que no llame a `datetime.now()` y que los intervalos sean `[inicio, fin)`. Además, las reglas del alta de turno que yo definí en el checklist del Discovery llegaron sin cambios a la knowledge-base, al spec y a los tests, así que se podía seguir de dónde salía cada una.

Lo que "menos" aportó fue el roadmap. Tiene 17 changes y nosotros implementamos uno solo. Además, crear-turno dependía de tantos changes que tuvimos que elegir C-10, que es la parte de dominio. Igual sirvió para ver esas dependencias antes de elegir y no meternos en un change imposible de terminar a tiempo.

## 5. En grupo: ¿qué hizo cada integrante y en qué etapa?

Yo hice la etapa 1 (`openspec init` y la bifurcación del Discovery), la etapa 2 (la investigación de 18 sistemas, el checklist de reglas de negocio y la verificación de la página dental de AgendaPro, fuente #1), la convención de Engram, la revisión del PR de Joaquín y la revisión final del repo antes de entregar. Elías verificó la fuente de Turnito, aplicó los ajustes del informe, hizo el PDF y la etapa 5. Belén hizo las etapas 3 y 4 y revisó el propose de C-10. Hernán hizo el explore y el propose de C-10 y Engram. Joaquín hizo el apply, verify y archive de C-10 y el README. Los cinco verificamos una fuente cada uno.

## Declaración de uso de IA

Usé Claude Code para correr el orquestador y las skills del Discovery, buscar y leer fuentes, verificar AgendaPro en el navegador, manejar Git y revisar el repo. También lo usé para armar el borrador de esta reflexión a partir de mi bitácora. Las decisiones de Continuar, Ajustar y Parar acá y las respuestas del checklist fueron mías, y revisé y corregí el texto antes de subirlo.
