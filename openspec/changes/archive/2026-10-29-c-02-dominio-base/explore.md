# Explore — C-02 dominio-base

> Relevamiento previo al propose de `C-02 dominio-base`.
> Durante la exploración no se modificó ningún archivo de código ni de la KB.

## 1. Qué pide C-02 (`CHANGES.md` L176-190)

| Ítem | Contenido |
|---|---|
| Modelos (`app/domain/models.py`) | Dataclasses `Turno`, `Prestacion`, `HorarioAtencion`, `Bloqueo` (sin dependencias de FastAPI ni DB) |
| Intervalos (`app/domain/intervalos.py`) | `solapan(a, b)` con intervalos semiabiertos `[inicio, fin)` (RN-TUR-04) |
| Reloj inyectable y turno futuro | `ahora: datetime` como parámetro y `es_futuro(turno, ahora)` (RN-TUR-09) |
| Errores (`app/domain/errores.py`) | `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo`, `TurnoNoModificable`, `DatoInvalido` |
| Tests de dominio (`tests/domain/`) | Contiguos válidos, solapamiento parcial, contención, mismo inicio; `es_futuro` con reloj fijo (antes, igual, después) |
| Dependencias | `C-01` (`foundation-setup`), governance **MEDIO** |

De la KB:
- **Reglas (`05_reglas_de_negocio.md`):**
  - `RN-TUR-04` (`SE-10`): Los intervalos son semiabiertos `[inicio, fin)`: un turno que empieza exactamente cuando termina otro es válido (turnos contiguos).
  - `RN-TUR-09` (`SE-11`): Solo se pueden cancelar o reprogramar turnos futuros (`inicio` estrictamente posterior al momento actual `ahora`). Un turno pasado o en curso (`inicio <= ahora`) se rechaza.
  - `RN-GLO-01`: Los errores de regla de negocio devuelven un mensaje claro en español y un código HTTP consistente (`409` conflicto, `422` dato inválido).
- **Arquitectura (`08_arquitectura_propuesta.md`):**
  - `app/domain/` es Python puro: no importa FastAPI, Pydantic ni `app/db` o `app/api`.
  - Reloj inyectado: nunca se llama a `datetime.now()` ni `date.today()` dentro del dominio; `ahora` se recibe como parámetro.

## 2. Qué existe hoy en `main` y qué falta

Al haberse implementado primero `C-10` (`reglas-alta-turno`) con una base mínima y luego `C-01`, `C-03`, `C-04`, `C-05`, `C-06` y `C-07`, gran parte de `C-02` ya vive en `main`:

**Ya existe en `main`:**
- `app/domain/models.py`: dataclasses inmutables (`frozen=True, kw_only=True`) `Turno`, `Prestacion`, `HorarioAtencion` y `Bloqueo` (además de `Profesional`, `Sillon` y `Paciente` agregados por `C-04`, `C-05` y `C-06`).
- `app/domain/intervalos.py`: protocolo `Intervalo` (`inicio`, `fin`) y función `solapan(a, b)` con intervalos semiabiertos `a.inicio < b.fin and b.inicio < a.fin`.
- `app/domain/errores.py`: `ErrorDominio`, `DatoInvalido`, `ConflictoAgenda`, `FueraDeHorario`, `DentroDeBloqueo` (más `NombreDuplicado`, `DniDuplicado`, `UsernameDuplicado`).
- `tests/domain/test_intervalos.py`: tests de turnos contiguos, solapamiento parcial, intervalo contenido, intervalos disjuntos y comparación entre turno y bloqueo.

**Falta para completar el scope de `C-02`:**
1. **`es_futuro(turno, ahora)` en `app/domain/intervalos.py`:** función pura que recibe un `Intervalo` (o `Turno`) y `ahora: datetime` inyectado, devolviendo `True` solo cuando `turno.inicio > ahora` (`RN-TUR-09`).
2. **`TurnoNoModificable` en `app/domain/errores.py` y su mapeo HTTP en `app/api/errores.py`:**
   - En `C-03` se agregó el test `tests/api/test_errores.py::test_todo_error_de_dominio_de_la_app_tiene_entrada_en_el_mapeo`, que exige que toda subclase de `ErrorDominio` definida en `app.*` figure en `MAPEO_DOMINIO` de `app/api/errores.py`.
   - Por lo tanto, al agregar `TurnoNoModificable(ErrorDominio)` en `app/domain/errores.py`, debe registrarse `TurnoNoModificable: (409, "turno_no_modificable")` en `app/api/errores.py` (y su ruta de prueba en `tests/api/rutas_prueba.py` + caso parametrizado en `tests/api/test_errores.py`).
3. **Tests unitarios faltantes en `tests/domain/test_intervalos.py`:**
   - Caso explícito de `solapan` con **mismo inicio** (pedido en `CHANGES.md` L183).
   - Casos de `es_futuro(turno, ahora)` con reloj fijo: `ahora` antes del inicio (`True`), `ahora` igual al inicio (`False`, turno en curso) y `ahora` después del inicio (`False`, turno pasado).
   - Tests unitarios de modelos base y jerarquía de errores de `C-02`.

## 3. Impacto de desbloqueo en el roadmap

Cerrar y archivar `C-02` destraba inmediatamente:
- **`C-08 horarios-atencion`** (depende de `C-02` y `C-04`).
- **`C-09 bloqueos`** (depende de `C-02`, `C-04` y `C-05`; ya implementado en rama `bruno-c09-bloqueos` esperando `C-02` para archivar y abrir PR).
- Indirectamente **`C-11 crear-turno`** (cuello de botella del MVP, que espera `C-08` y `C-09`) y **`C-12`/`C-13`** (que usan `es_futuro` y `TurnoNoModificable`).

## 4. Fuentes consultadas

- `CHANGES.md` §C-02 (L176-190).
- `knowledge-base/08_arquitectura_propuesta.md` §Patrones aplicados, §Testing.
- `knowledge-base/05_reglas_de_negocio.md` §RN-TUR-04, §RN-TUR-09, §RN-GLO-01.
- `knowledge-base/04_modelo_de_datos.md` §Convenciones, §Entidades.
- `knowledge-base/10_preguntas_abiertas.md` §SE-05, §SE-10, §SE-11.
