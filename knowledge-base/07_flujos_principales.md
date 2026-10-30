# Flujos Principales

Flujos extremo a extremo del MVP. Los datos de ejemplo son ficticios. Los nombres de endpoints son propuesta (ver 02).

## Flujo 1: Iniciar sesión
**Disparador**: un usuario quiere operar el sistema.
**Actor**: administración, recepción u odontólogo.

**Pasos**:
1. El cliente envía `POST /auth/login` con usuario y contraseña.
2. `app/api` busca el usuario en `app/db` y verifica el hash.
3. Si es válido, emite un token con el rol y el id de usuario (mecanismo a confirmar, ver D-03).
4. Cada request siguiente envía el token; una dependencia de FastAPI lo valida y carga el usuario y su rol.

```
Cliente --> API (/auth/login) --> DB (usuario)
                               <-- token
```

**Casos de error**:
- Credenciales inválidas -> 401.
- Token ausente, inválido o vencido -> 401.
- Rol sin permiso para la ruta -> 403.

## Flujo 2: Crear un turno
**Disparador**: un paciente pide un turno por teléfono o en persona.
**Actor**: recepción (o administración).

**Pasos**:
1. Recepción envía `POST /turnos` con paciente, profesional, sillón, prestación e inicio.
2. `app/api` valida permisos (RN-ACC-02) y el esquema de entrada.
3. `app/api` abre una transacción en `app/db` y carga: la prestación, los horarios del profesional, los bloqueos del profesional y del sillón, y los turnos activos del profesional, del sillón y del paciente cercanos al intervalo.
4. `app/domain` calcula `fin = inicio + duración` (RN-TUR-01) y valida: horario (RN-PRO-01/02), bloqueos (RN-TUR-05), solapamiento por profesional y por sillón (RN-TUR-03/04) y por paciente (RN-TUR-12).
5. Si todo es válido, `app/db` inserta el turno `reservado` y el registro de auditoría en la misma transacción (RN-AUD-01, RN-AUD-03) y confirma.
6. La API responde 201 con el turno.

```
Recepción --> API --> DB (lee contexto)
                  --> Dominio (valida) 
                  --> DB (inserta turno + auditoría, commit)
                  <-- 201
```

**Casos de error**:
- Solapamiento de profesional o sillón (o paciente) -> 409 con detalle del turno en conflicto, sin cambios.
- Fuera de horario o dentro de bloqueo -> 409 con motivo (RN-GLO-01).
- Profesional, sillón o prestación inexistente o inactivo -> 422.
- Dos reservas simultáneas del mismo hueco: la segunda ve el conflicto porque la verificación y la inserción ocurren en una única transacción de escritura (concurrencia: SE-06).

## Flujo 3: Cancelar un turno
**Disparador**: el paciente avisa que no va.
**Actor**: recepción (o administración).

**Pasos**:
1. `POST /turnos/{id}/cancelar`.
2. La API carga el turno y valida permisos.
3. El dominio verifica que sea futuro y que no esté ya cancelado (RN-TUR-09, RN-TUR-10), con la hora actual inyectada.
4. `app/db` marca el turno `cancelado` y agrega la auditoría (antes/después) en una transacción.
5. El horario queda libre (RN-TUR-06).

**Casos de error**:
- Turno inexistente -> 404.
- Turno pasado o en curso -> 409 (RN-TUR-09).
- Turno ya cancelado -> 409.

## Flujo 4: Reprogramar un turno
**Disparador**: el paciente pide cambiar el horario.
**Actor**: recepción (o administración).

**Pasos**:
1. `POST /turnos/{id}/reprogramar` con nuevo inicio y, opcionalmente, nuevo profesional y/o sillón.
2. La API carga el turno y el contexto del nuevo intervalo.
3. El dominio verifica que el turno sea futuro y esté activo (RN-TUR-09/10), recalcula el fin con la prestación y aplica las mismas validaciones de creación excluyendo al propio turno (RN-TUR-07/08).
4. Si es válido, `app/db` actualiza el turno y registra la auditoría con valores antes/después en una transacción.

**Casos de error**:
- Nuevo horario ocupado, fuera de horario o bloqueado -> 409; el turno queda como estaba y no se audita un cambio (RN-AUD-03).
- Turno cancelado o pasado -> 409 (RN-TUR-09).

## Flujo 5: Bloquear un horario
**Disparador**: vacaciones, feriado o mantenimiento de un sillón.
**Actor**: administración.

**Pasos**:
1. `POST /bloqueos` con alcance (profesional o sillón), recurso, inicio, fin y motivo.
2. El dominio valida inicio < fin (RN-REC-02).
3. `app/db` guarda el bloqueo.
4. Desde ese momento, crear o reprogramar turnos en ese intervalo y recurso se rechaza (RN-TUR-05).
5. Turnos preexistentes dentro del bloqueo (SE-09, decisión tomada): el bloqueo se crea igual y NO se cancelan turnos; la respuesta de `POST /bloqueos` devuelve la lista de turnos afectados (solo turnos en estado reservado, ordenados por inicio ASC) para que recepción los reprograme a mano.

**Casos de error**:
- inicio >= fin -> 422.
- Recurso inexistente -> 422.

## Flujo 6: Consultar la agenda
**Disparador**: iniciar el día o planificar la semana.
**Actor**: recepción, administración, odontólogo (solo la propia).

**Pasos**:
1. `GET /agenda/profesionales/{id}?desde=&hasta=` o `GET /agenda/sillones/{id}?desde=&hasta=`.
2. La API valida permisos (RN-ACC-03).
3. `app/db` devuelve los turnos activos y bloqueos del rango, ordenados por inicio.

**Casos de error**:
- Rango inválido (desde > hasta) -> 422.
- Odontólogo consultando a otro profesional -> 403.

## Flujo 7: Consultar auditoría de un turno
**Actor**: administración.

**Pasos**: `GET /auditoria?turno_id=` -> la API devuelve los registros en orden cronológico con usuario, acción, antes/después y fecha y hora.

**Casos de error**: rol sin permiso -> 403.
