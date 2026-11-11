# Evidencia de Verificación `C-18` — Joaquín Moran

Verificación asignada sobre `main` (`22c1b82`) después de la compilación final (`3.6`).

## 1. Tarea `4.4` — Prueba manual en navegador del rol `odontologo` (`odontologo_demo`)

Probado contra el servidor local `uvicorn app.main:app` en `http://127.0.0.1:8000/` (`APP_ENV=development` con el seed demo de `C-17` y una base SQLite nueva). El seed no trae turnos, así que antes de entrar como odontólogo se creó el turno `#1` con `recepcion_demo` desde *Crear turno*: `Paciente Ficticio 1`, `Odontólogo Ficticio A`, `Sillón 1` y `Consulta ficticia`, de `09:00` a `09:30`. La API respondió `201` con estado `reservado`.

| # | Escenario verificado (`tasks.md §4.4`) | Cómo se probó | Resultado observado | Evidencia |
|---|---|---|---|---|
| 1 | Login ok y visibilidad por rol (`RN-ACC-02`) | Ingreso con `odontologo_demo` | La barra muestra únicamente `Agenda de profesional`, con el usuario `odontologo_demo` y la etiqueta `ODONTÓLOGO`. `Crear turno` y `Crear bloqueo` no aparecen | [`01-odontologo-agenda-propia.png`](01-odontologo-agenda-propia.png) |
| 2 | Odontólogo ve su propia agenda con `"Paciente #<id>"` sin error (`RN-ACC-03`) | Consulta de `Odontólogo Ficticio A`, el día del turno `#1`, de `08:00` a `20:00` | Muestra `1 horario en agenda`: el turno de `09:00` a `09:30`, estado `reservado`, `Paciente #1` (sin nombre ni DNI), `Consulta ficticia (30 min)` y `Sillón 1`. No aparece ningún mensaje de error | [`01-odontologo-agenda-propia.png`](01-odontologo-agenda-propia.png) |
| 3 | Agenda de otro profesional → `403` en español (`RN-ACC-03`, `RN-GLO-01`) | Selección de `Odontóloga Ficticia B` con el mismo rango y clic en `Consultar agenda` | Alerta `"No se pudo consultar la agenda"` con el mensaje `"Tu rol no tiene permiso para esta operación."`; la tabla queda vacía (`0 horarios en agenda`) | [`02-odontologo-agenda-otro-403.png`](02-odontologo-agenda-otro-403.png) |

**Observación (no bloquea):** después del `403`, la línea de resumen de la tabla sigue diciendo `Odontólogo Ficticio A`, que es el profesional de la consulta anterior. Pasa porque `limpiarTablaAnteError` (`frontend/src/vistas/agenda.ts`) vacía la tabla y pone el contador en `0`, pero no actualiza `#agenda-resumen-rango`. El escenario pedido se cumple igual: el error se muestra y no se ven datos de la Odontóloga Ficticia B.

## 2. README desde cero

Se siguió el `README.md` de `main` en una PC con Windows y Git Bash, donde el repo ya estaba clonado y había un `.venv` creado: `git pull`, activar `.venv`, `pip install -r requirements.txt` (Python 3.13.7), exportar las variables de *Variables de entorno* (bloque de bash), `uvicorn app.main:app` y abrir `http://127.0.0.1:8000/`. La app levantó con el seed demo y el frontend funcionó sin Node.js, con los `.js` compilados de `app/static/`. No se encontraron pasos del README que no coincidan.
