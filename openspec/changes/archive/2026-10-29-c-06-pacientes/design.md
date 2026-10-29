# Design — C-06 pacientes

## Context

Ver `proposal.md` para la motivación. Estado y restricciones que condicionan el enfoque:

- `C-01` dejó `app/db/conexion.py` (`abrir_conexion`, `transaccion` con `BEGIN IMMEDIATE`, `inicializar_esquema`), `app/db/esquema.sql` y `app/main.py` (`create_app`).
- `C-03` archivado aporta `app/api/auth.py` (`usuario_actual` → `401`, `requiere_rol(*roles)` → `403`), `app/api/dependencias.py` (`obtener_conexion` por request) y el mapeo global de errores a JSON en español en `app/api/errores.py` (`RN-GLO-01`).
- `C-04` y `C-05` archivados son el modelo a seguir: dataclass + validación pura en `app/domain/models.py`, repositorio dedicado con SQL parametrizado y centinela `_SIN_CAMBIO`, router dedicado, `PATCH` con `exclude_unset=True` y tests por capa.
- `app/domain/models.py` ya define `Turno.paciente_id: int` para `C-10`/`C-11`, pero no existe la entidad `Paciente` ni la tabla `paciente`.
- Reglas duras aplicables (`AGENTS.md`): 1 (dominio puro), 4 (SQL parametrizado), 7 (errores en español con código), 8 (reglas de negocio en `app/domain/`, Pydantic solo en la frontera), 10 (datos ficticios), 11 (cada RN-xx con test), 12 (`snake_case` y type hints).

## Goals / Non-Goals

**Goals:**

- Persistir pacientes con DNI único y datos opcionales, reutilizando el esquema idempotente y la transacción existentes.
- Validar en dominio los obligatorios y normalizar los opcionales sin depender de DB ni HTTP.
- Exponer tres endpoints (`GET`, `POST`, `PATCH`) respetando la matriz RBAC: administración y recepción escriben y leen; odontólogo sin lectura hasta `C-11`.
- Dejar `obtener_paciente_por_id` listo para que `C-11` valide la existencia del paciente al crear un turno.
- Traducir el `UNIQUE(dni)` a un `409` estable sin filtrar el error de SQLite ni el DNI recibido.
- Resolver IF-02 y documentar la postura de privacidad del MVP.

**Non-Goals:**

- Baja lógica, `DELETE` y campo `activo` (la KB no los define para `Paciente`).
- Búsqueda, filtro o exportación por DNI.
- Validación del `nro_afiliado` contra `obra_social` o contra el padrón de la obra social.
- Liquidación a obras sociales (IF-02: el dato es solo informativo en el MVP).
- Lectura del odontólogo acotada a sus turnos (se habilita en `C-11`).
- Auditoría de pacientes (IF-06: el MVP audita solo turnos).
- Normalización del DNI más allá de `strip()`.

## Decisions

- **D1 — Esquema SQLite.** Se agrega la tabla al final de `app/db/esquema.sql`, después de `prestacion`:
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
  *Por qué:* `CREATE TABLE IF NOT EXISTS` mantiene idempotente a `inicializar_esquema()`; `UNIQUE(dni)` implementa RN-PAC-02 con índice implícito y sin chequeo previo (evita carreras); los `CHECK` refuerzan las invariantes como red de seguridad. `dni` es `TEXT` porque la KB lo modela como texto y porque los fixtures llevan el sufijo `"(ficticio)"` (RN-PAC-03).
  *Alternativa descartada:* `dni INTEGER` o `CHECK` de solo dígitos; rompería los fixtures ficticios y la convención de la KB.

- **D2 — Modelo de dominio.** Se agrega `Paciente(id: int | None = None, nombre: str, apellido: str, dni: str, telefono: str | None = None, obra_social: str | None = None, nro_afiliado: str | None = None)` en `app/domain/models.py`, con `frozen=True, kw_only=True` e `id` al final, igual que `Profesional` y `Sillon`.
  *Por qué:* consistencia con los modelos existentes y `id` opcional porque se asigna al insertar.

- **D3 — Validaciones puras.** `validar_datos_paciente(nombre, apellido, dni, telefono=None, obra_social=None, nro_afiliado=None) -> tuple[str, str, str, str | None, str | None, str | None]`:
  - `strip()` de `nombre`, `apellido` y `dni`; vacío o solo espacios → `DatoInvalido` con mensaje en español.
  - `strip()` de los opcionales; `""` → `None` (misma convención que `matricula` en `C-04`).
  - **No** se quitan puntos, guiones ni espacios internos del DNI: solo `strip()`. La unicidad es sobre el texto normalizado, y se acepta que `"00.000.001"` y `"00000001"` convivan (limitación documentada).
  Pydantic valida forma y tipo en la frontera (`str`, `str | None`); el dominio valida la regla de negocio (regla dura 8).
  *Alternativa descartada:* normalizar a solo dígitos; choca con RN-PAC-03 y con el sufijo `"(ficticio)"` de seeds y tests.

