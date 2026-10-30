# Design — C-14 agenda

## 1. Arquitectura y Componentes

Siguiendo la arquitectura desacoplada del proyecto (D-02) y las reglas de `AGENTS.md`:

```
[Cliente HTTP]
      │
      ▼
[app/api/agenda.py]
      │  - Validación de rango (desde <= hasta) -> 422
      │  - Control RBAC (odontólogo solo su propia agenda) -> 403
      │  - Verificación de existencia de recurso -> 404
      ▼
[app/db/repositorio_agenda.py]
      │  - Consultas SQL parametrizadas (?)
      ▼
[SQLite: turno + bloqueo + profesional + sillon]
```

---

## 2. Capa de Base de Datos (`app/db/repositorio_agenda.py`)

### Consultas SQL Parametrizadas
Para garantizar que se devuelvan los eventos que intersectan el intervalo `[desde, hasta]`:
- Un evento pertenece al rango si `inicio < hasta AND fin > desde`.
- Los turnos cancelados se excluyen (`WHERE estado = 'reservado'`).
- Los resultados se ordenan estrictamente por `inicio ASC`.

```sql
-- Turnos de un profesional en el rango
SELECT id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado
FROM turno
WHERE profesional_id = ? AND estado = 'reservado' AND inicio < ? AND fin > ?
ORDER BY inicio ASC;

-- Bloqueos de un profesional en el rango
SELECT id, alcance, recurso_id, inicio, fin, motivo
FROM bloqueo
WHERE alcance = 'profesional' AND recurso_id = ? AND inicio < ? AND fin > ?
ORDER BY inicio ASC;

-- Turnos de un sillón en el rango
SELECT id, paciente_id, profesional_id, sillon_id, prestacion_id, inicio, fin, estado
FROM turno
WHERE sillon_id = ? AND estado = 'reservado' AND inicio < ? AND fin > ?
ORDER BY inicio ASC;

-- Bloqueos de un sillón en el rango
SELECT id, alcance, recurso_id, inicio, fin, motivo
FROM bloqueo
WHERE alcance = 'sillon' AND recurso_id = ? AND inicio < ? AND fin > ?
ORDER BY inicio ASC;
```

---

## 3. Capa API y Modelos Pydantic (`app/api/agenda.py`)

### Esquemas de Datos
```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class ItemAgenda(BaseModel):
    tipo: Literal["turno", "bloqueo"]
    id: int
    inicio: datetime
    fin: datetime
    paciente_id: int | None = None
    profesional_id: int | None = None
    sillon_id: int | None = None
    prestacion_id: int | None = None
    estado: str | None = None
    alcance: str | None = None
    recurso_id: int | None = None
    motivo: str | None = None

class AgendaResponse(BaseModel):
    recurso_tipo: Literal["profesional", "sillon"]
    recurso_id: int
    desde: datetime
    hasta: datetime
    items: list[ItemAgenda]
```

### Endpoints y Reglas de Negocio

#### `GET /agenda/profesionales/{id}`
- **Parámetros Query:** `desde: datetime`, `hasta: datetime`.
- **Validación de fechas:** Si `desde > hasta` → lanza `DatoInvalido("El rango de fechas es inválido: 'desde' no puede ser posterior a 'hasta'.")` (mapeado globalmente a HTTP 422).
- **Control RBAC:**
  - Si `usuario.rol == "odontologo"`:
    - Se verifica que `usuario.profesional_id == id`. Si no coincide, responde HTTP 403 (`SinPermiso`).
  - Si `usuario.rol in ("administracion", "recepcion")`:
    - Permite la consulta de cualquier profesional.
- **Existencia de recurso:**
  - Si el profesional no existe en la tabla `profesional`, responde HTTP 404 (`ProfesionalNoEncontrado`).

#### `GET /agenda/sillones/{id}`
- **Parámetros Query:** `desde: datetime`, `hasta: datetime`.
- **Validación de fechas:** Si `desde > hasta` → lanza `DatoInvalido` (HTTP 422).
- **Control RBAC:**
  - Si `usuario.rol == "odontologo"`:
    - Responde HTTP 403 (`SinPermiso`), ya que la matriz RBAC otorga a los odontólogos visibilidad exclusivamente sobre su propia agenda profesional.
  - Si `usuario.rol in ("administracion", "recepcion")`:
    - Permite la consulta de cualquier sillón.
- **Existencia de recurso:**
  - Si el sillón no existe en la tabla `sillon`, responde HTTP 404 (`SillonNoEncontrado`).

---

## 4. Cumplimiento de Reglas Duras del Proyecto

- **Regla dura 1:** El repositorio de agenda y los routers de API no contaminan `app/domain/`.
- **Regla dura 4:** Todas las sentencias SQL usan parámetros posicionales `?`.
- **Regla dura 7:** Respuestas de error estructuradas en español con códigos HTTP normalizados (401, 403, 404, 422).
- **Regla dura 10:** Todos los fixtures de pruebas usan datos explícitamente ficticios.
- **Regla dura 12:** Código en `snake_case` con anotaciones de tipo completas para Python 3.11.
