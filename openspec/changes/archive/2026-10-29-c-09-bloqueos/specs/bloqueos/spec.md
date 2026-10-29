# Spec Delta

## Purpose

Gestión de bloqueos horarios por profesional o por sillón: permite a administración registrar intervalos de indisponibilidad validando que `inicio < fin` y que el recurso exista, consultarlos desde cualquier rol autenticado y eliminarlos para liberar nuevamente el horario.

## ADDED Requirements

### Requirement: Creación de bloqueo sobre profesional o sillón

El sistema SHALL permitir al rol `administracion` crear un bloqueo mediante `POST /bloqueos` indicando `alcance` (`profesional` o `sillon`), `recurso_id`, `inicio`, `fin` y `motivo`, siempre que `inicio < fin` y que el `recurso_id` corresponda a un profesional o sillón existente según el `alcance`. Cuando los datos son válidos, SHALL persistir el bloqueo y responder `201`.

#### Scenario: Alta válida de bloqueo para un profesional

- **Dado** un usuario autenticado con rol `administracion` y un profesional existente
- **Cuando** envía `POST /bloqueos` con `alcance = "profesional"`, el `recurso_id` de ese profesional, `inicio = "2026-11-10T09:00:00"`, `fin = "2026-11-10T13:00:00"` y `motivo = "Vacaciones"`
- **Entonces** el sistema responde `201` con el bloqueo creado e identificador asignado

#### Scenario: Rechazo por intervalo inválido (inicio mayor o igual que fin)

- **Dado** un usuario autenticado con rol `administracion` y un sillón existente
- **Cuando** envía `POST /bloqueos` con `inicio` igual o posterior a `fin`
- **Entonces** el sistema responde `422` con un mensaje de error en español y no persiste el bloqueo

#### Scenario: Rechazo por recurso inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `POST /bloqueos` con `alcance = "profesional"` (o `"sillon"`) y un `recurso_id` que no existe en la tabla correspondiente
- **Entonces** el sistema responde `422` con un mensaje de error en español y no persiste el bloqueo

### Requirement: Consulta y eliminación de bloqueos

El sistema SHALL exponer `GET /bloqueos` para cualquier usuario autenticado (`administracion`, `recepcion` u `odontologo`) devolviendo `200` con la lista de bloqueos registrados, y SHALL permitir al rol `administracion` eliminar un bloqueo existente mediante `DELETE /bloqueos/{id}`, respondiendo `404` si el identificador no existe.

#### Scenario: Eliminar bloqueo existente libera el registro

- **Dado** un bloqueo registrado y un usuario autenticado con rol `administracion`
- **Cuando** envía `DELETE /bloqueos/{id}` y luego consulta `GET /bloqueos`
- **Entonces** la eliminación responde exitosamente y el bloqueo ya no figura en el listado

#### Scenario: Eliminar bloqueo inexistente

- **Dado** un usuario autenticado con rol `administracion`
- **Cuando** envía `DELETE /bloqueos/9999` para un identificador que no existe
- **Entonces** el sistema responde `404` con un mensaje de error en español

### Requirement: Control de acceso por rol en bloqueos

El sistema SHALL exigir autenticación en todas las rutas de `/bloqueos` (`401` sin token válido) y SHALL restringir `POST /bloqueos` y `DELETE /bloqueos/{id}` al rol `administracion`, respondiendo `403` si un usuario con rol `recepcion` u `odontologo` intenta crear o eliminar un bloqueo.

#### Scenario: Recepción intenta crear un bloqueo

- **Dado** un usuario autenticado con rol `recepcion` y un profesional existente
- **Cuando** envía `POST /bloqueos` con datos válidos
- **Entonces** el sistema responde `403` con un mensaje de error en español y no crea el bloqueo

#### Scenario: Odontólogo intenta eliminar un bloqueo

- **Dado** un usuario autenticado con rol `odontologo` y un bloqueo existente
- **Cuando** envía `DELETE /bloqueos/{id}`
- **Entonces** el sistema responde `403` con un mensaje de error en español y el bloqueo permanece registrado