- **D4 — DNI obligatorio y único (SE-15).** Se implementa `NOT NULL UNIQUE` y la validación de dominio exige DNI no vacío. SE-15 queda resuelta para el MVP: un paciente sin DNI (por ejemplo, extranjero indocumentado) no puede cargarse. Se documenta la limitación en el change y en la nota de `tasks.md`.
  *Alternativa descartada:* `NULL UNIQUE` para habilitar indocumentados; contradice RN-PAC-01 ("datos mínimos: nombre, apellido, DNI") y agrega semántica de `NULL` que el MVP no necesita.

- **D5 — `DniDuplicado` → `409 dni_duplicado`.** Se agrega `DniDuplicado(ErrorDominio)` en `app/domain/errores.py` y su entrada `(409, "dni_duplicado")` en `MAPEO_DOMINIO` de `app/api/errores.py`. El repositorio envuelve el `sqlite3.IntegrityError` de `crear_paciente`/`actualizar_paciente`: si el mensaje contiene `UNIQUE`, lanza `DniDuplicado` con un mensaje genérico en español (`"Ya existe un paciente con ese DNI."`) que **no repite el valor recibido**; cualquier otra violación se re-lanza.
  *Por qué:* regla dura 7 (nada ad-hoc, código estable y español) y el `409` debe ser carrera-segura dejando fallar el `UNIQUE` dentro de `transaccion()`.
  *Alternativas descartadas:* reutilizar `NombreDuplicado` (el `codigo` `nombre_duplicado` no describe el conflicto); `HTTPException(409)` desde el router (el handler genérico lo convertiría en `error_http`); chequeo previo con `SELECT` (carrera entre requests).

- **D6 — Un router y un repositorio.** `app/api/pacientes.py` + `app/db/repositorio_pacientes.py`, montados en `app/main.py`. El router reutiliza `obtener_conexion`, `transaccion`, `usuario_actual`, `requiere_rol` y los handlers de `app/api/errores.py`.
  *Por qué:* patrón de `C-04`/`C-05` y módulos dedicados por recurso para minimizar conflictos con `C-07` y `C-08`.

- **D7 — RBAC de pacientes (SE-12 parcial).** `POST` y `PATCH` usan `requiere_rol(Rol.ADMINISTRACION, Rol.RECEPCION)`; `GET` usa la misma dependencia. `odontologo` recibe `403` en las tres rutas hasta que `C-11` exista y permita acotar la lectura a sus turnos.
  *Por qué:* la matriz de `knowledge-base/03_actores_y_roles.md` da `C L E` a administración y recepción, y `L (de sus turnos)` al odontólogo. Sin tabla `turno` no hay forma de implementar ese alcance; exponer todos los pacientes violaría la matriz y la privacidad. Se prefiere un `403` explícito y una nota para `C-11` antes que una lectura sobreexpuesta.
  *Alternativa descartada:* dar `200` con todos los pacientes al odontólogo "por ahora"; se descartó por privacidad y por contradir el alcance declarado.

- **D8 — Semántica de `PATCH` y campos opcionales.** Modelo Pydantic de entrada con todos los campos opcionales y `model_dump(exclude_unset=True)` para distinguir campo omitido de campo enviado:
  - `nombre`, `apellido` y `dni` no son anulables: `null` → `422` sin modificar el paciente.
  - `telefono`, `obra_social` y `nro_afiliado` sí son anulables: `null` → limpia el dato y responde `200`.
  - El candidato se arma combinando el valor actual con los cambios, se revalida en dominio y se persiste con un `UPDATE` que reescribe todas las columnas (patrón `_SIN_CAMBIO` de `C-04`).
  *Por qué:* paridad con `C-04`/`C-05`, y la distinción explícita `null` vs omitido es la única forma de permitir limpiar opcionales sin romper la edición parcial.

- **D9 — Listados completos y sin baja lógica.** `GET` devuelve todos los pacientes ordenados por `id ASC`, sin filtros ni paginación. No hay `DELETE` ni `activo`: la entidad de la KB no define estado y la matriz no otorga `B`.
  *Por qué:* el historial de turnos de `C-11` referencia pacientes; borrarlos rompería la trazabilidad. Si en el futuro se necesita dar de baja pacientes, será un change con cambio de KB.

