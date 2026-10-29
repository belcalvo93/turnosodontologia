# Explore — C-08 horarios-atencion

> Relevamiento previo al propose de `C-08 horarios-atencion`.
> Durante la exploración no se modificó ningún archivo de código ni de la KB.

## 1. Qué pide C-08 (`CHANGES.md` L279-293)

| Ítem | Contenido |
|---|---|
| Tabla | `horario_atencion` (`id`, `profesional_id`, `dia_semana` 0-6, `hora_desde`, `hora_hasta`) con índice (`profesional_id`, `dia_semana`) |
| Dominio | Validar `hora_desde < hora_hasta` y que las franjas del mismo día no se superpongan |
| Endpoints | `GET /profesionales/{id}/horarios` y `POST /profesionales/{id}/horarios` |
| Permisos | Administración escribe (`POST`); recepción lee (`GET`); odontólogo lee solo los propios (`GET` con `usuario.profesional_id == id`) |
| Tests exigidos | Dominio: franja invertida inválida, dos franjas por día (mañana y tarde) válidas, franjas superpuestas inválidas; API: profesional inexistente → 422 |
| Dependencias | `C-02` (`dominio-base`) y `C-04` (`profesionales`), governance **MEDIO** |

De la KB:
- **Modelo (`04_modelo_de_datos.md` §HorarioAtencion):**
  - `id` (PK), `profesional_id` (FK), `dia_semana` (0 = lunes ... 6 = domingo), `hora_desde` (HH:MM), `hora_hasta` (HH:MM).
  - Constraints: `hora_desde < hora_hasta`; un profesional puede tener varias franjas por día (ej. mañana y tarde); las franjas del mismo día no se superponen (SE).
  - Índice: (`profesional_id`, `dia_semana`).
- **Funcionalidades (`06_funcionalidades.md` §US-004):**
  - Como administración quiero cargar los días y franjas horarias de cada profesional para que no se den turnos fuera de su horario.
  - Criterios: una o más franjas por día; franja con `hora_desde >= hora_hasta` es inválida.
- **Reglas (`05_reglas_de_negocio.md`):**
  - `RN-PRO-01`: Cada profesional tiene horarios de atención por día de la semana; fuera de ellos no se le asignan turnos.
  - `RN-PRO-02`: Un turno debe quedar completo dentro de una misma franja de atención del profesional (no puede empezar dentro y terminar fuera, ni cruzar el corte entre mañana y tarde).
  - `RN-ACC-02` / `03_actores_y_roles.md`: Horarios de atención: Administración `C L E B`, Recepción `L`, Odontólogo `L (propios)`.
  - `RN-GLO-01`: Mensajes en español y códigos HTTP consistentes (422 dato inválido, 403 sin permiso, 401 no autenticado).

## 2. Estado actual del repositorio

- `C-02` completado: `HorarioAtencion` definido en `app/domain/models.py`, `solapan` y `es_futuro` en `app/domain/intervalos.py`.
- `C-04` completado: tabla `profesional`, `repositorio_profesionales.py`, `obtener_profesional_por_id(conexion, id)` disponible.
- `app/domain/reglas_turno.py` ya utiliza `HorarioAtencion` en `_encaja_en_franja(inicio, fin, profesional_id, h)`.
- `app/api/auth.py` provee `usuario_actual` y `requiere_rol`.

## 3. Decisiones de diseño

1. **Dominio puro:**
   - Dataclass `HorarioAtencion` con `id: int | None = None`.
   - Funciones puras:
     - `validar_datos_horario(profesional_id, dia_semana, hora_desde, hora_hasta, id=None) -> HorarioAtencion`: valida rango 0..6 y `hora_desde < hora_hasta`, lanzando `DatoInvalido` ante error.
     - `validar_franjas_no_superpuestas(franjas: Sequence[HorarioAtencion]) -> None`: valida que ninguna franja del mismo día se superponga utilizando intervalos semiabiertos `[hora_desde, hora_hasta)`.
     - `validar_horario_no_solapa(candidato: HorarioAtencion, existentes: Sequence[HorarioAtencion]) -> None`: valida que una franja candidata no colisione con las franjas existentes del profesional en ese día.
2. **Esquema y persistencia SQLite:**
   - Tabla `horario_atencion` con `profesional_id REFERENCES profesional(id)`, `CHECK (dia_semana BETWEEN 0 AND 6)` y `CHECK (hora_desde < hora_hasta)`.
   - Índice `idx_horario_profesional_dia` sobre `(profesional_id, dia_semana)`.
   - Funciones en `app/db/repositorio_horarios.py`: `crear_horario`, `listar_horarios_por_profesional`, `listar_horarios_por_profesional_y_dia`.
3. **API y control de acceso:**
   - Router `app/api/horarios.py` montado en `create_app`:
     - `POST /profesionales/{id}/horarios`: solo `administracion`. Si el profesional no existe, devuelve `422` (`DatoInvalido`). Si los datos son inválidos o se superpone con una franja existente, devuelve `422`. Responde `201` con la franja creada.
     - `GET /profesionales/{id}/horarios`: autenticado. Si el usuario es `odontologo` y su `profesional_id != id`, devuelve `403`. Si el profesional no existe, devuelve `404`. Devuelve `200` con la lista de franjas ordenadas por `dia_semana ASC, hora_desde ASC`.

## 4. Fuentes

- `CHANGES.md` §C-08 (L279-293)
- `knowledge-base/04_modelo_de_datos.md` §HorarioAtencion
- `knowledge-base/06_funcionalidades.md` §US-004
- `knowledge-base/05_reglas_de_negocio.md` §RN-PRO-01, §RN-PRO-02
- `knowledge-base/03_actores_y_roles.md` §RBAC
- `knowledge-base/10_preguntas_abiertas.md` §SE-14
