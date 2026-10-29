# Tasks — C-14 agenda

## 1. Repositorio de Base de Datos (`app/db/repositorio_agenda.py`)

- [ ] 1.1 Escribir tests para el repositorio de agenda en `tests/api/test_repositorio_agenda.py`:
  - [ ] Test: consulta de profesional devuelve turnos activos y bloqueos del rango ordenados por inicio.
  - [ ] Test: los turnos cancelados se excluyen de la consulta de agenda (RN-TUR-08).
  - [ ] Test: los eventos fuera del rango temporal `[desde, hasta]` no se incluyen.
  - [ ] Test: consulta de sillón devuelve turnos activos y bloqueos asignados al sillón ordenados por inicio.
- [ ] 1.2 Implementar `consultar_agenda_profesional` y `consultar_agenda_sillon` en `app/db/repositorio_agenda.py` con SQL parametrizado (`?`).

## 2. Router y API (`app/api/agenda.py`)

- [ ] 2.1 Definir los esquemas Pydantic `ItemAgenda` y `AgendaResponse`.
- [ ] 2.2 Implementar `GET /agenda/profesionales/{id}`:
  - [ ] Validación de `desde <= hasta` (lanza 422 si `desde > hasta`).
  - [ ] Verificación de existencia del profesional (404 si no existe).
  - [ ] Control de rol: odontólogo solo puede consultar si `usuario.profesional_id == id` (403 si no coincide).
- [ ] 2.3 Implementar `GET /agenda/sillones/{id}`:
  - [ ] Validación de `desde <= hasta` (422).
  - [ ] Verificación de existencia del sillón (404 si no existe).
  - [ ] Control de rol: solo administración y recepción (403 para odontólogo).
- [ ] 2.4 Montar el router de agenda en `app/main.py`.

## 3. Tests de API y Permisos (`tests/api/test_agenda.py`)

- [ ] 3.1 Tests de `GET /agenda/profesionales/{id}`:
  - [ ] Test: administración y recepción consultan agenda con turnos y bloqueos en orden cronológico (200 OK).
  - [ ] Test: odontólogo consulta exitosamente su propia agenda (200 OK).
  - [ ] Test: odontólogo A intentando consultar agenda de odontólogo B recibe 403 `SinPermiso` (RN-ACC-03).
  - [ ] Test: profesional inexistente responde 404.
  - [ ] Test: rango invertido (`desde > hasta`) responde 422 `DatoInvalido`.
  - [ ] Test: sin token de autenticación responde 401.
- [ ] 3.2 Tests de `GET /agenda/sillones/{id}`:
  - [ ] Test: administración y recepción consultan agenda de sillón (200 OK).
  - [ ] Test: odontólogo intentando consultar agenda de sillón recibe 403 `SinPermiso`.
  - [ ] Test: sillón inexistente responde 404.

## 4. Verificación y Cierre

- [ ] 4.1 Ejecutar suite completa con pytest y verificar que todos los tests pasen en verde.
- [ ] 4.2 Comprobar el cumplimiento de las reglas duras de `AGENTS.md`.
- [ ] 4.3 Redactar `verify.md` y documentar resultados.
