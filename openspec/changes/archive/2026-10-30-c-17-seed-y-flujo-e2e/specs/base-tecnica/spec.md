# Spec Delta

## ADDED Requirements

### Requirement: Trazabilidad de reglas de negocio a tests

El repositorio SHALL mantener `docs/trazabilidad-rn-test.md` con una fila por regla `RN-xx-NN` de `knowledge-base/05_reglas_de_negocio.md`, citando el test que la cubre. La suite SHALL fallar si falta una regla o un test citado, si `RN-TUR-13` no cita el mismo test que `RN-TUR-04`, o si una regla que no es `RN-GLO-02` figura como `No aplica`. `RN-GLO-02` SHALL figurar como `No aplica` con su motivo: declara una ausencia, no un comportamiento.

#### Scenario: Todas las reglas están mapeadas

- **Dado** el repositorio con `docs/trazabilidad-rn-test.md` y `knowledge-base/05_reglas_de_negocio.md`
- **Cuando** se corre la suite
- **Entonces** la verificación de trazabilidad pasa e informa que las 31 reglas están mapeadas
- **Y** cada test citado existe en la suite
- **Y** `RN-TUR-13` cita el mismo test que `RN-TUR-04`
- **Y** `RN-GLO-02` figura como `No aplica` con su motivo

#### Scenario: Una regla sin fila hace fallar la verificación

- **Dado** un documento de reglas que declara una regla `RN-xx-NN` ausente de la tabla de trazabilidad
- **Cuando** se ejecuta la verificación
- **Entonces** falla y el mensaje nombra el código de la regla que falta

#### Scenario: Un test citado inexistente hace fallar la verificación

- **Dado** una tabla de trazabilidad que cita un test que no existe en la suite
- **Cuando** se ejecuta la verificación
- **Entonces** falla y el mensaje nombra el test citado que no se encontró

#### Scenario: No aplica solo vale para RN-GLO-02 y con motivo

- **Dado** una tabla de trazabilidad donde `RN-PAC-01` figura como `No aplica` con motivo, y otra donde `RN-GLO-02` figura como `No aplica` sin motivo
- **Cuando** se ejecuta la verificación sobre cada una
- **Entonces** la primera falla y el mensaje nombra `RN-PAC-01`
- **Y** la segunda falla y el mensaje nombra `RN-GLO-02`

#### Scenario: Una regla sin test verificable no rompe la tabla

- **Dado** una tabla donde `RN-GLO-02` figura como `No aplica` con el motivo "declara una ausencia de funcionalidad del MVP"
- **Cuando** se ejecuta la verificación
- **Entonces** no reporta hallazgos para `RN-GLO-02` y no exige un test citado para esa fila
