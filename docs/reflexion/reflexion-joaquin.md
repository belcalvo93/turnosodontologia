## 1. ¿Qué información del Discovery resultó incorrecta, no verificable o inventada por el agente? ¿Cómo la detectaron?

En mi fuente (AgendaPro) el informe decía que no había tutoriales de agenda, pero al abrir los manuales y los videos vi que uno explica cómo configurar el período de reservas, así que la marqué como parcial y anoté que los videos son de 2015 y la empresa es chilena.

## 2. ¿En qué etapa usaron Ajustar, qué estaba mal y qué habría pasado si hubieran apretado Continuar?

En el apply no dejé agregar `DatoInvalido` porque no estaba en el spec, corregí el caso `excluir_turno_id=None` con un test que primero falló (si seguía, un turno sin id se salteaba y se aceptaba un turno superpuesto) y arreglé el "[x] pendiente" de `CHANGES.md`.

## 3. ¿Qué diferencia notaron entre implementar con una especificación aprobada y pedir código con un prompt suelto?

Con el spec aprobado cada test salió de un escenario concreto y el agente no tuvo que adivinar, mientras que con un prompt suelto habría inventado reglas, como el `DatoInvalido` que nadie pidió.

## 4. ¿Qué parte de la fundación (knowledge-base, roadmap, reglas) le aportó más valor al ciclo OPSX y cuál menos?

Lo que más me sirvió fueron las reglas de `AGENTS.md` y la knowledge-base, que usé para decidir lo de `DatoInvalido` con RN-REC-01, y lo que menos fue el roadmap, porque yo implementé un solo change.

## 5. En grupo: ¿qué hizo cada integrante y en qué etapa?

Bruno hizo el Discovery y la entrega final, Belén las etapas 3 y 4, Elías la etapa 5, Hernán el explore y propose de C-10 y Engram, y yo la etapa 0, la verificación de la fuente 5, el apply, verify y archive de C-10 y el README.

## Declaración de uso de IA

Usé Claude como guía paso a paso para la instalación, git y el apply, y también para redactar esta reflexión a partir de lo que hice; las decisiones fueron mías y revisé cada respuesta antes de dejarla.