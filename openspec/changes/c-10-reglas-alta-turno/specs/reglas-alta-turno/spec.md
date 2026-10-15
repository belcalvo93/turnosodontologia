# Spec Delta

## Purpose

Validación de alta de turnos en dominio puro: calcula el fin desde la prestación y rechaza lo que esté fuera de horario, en bloqueo o solapado.

## ADDED Requirements

### Requirement: Validar alta de turno

El sistema SHALL validar el alta de un turno en dominio puro: calcula `fin = inicio + duracion_minutos`, exige encaje completo en una única franja de atención, rechaza solapamiento con bloqueos del profesional o del sillón, y rechaza solapamiento con turnos activos del mismo profesional, sillón o paciente usando intervalos semiabiertos `[inicio, fin)`. Los turnos cancelados no generan conflicto y `excluir_turno_id` excluye el propio turno.

#### Scenario: Alta exitosa de un turno

- **Dado** la prestación "Limpieza ficticia" de 30 minutos, el profesional "Odontólogo Ficticio A", el "Sillón 1", el paciente "Paciente Ficticio 1" (DNI "00000001 (ficticio)"), horario lunes 09:00-13:00, sin bloqueos ni turnos activos
- **Cuando** se valida el alta con inicio lunes 10:00
- **Entonces** el sistema devuelve el turno armado con `fin` 10:30 y sin errores

#### Scenario: Validación fallida por solapamiento del profesional

- **Dado** un turno activo del profesional "Odontólogo Ficticio A" de 10:00 a 10:30 en el "Sillón 1" y una solicitud del mismo profesional de 10:15 a 10:45 con el "Sillón 2"
- **Cuando** se valida el alta de la solicitud
- **Entonces** el sistema lanza `ConflictoAgenda` y no arma ningún turno

#### Scenario: Turnos contiguos en el límite del horario

- **Dado** un turno activo de 10:00 a 10:30 del profesional "Odontólogo Ficticio A" en el "Sillón 1" y una solicitud del mismo profesional y sillón de 10:30 a 11:00 dentro de la franja 09:00-13:00
- **Cuando** se valida el alta de la solicitud
- **Entonces** el sistema la acepta porque los intervalos son semiabiertos `[inicio, fin)` y los turnos contiguos son válidos
