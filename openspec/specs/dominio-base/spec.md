# dominio-base Specification

## Purpose

Provee los modelos inmutables del dominio de agenda (`Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo`), las operaciones puras sobre intervalos semiabiertos `[inicio, fin)` y reloj inyectado (`solapan` y `es_futuro`), y la jerarquía base de errores de dominio sin dependencias de base de datos ni de HTTP.

## Requirements

### Requirement: Comparación de intervalos semiabiertos

El dominio SHALL comparar intervalos de tiempo mediante `solapan(a, b)` tratando todo intervalo como semiabierto `[inicio, fin)` (`RN-TUR-04`). Dos intervalos SHALL considerarse superpuestos si y solo si `a.inicio < b.fin` y `b.inicio < a.fin`. Los intervalos contiguos donde `a.fin == b.inicio` MUST NOT considerarse superpuestos.

#### Scenario: Turnos contiguos no se superponen

- **Dado** un turno de `10:00` a `10:30` y otro turno de `10:30` a `11:00` en la misma fecha
- **Cuando** se evalúa `solapan(a, b)` y `solapan(b, a)`
- **Entonces** ambas llamadas devuelven `False`

#### Scenario: Solapamiento parcial entre dos intervalos

- **Dado** un turno de `10:00` a `10:30` y otro turno de `10:15` a `10:45`
- **Cuando** se evalúa `solapan(a, b)` y `solapan(b, a)`
- **Entonces** ambas llamadas devuelven `True`

#### Scenario: Intervalo completamente contenido dentro de otro

- **Dado** un intervalo de `10:00` a `12:00` y otro de `10:30` a `11:00`
- **Cuando** se evalúa `solapan(a, b)` y `solapan(b, a)`
- **Entonces** ambas llamadas devuelven `True`

#### Scenario: Intervalos con el mismo instante de inicio

- **Dado** un turno de `10:00` a `10:30` y otro turno de `10:00` a `10:45`
- **Cuando** se evalúa `solapan(a, b)`
- **Entonces** devuelve `True`

### Requirement: Verificación de turno futuro con reloj inyectado

El dominio SHALL determinar si un turno o intervalo es futuro mediante `es_futuro(turno, ahora)` recibiendo el instante actual `ahora` como parámetro explícito sin consultar el reloj del sistema (`RN-TUR-09`). La función SHALL devolver `True` únicamente cuando `turno.inicio > ahora`, y `False` cuando `turno.inicio <= ahora`.

#### Scenario: Turno con inicio posterior al reloj inyectado es futuro

- **Dado** un reloj fijo `ahora` a las `09:00` y un turno con inicio a las `10:00`
- **Cuando** se evalúa `es_futuro(turno, ahora)`
- **Entonces** devuelve `True`

#### Scenario: Turno con inicio igual al reloj inyectado no es futuro

- **Dado** un reloj fijo `ahora` a las `09:00` y un turno con inicio exactamente a las `09:00`
- **Cuando** se evalúa `es_futuro(turno, ahora)`
- **Entonces** devuelve `False`

#### Scenario: Turno con inicio anterior al reloj inyectado no es futuro

- **Dado** un reloj fijo `ahora` a las `09:00` y un turno con inicio a las `08:30`
- **Cuando** se evalúa `es_futuro(turno, ahora)`
- **Entonces** devuelve `False`

### Requirement: Modelos y errores de dominio puros

El paquete `app/domain/` SHALL exponer las dataclasses inmutables `Turno`, `Prestacion`, `HorarioAtencion` y `Bloqueo` en `app/domain/models.py` y las excepciones `ErrorDominio`, `DatoInvalido`, `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo` y `TurnoNoModificable` en `app/domain/errores.py`, sin importar `fastapi`, `pydantic`, `sqlite3`, `app.db` ni `app.api`.

#### Scenario: Instanciación de modelos y jerarquía de errores sin dependencias externas

- **Dado** el paquete `app/domain/`
- **Cuando** se instancian `Turno`, `Prestacion`, `HorarioAtencion` y `Bloqueo` y se inspeccionan `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`, `TurnoNoModificable` y `DatoInvalido`
- **Entonces** todos los errores heredan de `ErrorDominio` y los módulos de `app/domain/` no importan `fastapi`, `sqlite3`, `app.db` ni `app.api`
