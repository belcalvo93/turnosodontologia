# Spec Delta

## ADDED Requirements

### Requirement: Trazabilidad de reglas de negocio a tests

El repositorio SHALL mantener `docs/trazabilidad-rn-test.md` con una fila por cada regla `RN-xx-NN` de `knowledge-base/05_reglas_de_negocio.md`, indicando el test que la cubre, y la suite SHALL verificar automáticamente que no falte ninguna regla ni ninguno de los tests citados. Una regla sin fila o un test citado inexistente SHALL hacer fallar la suite.

#### Scenario: Todas las reglas están mapeadas

- **Dado** el repositorio con `docs/trazabilidad-rn-test.md` y `knowledge-base/05_reglas_de_negocio.md`
- **Cuando** se corre la suite
- **Entonces** la verificación de trazabilidad pasa e informa que las 31 reglas están mapeadas
- **Y** cada test citado existe en la suite

#### Scenario: Una regla sin fila hace fallar la verificación

- **Dado** un documento de reglas que declara una regla `RN-xx-NN` ausente de la tabla de trazabilidad
- **Cuando** se ejecuta la verificación
- **Entonces** falla y el mensaje nombra el código de la regla que falta

#### Scenario: Un test citado inexistente hace fallar la verificación

- **Dado** una tabla de trazabilidad que cita un test que no existe en la suite
- **Cuando** se ejecuta la verificación
- **Entonces** falla y el mensaje nombra el test citado que no se encontró
