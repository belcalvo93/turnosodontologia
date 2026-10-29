# Explore — C-06 pacientes

Relevamiento previo al propose. **No implementa nada**: fija el estado actual, la brecha, los riesgos y las decisiones ya cerradas por el equipo.

## 1. Alcance declarado en el roadmap

`CHANGES.md` (sección `[C-06] pacientes`) define:

- Tabla `paciente` con `nombre`, `apellido`, `dni` único y `telefono`, `obra_social`, `nro_afiliado` opcionales.
- `GET/POST /pacientes` y `PATCH /pacientes/{id}`. La obra social es solo un dato, sin liquidación (RN-PAC-01).
- Permisos: administración y recepción `C L E`; odontólogo `L (de sus turnos)`, a completar cuando existan turnos (SE-12).
- Fixtures solo con datos ficticios y DNI con sufijo `"(ficticio)"` (RN-PAC-03).
- Tests: alta con y sin obra social, DNI duplicado → 409 (RN-PAC-02), odontólogo creando → 403.
- Dependencias: `C-03` (archivado). Como consumidor, `C-11 crear-turno` depende de `C-06`.
- Governance: BAJO.

## 2. Qué existe hoy

| Pieza | Estado | Evidencia |
|---|---|---|
| `NombreDuplicado` en dominio | Existe | `app/domain/errores.py` |
| Mapeo `409 nombre_duplicado` | Existe | `app/api/errores.py` (`MAPEO_DOMINIO`) |
| `404 → no_encontrado` global | Existe | `app/api/errores.py` (`_MAPEO_HTTP`) |
| `obtener_conexion`, `usuario_actual`, `requiere_rol` | Existen | `app/api/dependencias.py`, `app/api/auth.py` |
| Patrón dataclass + `validar_datos_*` | Modelo en C-04/C-05 | `app/domain/models.py` |
| Patrón repositorio con centinela `_SIN_CAMBIO` | Modelo en C-05 | `app/db/repositorio_sillones.py`, `app/db/repositorio_prestaciones.py` |
| Patrón router + `PATCH` con `exclude_unset=True` | Modelo en C-05 | `app/api/sillones.py`, `app/api/prestaciones.py` |
| `Turno.paciente_id: int` (solo el id) | Existe en dominio | `app/domain/models.py` |
| Tabla `paciente` | **No existe** | `app/db/esquema.sql` solo tiene `usuario`, `profesional`, `sillon`, `prestacion` |
| `Paciente` y `validar_datos_paciente` | **No existen** | `app/domain/models.py` |
| `app/db/repositorio_pacientes.py` | **No existe** | — |
| `app/api/pacientes.py` y montaje | **No existen** | `app/main.py` monta salud, auth, profesionales, sillones y prestaciones |
| Capability `pacientes` en `openspec/specs/` | **No existe** | Solo `acceso-usuarios`, `base-tecnica`, `errores-api`, `profesionales`, `reglas-alta-turno`, `sillones`, `prestaciones` |
| Fixtures reutilizables (`cliente`, `crear_usuario`, `token_de`, `reloj`) | Existen | `tests/conftest.py` |
| Baseline de la suite | 314 tests verdes | Última corrida del proyecto |

**Conclusión:** C-06 es trabajo nuevo en las cuatro capas, pero encaja sin fricción en los patrones de C-04/C-05. Solo se tocan archivos existentes de forma aditiva: `app/db/esquema.sql`, `app/domain/models.py`, `app/domain/errores.py`, `app/api/errores.py` y `app/main.py`.

## 3. Qué falta

### 3.1 Esquema

```sql
CREATE TABLE IF NOT EXISTS paciente (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    apellido      TEXT NOT NULL CHECK (length(trim(apellido)) > 0),
    dni           TEXT NOT NULL UNIQUE CHECK (length(trim(dni)) > 0),
    telefono      TEXT NULL,
    obra_social   TEXT NULL,
    nro_afiliado  TEXT NULL
);
```

- La tabla se agrega al final de `app/db/esquema.sql` con `CREATE TABLE IF NOT EXISTS`, igual que C-04/C-05, para mantener idempotente a `inicializar_esquema()`.
- No lleva `activo`: la entidad `Paciente` de la KB no lo define y la matriz RBAC no otorga `B` sobre pacientes.
- No hay `DELETE`: el paciente queda referenciado por turnos históricos desde C-11.
- La FK `turno.paciente_id → paciente.id` la creará C-11 al crear la tabla `turno` (SQLite no permite agregar FKs a tablas existentes y el proyecto no usa migraciones).

