# Explore — C-14 agenda

> Relevamiento previo al propose. Guardado en el repositorio para trazabilidad del equipo.
> Durante la exploración no se modificó código de la aplicación.

## 1. Qué pide C-14 (`CHANGES.md` L388-403)

| Ítem | Contenido |
|---|---|
| Endpoints | `GET /agenda/profesionales/{id}?desde&hasta` y `GET /agenda/sillones/{id}?desde&hasta` |
| Alcance | Devuelve turnos activos y bloqueos del rango temporal solicitado, ordenados por fecha y hora de `inicio` (sirve para vistas diaria y semanal) |
| Permisos RBAC | `administracion` y `recepcion` pueden consultar cualquier agenda; `odontologo` solo puede consultar su propia agenda mediante `usuario.profesional_id` (`RN-ACC-03`, `03_actores_y_roles.md`); petición sin token responde 401 |
| Errores | `desde > hasta` → **422** (`DatoInvalido`); odontólogo consultando a otro profesional o un sillón → **403** (`SinPermiso`); recurso inexistente → **404**; sin autenticar → **401** |
| Tests exigidos | Orden cronológico por `inicio`, turnos cancelados excluidos (`RN-TUR-08`), bloqueos incluidos, rango invertido `desde > hasta` → 422, odontólogo A consultando agenda de odontólogo B → 403 |
| Dependencia | `C-11` (`crear-turno`), governance **MEDIO** |

### Relevamiento desde la Base de Conocimiento (KB)

- **US-009 (`06_funcionalidades.md`):** Como recepción, administración u odontólogo (este último solo la propia), ver la agenda diaria y semanal de un profesional para saber qué turnos tiene. Criterios de aceptación: devuelve turnos activos del rango ordenados por inicio; odontólogo recibe 403 si pide la agenda de otro profesional.
- **US-010 (`06_funcionalidades.md`):** Como recepción o administración, ver la agenda diaria y semanal de un sillón para saber cuándo está ocupado o libre. Criterios de aceptación: devuelve turnos activos del sillón en el rango ordenados por inicio; incluye los bloqueos del sillón en el rango.
- **Flujo 6 (`07_flujos_principales.md`):** `GET /agenda/profesionales/{id}?desde=&hasta=` o `GET /agenda/sillones/{id}?desde=&hasta=`. Pasos: La API valida permisos (`RN-ACC-03`), `app/db` devuelve turnos activos y bloqueos del rango ordenados por inicio. Errores: rango inválido (`desde > hasta`) → 422; odontólogo consultando a otro profesional → 403.
- **Regla `RN-ACC-03` (`05_reglas_de_negocio.md`):** Un odontólogo solo ve su propia agenda (odontólogo A pidiendo agenda de B devuelve 403).
- **Matriz RBAC (`03_actores_y_roles.md`):** "Agenda: ver (diaria/semanal)": administración y recepción = todas; odontólogo = solo la propia.

---

## 2. Estado Actual del Código y Dependencias

### Ya implementado en el repositorio
- **`C-03` (`auth-login-roles`):** Dependencias de autenticación `usuario_actual`, `requiere_rol` y modelo `Usuario` con campo `profesional_id` opcional.
- **`C-04` (`profesionales`):** Tabla `profesional` y repositorio para consultar existencia y estado de un profesional por ID.
- **`C-05` (`sillones-prestaciones`):** Tabla `sillon` y repositorio para consultar existencia y estado de un sillón por ID.
- **`C-08` (`horarios-atencion`):** Tabla `horario_atencion` y repositorios.
- **`C-09` (`bloqueos`, listo en rama de Bruno):** Tabla `bloqueo` (`alcance`, `recurso_id`, `inicio`, `fin`, `motivo`) e índice compuesto.

### Que proveerá `C-11` (`crear-turno`)
- Tabla `turno` con índices por `profesional_id`, `sillon_id`, `paciente_id` e `inicio`.
- Estados de turno: `reservado` y `cancelado`.

### Lo que agregará `C-14`
1. **Dominio puro o Servicios de Agenda:**
   - Estructuras o funciones auxiliares para validar el rango temporal (`desde <= hasta`).
   - Normalización y ordenamiento de eventos por `inicio`.
2. **Capa de Persistencia (`app/db/repositorio_agenda.py`):**
   - Consultas SQL parametrizadas para obtener turnos activos en el intervalo:
     `SELECT ... FROM turno WHERE profesional_id = ? AND estado = 'reservado' AND inicio < ? AND fin > ? ORDER BY inicio ASC`
   - Consultas SQL parametrizadas para obtener bloqueos en el intervalo:
     `SELECT ... FROM bloqueo WHERE alcance = ? AND recurso_id = ? AND inicio < ? AND fin > ? ORDER BY inicio ASC`
3. **Capa API (`app/api/agenda.py`):**
   - Endpoints:
     - `GET /agenda/profesionales/{id}?desde=...&hasta=...`
     - `GET /agenda/sillones/{id}?desde=...&hasta=...`
   - Parámetros query validados con Pydantic/FastAPI: `desde: datetime`, `hasta: datetime`.
   - Control RBAC estricto según `RN-ACC-03` y la matriz de actores.
   - Formato de respuesta con lista combinada y/o separada de turnos y bloqueos ordenados por `inicio`.

---

## 3. Riesgos Técnicos y Decisiones de Diseño

| # | Riesgo / Decisión | Criterio propuesto |
|---|---|---|
| 1 | **Rango temporal invertido (`desde > hasta`)** | Lanzar `DatoInvalido` (HTTP 422) cuando `desde > hasta`, cumpliendo con la regla dura #7 y la especificación de `CHANGES.md`. |
| 2 | **Filtrado de turnos cancelados (`RN-TUR-08`)** | La consulta SQL filtra estrictamente `WHERE estado = 'reservado'`. Los turnos en estado `cancelado` no ocupan agenda y se omiten de la respuesta. |
| 3 | **Criterio de solapamiento con el rango consultado** | Un evento (turno o bloqueo) pertenece al rango si intersecta la ventana consultada (`evento.inicio < hasta AND evento.fin > desde`). Esto asegura que turnos que cruzan la medianoche o los límites del día solicitado aparezcan en la vista diaria o semanal. |
| 4 | **Estructura del JSON de respuesta** | Proveer un objeto que contenga los metadatos del recurso consultado (`recurso_tipo`, `recurso_id`, `desde`, `hasta`), una lista cronológica unificada de `items` (cada uno con `tipo: "turno" | "bloqueo"`) y listas tipadas `turnos` y `bloqueos` para máxima flexibilidad del consumidor. |
| 5 | **RBAC para odontólogos consultando sillones** | Según la matriz de `03_actores_y_roles.md`, los odontólogos solo tienen permiso para "solo la propia" agenda. Por lo tanto, cualquier solicitud de un odontólogo a `GET /agenda/sillones/{id}` debe responder HTTP 403 (`SinPermiso`). |

---

## 4. Resumen

`C-14 agenda` implementa las vistas de consulta diaria y semanal de turnos activos y bloqueos para profesionales y sillones (`US-009`, `US-010`, `Flujo 6`). Requiere validación de rangos, filtrado estricto de turnos cancelados, orden cronológico y control RBAC granular para proteger la confidencialidad de la agenda entre profesionales.
