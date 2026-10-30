# Tasks — C-14 agenda

## 1. Repositorio de Base de Datos (`app/db/repositorio_agenda.py`)

- [x] 1.1 Escribir tests para el repositorio de agenda en `tests/api/test_repositorio_agenda.py`:
  - [x] Test: consulta de profesional devuelve turnos activos y bloqueos del rango ordenados por inicio.
  - [x] Test: los turnos cancelados se excluyen de la consulta de agenda (RN-TUR-08).
  - [x] Test: los eventos fuera del rango temporal `[desde, hasta]` no se incluyen.
  - [x] Test: consulta de sillón devuelve turnos activos y bloqueos asignados al sillón ordenados por inicio.
- [x] 1.2 Implementar `consultar_agenda_profesional` y `consultar_agenda_sillon` en `app/db/repositorio_agenda.py` con SQL parametrizado (`?`).

## 2. Router y API (`app/api/agenda.py`)

- [x] 2.1 Definir los esquemas Pydantic `ItemAgenda` y `AgendaResponse`.
- [x] 2.2 Implementar `GET /agenda/profesionales/{id}`:
  - [x] Validación de `desde <= hasta` (lanza 422 si `desde > hasta`).
  - [x] Verificación de existencia del profesional (404 si no existe).
  - [x] Control de rol: odontólogo solo puede consultar si `usuario.profesional_id == id` (403 si no coincide).
- [x] 2.3 Implementar `GET /agenda/sillones/{id}`:
  - [x] Validación de `desde <= hasta` (422).
  - [x] Verificación de existencia del sillón (404 si no existe).
  - [x] Control de rol: solo administración y recepción (403 para odontólogo).
- [x] 2.4 Montar el router de agenda en `app/main.py`.

## 3. Tests de API y Permisos (`tests/api/test_agenda.py`)

- [x] 3.1 Tests de `GET /agenda/profesionales/{id}`:
  - [x] Test: administración y recepción consultan agenda con turnos y bloqueos en orden cronológico (200 OK).
  - [x] Test: odontólogo consulta exitosamente su propia agenda (200 OK).
  - [x] Test: odontólogo A intentando consultar agenda de odontólogo B recibe 403 `SinPermiso` (RN-ACC-03).
  - [x] Test: profesional inexistente responde 404.
  - [x] Test: rango invertido (`desde > hasta`) responde 422 `DatoInvalido`.
  - [x] Test: sin token de autenticación responde 401.
- [x] 3.2 Tests de `GET /agenda/sillones/{id}`:
  - [x] Test: administración y recepción consultan agenda de sillón (200 OK).
  - [x] Test: odontólogo intentando consultar agenda de sillón recibe 403 `SinPermiso`.
  - [x] Test: sillón inexistente responde 404.

## 4. Verificación y Cierre

- [x] 4.1 Ejecutar suite completa con pytest y verificar que todos los tests pasen en verde.
- [x] 4.2 Comprobar el cumplimiento de las reglas duras de `AGENTS.md`.
- [x] 4.3 Redactar `verify.md` y documentar resultados.