### 3.2 Dominio

- `Paciente(id: int | None = None, nombre, apellido, dni, telefono=None, obra_social=None, nro_afiliado=None)` con `frozen=True, kw_only=True`, mismo estilo que `Sillon`.
- `validar_datos_paciente(...)`: `strip()` de `nombre`, `apellido` y `dni`; rechazo de vacíos con `DatoInvalido`; normalización de opcionales con `strip()` y `"" → None` (misma convención que `matricula` en C-04).
- `dni` se guarda como texto (KB 04) y su unicidad se resuelve en la base con `UNIQUE`, no con un `SELECT` previo.

### 3.3 Repositorio

`app/db/repositorio_pacientes.py` con:

- `crear_paciente(conexion, *, nombre, apellido, dni, telefono=None, obra_social=None, nro_afiliado=None) -> Paciente`
- `listar_pacientes(conexion) -> list[Paciente]` ordenado por `id ASC`
- `obtener_paciente_por_id(conexion, id_paciente) -> Paciente | None` (lo consumirá C-11 para validar existencia)
- `actualizar_paciente(conexion, id_paciente, *, ...) -> Paciente | None` con centinela `_SIN_CAMBIO`

Traducción de `sqlite3.IntegrityError`: si el mensaje contiene `UNIQUE`, lanzar `DniDuplicado`; cualquier otra violación se re-lanza para no tapar bugs.

### 3.4 Router

`app/api/pacientes.py`, montado en `app/main.py`:

| Ruta | Status | Roles |
|---|---|---|
| `GET /pacientes` | 200 | administración y recepción; odontólogo 403 hasta C-11 |
| `POST /pacientes` | 201 | administración y recepción |
| `PATCH /pacientes/{id}` | 200 / 404 / 409 / 422 | administración y recepción |

- `401` sin token en las tres rutas.
- `404` con `codigo` `no_encontrado` y mensaje en español, vía `HTTPException(404)` y el handler global.
- `409` con `codigo` `dni_duplicado`.
- `422` con `codigo` `dato_invalido` para campos obligatorios vacíos, `null` en `nombre`/`apellido`/`dni` y DNI compuesto solo por espacios.

## 4. Reglas de negocio y escenarios candidatos

Reglas aplicables (`knowledge-base/05_reglas_de_negocio.md`):

- **RN-PAC-01:** datos mínimos (nombre, apellido, DNI) y obra social/prepaga + nro. de afiliado opcionales, sin liquidación ni validación contra el padrón.
- **RN-PAC-02:** DNI único por paciente.
- **RN-PAC-03:** solo datos ficticios; DNI de fixtures con sufijo `"(ficticio)"`.

Escenarios a cubrir en el delta de spec:

- **Alta:** válida con obra social y nro. de afiliado; válida sin datos opcionales; nombre vacío o solo espacios → 422; apellido vacío → 422; DNI vacío o solo espacios → 422; DNI duplicado → 409 `dni_duplicado`.
- **Listado:** administración → 200 ordenado por `id`; recepción → 200; odontólogo → 403 `sin_permiso`.
- **Edición:** renombrar; cambiar apellido; cambiar DNI; cambiar teléfono; cambiar obra social y nro. de afiliado; limpiar `telefono`, `obra_social` y `nro_afiliado` con `null` → 200; `nombre`, `apellido` o `dni` en `null` → 422 sin modificar; DNI de otro paciente → 409; `id` inexistente → 404 `no_encontrado`.
- **Acceso:** sin token en GET/POST/PATCH → 401; odontólogo POST/PATCH → 403.

## 5. Privacidad y datos

