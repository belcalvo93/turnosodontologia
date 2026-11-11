# Evidencia de Verificación `C-18` — Hernán González

Verificación asignada sobre `main` (`0d4c82d`) tras la compilación final (`3.6`):

## 1. Tarea `4.1` — Verificación de tipos TypeScript

- **Comando ejecutado:** `npx tsc --noEmit`
- **Resultado:** salida vacía, código de retorno `0` (cero errores de tipos en `frontend/src/`).

## 2. Tarea `4.4` — Prueba manual en navegador del rol `recepcion` (`recepcion_demo`)

Probado contra el servidor local `uvicorn app.main:app` en `http://127.0.0.1:8000/` (`APP_ENV=development` con seed demo de `C-17`).

| # | Escenario verificado (`tasks.md §4.4`) | Cómo se probó | Resultado observado | Evidencia |
|---|---|---|---|---|
| 1 | Login ok y visibilidad RBAC (`RN-ACC-02`) | Ingreso con `recepcion_demo` | Barra muestra únicamente `Agenda de profesional` y `Crear turno` (`#nav-crear-bloqueo` oculto) | [`01-recepcion-agenda-con-paciente.png`](01-recepcion-agenda-con-paciente.png) |
| 2 | Consulta de agenda con pacientes ficticios (`RN-PAC-03`) | Consulta de `Odontólogo Ficticio A` (`17/11/2026 08:00–20:00`) | Muestra bloqueo profesional y turno `reservado` con `Paciente Ficticio 1` y `DNI 00000001 (ficticio)` | [`01-recepcion-agenda-con-paciente.png`](01-recepcion-agenda-con-paciente.png) |
| 3 | Agenda sin turnos ni bloqueos (caso de borde `items = []`) | Consulta de día sin eventos (`25/11/2026 08:00–20:00`) | Muestra `0 horarios en agenda` y estado vacío `"No hay turnos ni bloqueos en este período"` | [`02-recepcion-agenda-vacia.png`](02-recepcion-agenda-vacia.png) |
| 4 | Recurso inactivo excluido de selectores (`RN-REC-03`) | Desactivación temporal de `Sillón 2` vía `PATCH /sillones/2` (`{"activo": false}`), carga de `Crear turno` y restauración posterior (`{"activo": true}`) | Con `activo: false`, `#turno-sillon` listó únicamente `Sillón 1` (sin `Sillón 2`); al restaurar `activo: true`, volvió a listar `["Sillón 1", "Sillón 2"]` | Verificado en DOM y log HTTP (`PATCH /sillones/2` 200 OK) |
| 5 | Error `409` al crear turno solapado o bloqueado (`RN-TUR-03`, `RN-TUR-05`, `RN-GLO-01`) | Envío de turno el `17/11/2026 09:00` sobre horario bloqueado | `POST /turnos` → `409 Conflict`; muestra `"No se pudo registrar el turno / El profesional está bloqueado en ese horario."` sin limpiar los selectores | [`03-recepcion-crear-turno-409.png`](03-recepcion-crear-turno-409.png) |
| 6 | Error `422` por datos inválidos (`RN-GLO-01`) | Envío del formulario sin fecha/hora válida en `#turno-inicio` | `POST /turnos` → `422 Unprocessable Content`; muestra `"Los datos enviados no son válidos."` con el detalle `"Fecha y hora de inicio: Valor inválido."` | [`04-recepcion-crear-turno-422.png`](04-recepcion-crear-turno-422.png) |