- **D10 — Obra social e IF-02.** `obra_social` y `nro_afiliado` se guardan como texto libre, sin validación contra el padrón, sin correlación obligatoria entre ambos y sin liquidación. IF-02 queda resuelta para el MVP: el dato es informativo y sirve para mostrarlo en la ficha del paciente y en la agenda; una eventual liquidación es etapa posterior y no cambia el modelo actual.
  *Por qué:* RN-PAC-01 lo declara explícitamente y el informe D.3 #7 lo trata como dato. Permitir `nro_afiliado` sin `obra_social` evita inventar una regla que la KB no pide.

- **D11 — Privacidad de datos de pacientes.** Aunque el MVP solo usa datos ficticios (RN-PAC-03), el diseño fija las siguientes garantías:
  - `GET`, `POST` y `PATCH` exigen token válido (`401` sin autenticación); no hay rutas públicas de pacientes.
  - El `409` no repite el DNI y el `404` no distingue "no existe" de "sin permiso".
  - No se loggean cuerpos de request ni valores de DNI o teléfono.
  - No se exponen búsqueda por DNI, exportación ni endpoints adicionales.
  - El odontólogo no lee pacientes hasta que `C-11` permita acotar por turnos (D7).
  - **No hay auditoría de pacientes**: IF-06 define que el MVP audita solo turnos; se documenta como decisión explícita. Con datos reales aplicarían Ley 25.326 y la normativa de salud (IF-07), y el modelo de amenaza cambiaría (SQLite en texto plano, retención, acceso).
  *Por qué:* la privacidad es un requisito de la KB (`knowledge-base/08_arquitectura_propuesta.md` §Seguridad) y el change introduce la primera entidad con PII del sistema.

## Estructura resultante (archivos tocados por C-06)

```
app/
├── main.py                            # monta el router de pacientes
├── domain/
│   ├── models.py                      # + Paciente, validar_datos_paciente()
│   └── errores.py                     # + DniDuplicado
├── db/
│   ├── esquema.sql                    # + CREATE TABLE IF NOT EXISTS paciente
│   └── repositorio_pacientes.py       # crear, listar, obtener_por_id, actualizar
└── api/
    ├── errores.py                     # + mapeo 409 dni_duplicado
    └── pacientes.py                   # GET/POST /pacientes, PATCH /pacientes/{id}
tests/
├── domain/
│   └── test_pacientes.py              # validación pura, normalización y opcionales
└── api/
    ├── test_repositorio_pacientes.py  # esquema, UNIQUE, CRUD y errores no traducidos
    └── test_pacientes.py              # 201, 409, 422, 404, 403 y 401
```

## Risks / Trade-offs

- **[DNI con formatos distintos]** → solo `strip()`; `"00.000.001"` y `"00000001"` se consideran distintos. Se documenta como limitación del MVP; unificarlos exigiría una decisión de normalización y migrar datos.
- **[Pacientes sin DNI no pueden cargarse (SE-15)]** → DNI obligatorio; se documenta la limitación y se revisa si el consultorio atiende pacientes indocumentados.
- **[Odontólogo sin acceso a pacientes hasta C-11]** → `403` explícito y nota de seguimiento en `tasks.md`; C-11 habilitará la lectura acotada a sus turnos y su test.
- **[Traducción de `IntegrityError` dependiente del texto `UNIQUE` de SQLite]** → el mensaje es estable en SQLite y solo se traduce esa violación; cualquier otro `IntegrityError` sigue propagándose para no tapar bugs.
- **[Sin auditoría de pacientes]** → aceptado por IF-06 (el MVP audita turnos); se documenta para que no se lea como omisión.
- **[PII en un almacenamiento sin cifrar]** → aceptable mientras los datos sean ficticios (RN-PAC-03); con datos reales aplica IF-07 y habría que revisar cifrado, retención y accesos.
- **[Conflicto de merge con C-07/C-08 en `main.py`, `models.py` y `esquema.sql`]** → cambios estrictamente aditivos al final de cada archivo y módulos dedicados por recurso.

## Migration Plan

La tabla se crea con `CREATE TABLE IF NOT EXISTS` al iniciar la app; no hay migraciones ni backfill. Rollback: revertir el merge del change (la tabla nueva puede quedarse vacía sin afectar a los changes previos). `C-11` creará `turno` con la FK `paciente_id` cuando la tabla ya exista.

## Open Questions

Ninguna. Las seis decisiones de `explore.md` §8 quedaron cerradas y se reflejan en D1–D11; IF-02 y SE-15 se resuelven en D10 y D4, y la parte de SE-12 que depende de turnos queda como nota para `C-11`.
