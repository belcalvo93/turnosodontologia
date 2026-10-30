# Evidencia: uso del MCP Context7 en la preparación de C-16

**Fecha:** 2026-10-29

**Herramienta:** MCP Context7, servidor remoto `https://mcp.context7.com/mcp`, habilitado en la configuración global de OpenCode (`~/.config/opencode/opencode.json`) sin clave.

**Comprobación de conexión:** `opencode mcp list` → resultado: `context7 connected`, `engram connected`.

**Solicitud textual recibida:**

> Usá el MCP context7 (resolvé el id de la librería con context7_resolve-library-id y consultá con context7_query-docs) para consultar la documentación oficial de FastAPI sobre cómo se serializa la respuesta cuando una ruta declara un modelo de respuesta que HEREDA de otro (por ejemplo BloqueoCreadoSalida que extiende BloqueoSalida con un campo extra), y qué pasa con los campos extra si la ruta GET sigue usando el modelo base. Con eso, decime si la tarea 3.3 de openspec/changes/c-16-bloqueos-turnos-afectados/tasks.md (BloqueoCreadoSalida solo para POST, GET sin turnos_afectados) es consistente con lo que dice la documentación, o si hay que ajustar algo. No modifiques ningún archivo. Mostrame: qué library id usaste, qué consultaste exactamente, qué devolvió y qué aporta al change.

---

## 1. Library ID usado

`resolve-library-id` con el nombre "FastAPI" devolvió 5 opciones; se usó la principal, la que refleja la documentación oficial (fastapi.tiangolo.com):

- **`/websites/fastapi_tiangolo`** — "FastAPI", fuente High reputation, 6.499 snippets, benchmark 78.12.

## 2. Consultas exactas y qué devolvió

### Consulta A
> *"How does FastAPI serialize the response when a path operation declares a response_model class that inherits from another Pydantic model (subclass adds extra fields)? Does the response include the inherited fields and subclass fields when the route uses the subclass?"*

Devolvió 4 resultados relevantes:

1. **Release notes 0.30.0 (PR #322)** — el comportamiento clave para la pregunta: cuando se declara un `response_model`, FastAPI lo **"clona"** antes de usarlo. Esto existe justamente por el caso opuesto al del change: si se devuelve una subclase (ej. `UserInDB` que hereda de `User` con `hashed_password`) pero el `response_model` es el modelo base (`User`), la subclase **no** "pasa como viene" por ser instanceof del base — se construye un objeto nuevo del modelo clonado y **se filtra a los campos declarados**. Texto literal: *"it will be a new object (made with the data from the returned one), and will be filtered by the cloned response_model, containing only the declared fields as normally."*

2. **Tutorial `response-model` → "Filter response data using return type annotation"** — el patrón exacto de herencia: `class UserIn(BaseUser)` suma `password`, y el endpoint `create_user` declara `-> BaseUser`. FastAPI filtra la salida a los campos del modelo anotado.

3. **Tutorial `extra-models` → "UserBase + UserIn/UserOut/UserInDB"** — ejemplo canónico de la misma herencia con destino distinto: `UserOut(UserBase)` con `pass`, el endpoint declara `response_model=UserOut` y devuelve un `UserInDB` (subclase con campo extra), y la contraseña hasheada no aparece en el JSON.

4. **Reference de `APIRouter`/`FastAPI` (`response_model`)** — enumera los 4 usos del parámetro: *Documentation* (OpenAPI), *Serialization*, **Filtering** y *Validation*.

### Consulta B
> *"response_model filtering: what happens to extra fields present in the returned object that are NOT declared in the response_model? Are they removed from the JSON response?"*

Devolvió cita literal del reference oficial:

> *"**Filtering**: the JSON sent to the client will only contain the data (fields) defined in the `response_model`. If you returned an object that contains an attribute `password` but the `response_model` does not include that field, the JSON sent to the client would not have that `password`."*

(Devolvió la misma cita en `/reference/apirouter/` y `/reference/fastapi/`, más el release note 0.30.0 y dos ejemplos del tutorial.)

## 3. Qué aporta esto al change C-16

La doc oficial responde las tres preguntas clave de las tareas:

| Situación del change | Qué dice la doc |
|---|---|
| `BloqueoCreadoSalida(BloqueoSalida)` con `turnos_afectados` extra, `response_model` de `POST` = la subclase | Patrón exacto del tutorial (`UserOut(UserBase)` + `response_model=UserOut`): el modelo de salida que hereda de otro declarado como `response_model` **serializa los campos heredados + los propios**. ✔ |
| ¿Y si por error una ruta `GET` devolviera un objeto con `turnos_afectados` pero declaran el modelo base? | PR #322 + "Filtering": los campos extra **no declarados se eliminan del JSON** — no hay fuga accidental. ✔ |
| ¿`GET /bloqueos` puede seguir con `BloqueoSalida` sin el campo? | Sí, y es la elección correcta: el `response_model` también define el **JSON Schema de OpenAPI**, así que con el modelo base la doc de `GET /bloqueos` no mostrará `turnos_afectados` — coherente con el D-A2 (evita N+1 en el listado). ✔ |

## 4. Veredicto sobre la tarea 3.3

**Es consistente con la documentación, sin ajustes necesarios.** Específicamente:

- **`BloqueoCreadoSalida(BloqueoSalida)` solo para `POST`** es exactamente el patrón del tutorial oficial de herencia de modelos de salida, extendido vía el parámetro `response_model`.
- **GET con el modelo base sin el campo extra** es doblemente correcto según la doc: (a) la subclase con extra será filtrada aunque se devuelva por error (PR #322), y (b) mantener el modelo base en `GET` es lo que garantiza que el contrato OpenAPI del listado no publique el campo.
- El pariente cercano (test 3.2 de que `GET` no contenga la clave `turnos_afectados`) y la aserción del C-09 (4.1) quedan alineados con los ejemplos `UserIn`/`UserOut` de la doc, donde se verifica que el campo excluido no llega al cliente.

Única observación fina (no es un ajuste al change, es un detalle de implementación para 3.3): al construir la salida de `POST` conviene instanciar `BloqueoCreadoSalida` explícitamente (con `turno_a_response(...)` para cada turno) y devolver ese objeto, tal como pide la tarea — devolver un dict crudo también funcionaría porque FastAPI valida y serializa con el `response_model`, pero el objeto tipado es lo que el patrón de la doc recomienda y lo que hace type-checking real.

---

## Revisión crítica del resultado

- La consulta confirmó el diseño de la tarea 3.3 sin cambiarlo; el aporte es verificación contra la documentación oficial, no un cambio al change.
- Una de las fuentes devueltas es una nota de la versión 0.30.0 de FastAPI (clonado del response_model), histórica respecto de la versión del proyecto (FastAPI 0.14x o superior con Pydantic 2); el comportamiento sigue siendo válido porque lo confirma el texto vigente de "Filtering" de la referencia, pero no debe citarse esa nota como respaldo de la versión actual.
- El proyecto declara la salida con anotación de retorno (`-> TurnoResponse`) y no con el parámetro `response_model`; en la tarea 3.3 el POST debe declarar `-> BloqueoCreadoSalida`. Es un detalle para el apply.