- `knowledge-base/08_arquitectura_propuesta.md` (Seguridad): en el MVP los datos de pacientes son ficticios; con datos reales aplican Ley 25.326 y la normativa de salud (IF-07).
- RN-PAC-03: prohibido usar datos reales en seeds, ejemplos y tests; los DNI de fixtures llevan `"(ficticio)"`.
- **No hay auditoría de pacientes**: IF-06 define que el MVP audita solo turnos. Se documenta como decisión explícita, no como olvido.
- Riesgos a mitigar:
  - El mensaje del `409` no debe repetir el DNI recibido.
  - El `404` no debe distinguir "no existe" de "existe pero sin permiso".
  - No loggear cuerpos con DNI ni teléfono.
  - No exponer búsqueda por DNI ni exportación (fuera de alcance).
  - SQLite en texto plano: aceptable solo mientras los datos sean ficticios.
  - El acceso del odontólogo es el principal riesgo de exposición: se difiere a C-11 con 403 explícito.

## 6. Riesgos del change

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Nombre del error `DniDuplicado` vs reutilizar `NombreDuplicado` | Contrato de errores | Decisión cerrada: error nuevo con código `dni_duplicado` |
| DNI con formatos distintos (`00.000.001` vs `00000001`) | Duplicados que la base no detecta | Decisión cerrada: solo `strip()`; se documenta la limitación |
| Pacientes extranjeros sin DNI | No se pueden cargar en el MVP | Decisión cerrada: DNI obligatorio; SE-15 resuelta para el MVP con la limitación documentada |
| Odontólogo sin filtro por turnos | Exposición de PII | Decisión cerrada: 403 hasta C-11 |
| Sin `activo` ni `DELETE` | No se puede "borrar" un paciente | Correcto para el historial de turnos; se documenta |
| Cambios aditivos en `esquema.sql`, `models.py`, `errores.py`, `main.py` | Conflictos con C-07/C-08 | Aditivo al final, módulos dedicados por recurso |
| C-11 depende de C-06 | Un modelo mal definido arrastra a crear-turno | Modelo y contrato cerrados en este change |

## 7. Alternativas descartadas

- **Reutilizar `NombreDuplicado` para el DNI:** el `codigo` resultante (`nombre_duplicado`) no describe el conflicto y obliga a estirar el contrato de `errores-api`. Se descartó en favor de `DniDuplicado`.
- **Normalizar el DNI a solo dígitos:** rompe la convención de RN-PAC-03 (`"00000001 (ficticio)"`), que exige el sufijo en fixtures.
- **DNI nullable para extranjeros:** contradice RN-PAC-01 (datos mínimos) y agrega semántica de `NULL` en `UNIQUE`; queda como limitación conocida.
- **Añadir `activo` y baja lógica:** no está en la KB ni en la matriz RBAC; se evita inventar alcance.
- **Un `GET /pacientes` con todos los datos para el odontólogo:** viola "de sus turnos"; se prefiere 403 explícito hasta C-11.
- **Validar `nro_afiliado` contra `obra_social`:** agrega una regla que la KB no pide; se permite el dato suelto.

## 8. Decisiones cerradas

1. **DNI solo `strip()`.** Sin quitar puntos ni espacios internos y sin exigir solo dígitos, para no romper la convención de fixtures de RN-PAC-03. La unicidad es sobre el texto normalizado con `strip()`.
2. **DNI obligatorio y único (`NOT NULL UNIQUE`).** SE-15 queda resuelta para el MVP: se documenta que un paciente sin DNI (por ejemplo, extranjero indocumentado) no puede cargarse; revisar si el consultorio lo necesita en una iteración futura.
3. **Error nuevo `DniDuplicado`.** Se agrega en `app/domain/errores.py` y se mapea a `(409, "dni_duplicado")` en `app/api/errores.py`. El mensaje en español no repite el DNI recibido.
4. **`GET /pacientes`:** administración y recepción → `200`; odontólogo → `403` (`sin_permiso`) hasta que C-11 permita acotar la lectura a sus turnos.
5. **Sin `activo`, sin baja lógica y sin `DELETE`.** La entidad `Paciente` de la KB no define estado y la matriz RBAC no otorga `B`; el historial de turnos exige conservar la fila.
6. **`nro_afiliado` sin `obra_social` permitido.** La KB no exige correlación y RN-PAC-01 prohíbe validar contra el padrón; se guarda como dato libre.

## 9. Preguntas abiertas

Ninguna. Las seis decisiones de §8 cierran el alcance del change; IF-02 se resuelve en el design (obra social = texto libre, sin liquidación ni validación) y SE-12 se resuelve parcialmente acá (administración y recepción escriben; odontólogo sin lectura hasta C-11).
