# Evidencia de Verificación `C-18` — Bruno Fiouchetta

Verificación asignada sobre `main` (`43875e0`), después de la compilación final (`3.6`) y del merge de la verificación de Elías (PR #66).

## 1. Tarea `4.4` — Prueba manual en navegador del rol `administracion` (`admin_demo`)

Probado contra el servidor local `uvicorn app.main:app` en `http://127.0.0.1:8000/` (`APP_ENV=development`, `CLINIC_TIMEZONE=America/Argentina/Buenos_Aires`, seed demo de `C-17` y una base SQLite nueva fuera del repositorio). El seed no trae turnos, así que el turno usado en los bloqueos se creó en el escenario 2 desde la misma sesión de `admin_demo`.

| # | Escenario verificado (`tasks.md §4.4`) | Cómo se probó | Resultado observado | Evidencia |
|---|---|---|---|---|
| 1 | Login ok y visibilidad por rol (`RN-ACC-02`) | Ingreso con `admin_demo` | La barra muestra las tres vistas (`Agenda de profesional`, `Crear turno` y `Crear bloqueo`), con el usuario `admin_demo` y la etiqueta `ADMINISTRACIÓN` | [`01-administracion-login-vistas.jpg`](01-administracion-login-vistas.jpg) |
| 2 | Crear turno válido (`201`) | `Paciente Ficticio 1`, `Odontólogo Ficticio A`, `Sillón 1`, `Limpieza ficticia (45 min)`, inicio `18/11/2026 10:00` | `POST /turnos` → `201 Created`; muestra `"Turno reservado con éxito"` con estado `reservado` y el fin calculado por la prestación: `Turno #1 ... el 18/11/2026 de 10:00 a 10:45` | [`02-administracion-crear-turno-201.jpg`](02-administracion-crear-turno-201.jpg) |
| 3 | Bloqueo superpuesto con `turnos_afectados` sin cancelar el turno (`SE-09`) | Bloqueo de `Odontólogo Ficticio A` el `18/11/2026` de `09:00` a `13:00`, motivo `Congreso odontológico ficticio` | `POST /bloqueos` → `201 Created`; muestra `"Bloqueo horario registrado"` y la tabla con `1 turno afectado`: el turno `#1` de `10:00` a `10:45` sigue en estado `reservado`. El panel no tiene botones de acción ni de exportación | [`03-administracion-bloqueo-turnos-afectados.jpg`](03-administracion-bloqueo-turnos-afectados.jpg) |
| 4 | Bloqueo sin turnos superpuestos (caso de borde `turnos_afectados = []`) | Bloqueo de `Sillón 2` el `19/11/2026` de `09:00` a `11:00`, motivo `Mantenimiento de equipo ficticio` | `POST /bloqueos` → `201 Created`; muestra `0 turnos afectados`, oculta la tabla y muestra el aviso `#turnos-afectados-vacio`: `"No hay turnos afectados en este horario"` | [`04-administracion-bloqueo-sin-turnos-afectados.jpg`](04-administracion-bloqueo-sin-turnos-afectados.jpg) |
| 5 | Intervalo de bloqueo inválido → `422` en español (`RN-REC-02`, `RN-GLO-01`) | Bloqueo de `Sillón 2` con inicio `20/11/2026 12:00` y fin `20/11/2026 11:00` (`inicio >= fin`) | `POST /bloqueos` → `422 Unprocessable Content` con `{"codigo": "dato_invalido", "mensaje": "El inicio del bloqueo debe ser anterior al fin."}`; muestra `"No se pudo registrar el bloqueo horario"` con ese mensaje y no muestra la tabla de turnos afectados | [`05-administracion-bloqueo-422.jpg`](05-administracion-bloqueo-422.jpg) |
